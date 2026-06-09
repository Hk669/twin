#!/usr/bin/env python3
"""
harvest.py -- multi-harness session harvester (PLAN.md, cross-harness senses).

Sweeps every agent harness on this PC, keeps the human<->assistant conversation,
drops tool-call noise, scrubs obvious secrets, and writes one provenance-headed
markdown file per session into ./harvest/ for `gbrain import` + distillation.

Substance gate: only sessions with MORE THAN --min-messages user+assistant
messages are kept (default: more than 10).

Harnesses:
  claude  ~/.claude/projects/<proj>/<session>.jsonl   (type=user/assistant, message.content)
  codex   ~/.codex/sessions/YYYY/MM/DD/rollout-*.jsonl (payload.role + payload.content)
  hermes  ~/AppData/Local/hermes/sessions/*.jsonl      (top-level role + content)
  openclaw: DEFERRED -- retired; agents/ holds auth/cache (incl. live tokens), no
            clean transcripts. Not harvested.

Claude file naming is preserved (<project>__<uuid>.md) so already-distilled
sessions stay idempotent; codex/hermes pages are prefixed by harness.

Usage:
    python harvest.py                       # all harnesses, >10 messages
    python harvest.py --harness codex       # one harness
    python harvest.py --min-messages 10     # keep sessions with > 10 messages
    python harvest.py --dry-run             # scan + per-harness report, write nothing
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

# --- harness noise injected into the user turn; not operating signal ----------
_NOISE_BLOCKS = [
    re.compile(r"<system-reminder>.*?</system-reminder>", re.DOTALL),
    re.compile(r"<command-(?:message|name|args)>.*?</command-(?:message|name|args)>", re.DOTALL),
    re.compile(r"<local-command-[^>]*>.*?</local-command-[^>]*>", re.DOTALL),
    re.compile(r"<environment_context>.*?</environment_context>", re.DOTALL),   # codex
    re.compile(r"<user_instructions>.*?</user_instructions>", re.DOTALL),       # codex
]

# --- obvious secrets to redact before anything reaches the gold layer ----------
_SECRET_PATTERNS = [
    re.compile(r"sk-[A-Za-z0-9_\-]{16,}"),
    re.compile(r"ghp_[A-Za-z0-9]{20,}"),
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"(?i)\b(api[_-]?key|secret|token|bearer|access)\b\s*[:=]\s*\S+"),
    re.compile(r"eyJ[A-Za-z0-9_\-]{10,}\.[A-Za-z0-9_\-]{10,}\.[A-Za-z0-9_\-]{6,}"),  # JWT
]

_TOOL_TYPES = {
    "tool_use", "tool_result", "function_call", "function_call_output",
    "local_shell_call", "local_shell_call_output", "custom_tool_call",
}
_MSG_ROLES = {"user", "assistant"}


@dataclass
class Turn:
    role: str
    text: str


@dataclass
class Session:
    harness: str
    session_id: str
    out_name: str            # markdown filename stem (no extension)
    cwd: str = ""
    git_branch: str = ""
    first_ts: str = ""
    last_ts: str = ""
    turns: list[Turn] = field(default_factory=list)
    used_tools: bool = False
    parse_errors: int = 0

    @property
    def messages(self) -> int:
        return len(self.turns)


def scrub_secrets(text: str) -> str:
    for pat in _SECRET_PATTERNS:
        text = pat.sub("[REDACTED]", text)
    return text


def strip_noise(text: str) -> str:
    for pat in _NOISE_BLOCKS:
        text = pat.sub("", text)
    return text.strip()


def content_to_text(content) -> tuple[str, bool]:
    """
    Normalize a message `content` (str | list of blocks) to plain text across
    harness formats. Grabs any block's 'text' field (covers Anthropic
    {type:text}, codex {type:input_text/output_text}, hermes parts). Flags tool
    blocks so the session is marked as tool-using. Drops thinking/images.
    """
    if isinstance(content, str):
        return content, False
    if not isinstance(content, list):
        return "", False
    parts, saw_tool = [], False
    for b in content:
        if not isinstance(b, dict):
            if isinstance(b, str):
                parts.append(b)
            continue
        if isinstance(b.get("text"), str):
            parts.append(b["text"])
        elif b.get("type") in _TOOL_TYPES:
            saw_tool = True
    return "\n".join(p for p in parts if p), saw_tool


def _add_turn(sess: Session, role: str, content) -> None:
    text, saw_tool = content_to_text(content)
    if saw_tool:
        sess.used_tools = True
    if role == "user":
        text = strip_noise(text)
    text = scrub_secrets(text).strip()
    if text:
        sess.turns.append(Turn(role=role, text=text))


def _track_meta(sess: Session, obj: dict) -> None:
    if obj.get("cwd") and not sess.cwd:
        sess.cwd = obj["cwd"]
    if obj.get("gitBranch") and not sess.git_branch:
        sess.git_branch = obj["gitBranch"]
    ts = obj.get("timestamp")
    if ts:
        if not sess.first_ts:
            sess.first_ts = ts
        sess.last_ts = ts


def _read_jsonl(path: Path):
    with path.open("r", encoding="utf-8", errors="replace") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError:
                yield None


# --- per-harness parsers ------------------------------------------------------

def iter_claude_sessions(root: Path, project: str | None):
    projects = [root / project] if project else sorted(p for p in root.iterdir() if p.is_dir())
    for proj_dir in projects:
        if not proj_dir.is_dir():
            continue
        for jsonl in sorted(proj_dir.glob("*.jsonl")):
            sess = Session("claude", jsonl.stem, f"{proj_dir.name}__{jsonl.stem}")
            for obj in _read_jsonl(jsonl):
                if obj is None:
                    sess.parse_errors += 1
                    continue
                if "toolUseResult" in obj:
                    sess.used_tools = True
                _track_meta(sess, obj)
                if obj.get("type") not in ("user", "assistant"):
                    continue
                if obj.get("isMeta") or obj.get("isSidechain"):
                    continue
                msg = obj.get("message") or {}
                _add_turn(sess, msg.get("role", obj["type"]), msg.get("content"))
            yield sess


def iter_codex_sessions(root: Path):
    for jsonl in sorted(root.rglob("rollout-*.jsonl")):
        sess = Session("codex", jsonl.stem, f"codex__{jsonl.stem}")
        for obj in _read_jsonl(jsonl):
            if obj is None:
                sess.parse_errors += 1
                continue
            _track_meta(sess, obj)
            payload = obj.get("payload")
            if not isinstance(payload, dict):
                continue
            if payload.get("type") in _TOOL_TYPES:
                sess.used_tools = True
            role = payload.get("role")
            if role in _MSG_ROLES:
                _add_turn(sess, role, payload.get("content"))
        yield sess


def iter_hermes_sessions(root: Path):
    for jsonl in sorted(root.glob("*.jsonl")):
        sess = Session("hermes", jsonl.stem, f"hermes__{jsonl.stem}")
        for obj in _read_jsonl(jsonl):
            if obj is None:
                sess.parse_errors += 1
                continue
            _track_meta(sess, obj)
            role = obj.get("role")
            if role in _MSG_ROLES:
                _add_turn(sess, role, obj.get("content"))
        yield sess


HARNESS_DIRS = {
    "claude": Path.home() / ".claude" / "projects",
    "codex": Path.home() / ".codex" / "sessions",
    "hermes": Path.home() / "AppData" / "Local" / "hermes" / "sessions",
}


def gather(harnesses, project):
    for h in harnesses:
        root = HARNESS_DIRS[h]
        if not root.is_dir():
            print(f"  ({h}: {root} not found, skipping)", file=sys.stderr)
            continue
        if h == "claude":
            yield from iter_claude_sessions(root, project)
        elif h == "codex":
            yield from iter_codex_sessions(root)
        elif h == "hermes":
            yield from iter_hermes_sessions(root)


def render_markdown(sess: Session) -> str:
    fm = [
        "---",
        f"source_harness: {sess.harness}",
        f"session_id: {sess.session_id}",
        f"cwd: {sess.cwd}",
        f"git_branch: {sess.git_branch}",
        f"first_ts: {sess.first_ts}",
        f"last_ts: {sess.last_ts}",
        f"messages: {sess.messages}",
        f"stateless: {'true' if not sess.used_tools else 'false'}",
        "---",
        "",
    ]
    body = [f"## {'User' if t.role == 'user' else 'Assistant'}\n\n{t.text}\n" for t in sess.turns]
    return "\n".join(fm) + "\n".join(body)


def main() -> int:
    ap = argparse.ArgumentParser(description="Harvest sessions across all harnesses -> gbrain-ready markdown.")
    ap.add_argument("--harness", default="claude,codex,hermes",
                    help="comma list of harnesses to harvest")
    ap.add_argument("--out", default="./harvest")
    ap.add_argument("--project", default=None, help="claude only: limit to one project dir")
    ap.add_argument("--min-messages", type=int, default=10,
                    help="keep sessions with MORE THAN this many user+assistant messages")
    ap.add_argument("--stateless-only", action="store_true",
                    help="keep only pure-conversation sessions (for the eval task set, not harvest)")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    harnesses = [h.strip() for h in args.harness.split(",") if h.strip() in HARNESS_DIRS]
    out_dir = Path(args.out)
    if not args.dry_run:
        out_dir.mkdir(parents=True, exist_ok=True)

    from collections import Counter
    scanned = Counter()
    written = Counter()
    skipped_short = Counter()
    skipped_stateful = Counter()
    total_written = 0

    for sess in gather(harnesses, args.project):
        scanned[sess.harness] += 1
        if sess.messages <= args.min_messages:
            skipped_short[sess.harness] += 1
            continue
        if args.stateless_only and sess.used_tools:
            skipped_stateful[sess.harness] += 1
            continue
        if not args.dry_run:
            (out_dir / f"{sess.out_name}.md").write_text(render_markdown(sess), encoding="utf-8")
        written[sess.harness] += 1
        total_written += 1
        if args.limit and total_written >= args.limit:
            break

    print(f"{'harness':8} {'scanned':>8} {'written':>8} {'<=msgs':>8} {'stateful':>9}")
    for h in harnesses:
        print(f"{h:8} {scanned[h]:8d} {written[h]:8d} {skipped_short[h]:8d} {skipped_stateful[h]:9d}")
    print(f"{'TOTAL':8} {sum(scanned.values()):8d} {sum(written.values()):8d} "
          f"{sum(skipped_short.values()):8d} {sum(skipped_stateful.values()):9d}")
    print(f"\nkept sessions with > {args.min_messages} messages.")
    if not args.dry_run:
        print(f"out: {out_dir.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
