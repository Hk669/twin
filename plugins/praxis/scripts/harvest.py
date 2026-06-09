#!/usr/bin/env python3
"""
harvest.py -- multi-harness session harvester.

Sweeps every agent harness on this machine, keeps the human<->assistant conversation,
drops tool-call noise, scrubs obvious secrets, and writes one provenance-headed markdown
file per session into ./harvest/ for distillation.

Substance gate: only sessions with MORE THAN --min-messages user+assistant messages are
kept (default: more than 10).

Harnesses:
  claude  ~/.claude/projects/<proj>/<session>.jsonl   (type=user/assistant, message.content)
  codex   ~/.codex/sessions/YYYY/MM/DD/rollout-*.jsonl (payload.role + payload.content)
  hermes  ~/AppData/Local/hermes/sessions/*.jsonl      (top-level role + content)
  openclaw: DEFERRED -- retired; agents/ holds auth/cache (incl. live tokens), no clean
            transcripts. Not harvested.

Claude file naming is preserved (<project>__<uuid>.md); codex/hermes pages are prefixed
by harness.

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
from collections import Counter
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

    @property
    def messages(self) -> int:
        return len(self.turns)

    @property
    def looks_automated(self) -> bool:
        """Eval / benchmark / automation runs repeat near-identical prompts and carry no
        preference signal. Detect heavy user-turn repetition so they never reach distillation."""
        users = [t.text.strip() for t in self.turns if t.role == "user" and t.text.strip()]
        if len(users) < 4:
            return False
        counts = Counter(users)
        if counts.most_common(1)[0][1] >= 4:        # same prompt 4+ times
            return True
        return len(counts) / len(users) < 0.5       # mostly repeats


def scrub_secrets(text: str) -> str:
    for pat in _SECRET_PATTERNS:
        text = pat.sub("[REDACTED]", text)
    return text


def strip_noise(text: str) -> str:
    for pat in _NOISE_BLOCKS:
        text = pat.sub("", text)
    return text.strip()


def content_to_text(content) -> str:
    """Normalize a message `content` (str | list of blocks) to plain text across harness
    formats. Grabs any block's 'text' field (Anthropic, codex input/output_text, hermes);
    tool/thinking/image blocks have no such field and are dropped."""
    if isinstance(content, str):
        return content
    if not isinstance(content, list):
        return ""
    parts = []
    for b in content:
        if isinstance(b, str):
            parts.append(b)
        elif isinstance(b, dict) and isinstance(b.get("text"), str):
            parts.append(b["text"])
    return "\n".join(p for p in parts if p)


def _add_turn(sess: Session, role: str, content) -> None:
    text = content_to_text(content)
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
                    continue
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
                continue
            _track_meta(sess, obj)
            payload = obj.get("payload")
            if isinstance(payload, dict) and payload.get("role") in _MSG_ROLES:
                _add_turn(sess, payload["role"], payload.get("content"))
        yield sess


def iter_hermes_sessions(root: Path):
    for jsonl in sorted(root.glob("*.jsonl")):
        sess = Session("hermes", jsonl.stem, f"hermes__{jsonl.stem}")
        for obj in _read_jsonl(jsonl):
            if obj is None:
                continue
            _track_meta(sess, obj)
            if obj.get("role") in _MSG_ROLES:
                _add_turn(sess, obj["role"], obj.get("content"))
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
        "---",
        "",
    ]
    body = [f"## {'User' if t.role == 'user' else 'Assistant'}\n\n{t.text}\n" for t in sess.turns]
    return "\n".join(fm) + "\n".join(body)


def main() -> int:
    ap = argparse.ArgumentParser(description="Harvest sessions across all harnesses into markdown.")
    ap.add_argument("--harness", default="claude,codex,hermes", help="comma list of harnesses")
    ap.add_argument("--out", default="./harvest")
    ap.add_argument("--project", default=None, help="claude only: limit to one project dir")
    ap.add_argument("--min-messages", type=int, default=10,
                    help="keep sessions with MORE THAN this many user+assistant messages")
    ap.add_argument("--dry-run", action="store_true", help="scan + report, write nothing")
    args = ap.parse_args()

    harnesses = [h.strip() for h in args.harness.split(",") if h.strip() in HARNESS_DIRS]
    out_dir = Path(args.out)
    if not args.dry_run:
        out_dir.mkdir(parents=True, exist_ok=True)

    scanned, written, skipped_short, skipped_eval = Counter(), Counter(), Counter(), Counter()
    for sess in gather(harnesses, args.project):
        scanned[sess.harness] += 1
        if sess.messages <= args.min_messages:
            skipped_short[sess.harness] += 1
            continue
        if sess.looks_automated:
            skipped_eval[sess.harness] += 1
            continue
        if not args.dry_run:
            (out_dir / f"{sess.out_name}.md").write_text(render_markdown(sess), encoding="utf-8")
        written[sess.harness] += 1

    print(f"{'harness':8} {'scanned':>8} {'written':>8} {'<=msgs':>8} {'eval':>6}")
    for h in harnesses:
        print(f"{h:8} {scanned[h]:8d} {written[h]:8d} {skipped_short[h]:8d} {skipped_eval[h]:6d}")
    print(f"{'TOTAL':8} {sum(scanned.values()):8d} {sum(written.values()):8d} "
          f"{sum(skipped_short.values()):8d} {sum(skipped_eval.values()):6d}")
    print(f"\nkept sessions with > {args.min_messages} messages (dropped eval/automation runs).")
    if not args.dry_run:
        print(f"out: {out_dir.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
