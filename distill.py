#!/usr/bin/env python3
"""
distill.py -- distillation pass (PLAN.md T4).

For each harvested session, asks codex (codex exec) to extract "how the user
operates" facts -- preferences, conventions, decision patterns, working style --
each with a verbatim evidence quote. Appends every fact to claims.jsonl and writes
one provenance-headed distilled/<session>.md page per session, ready for
`gbrain import` into the PROJECT brain.

This is the step that turns raw transcript chunks into gold. The extractor reads
each harvest file directly (passed by path), so large sessions don't hit argv
size limits.

Usage:
    python distill.py                 # all harvested sessions
    python distill.py --limit 8       # first 8 (batch / eyeball)
    python distill.py --effort medium # higher-quality extraction (slower)
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

# On Windows, `codex` is an npm .CMD shim; subprocess needs the resolved path.
_CODEX = shutil.which("codex") or "codex"

PROMPT_TMPL = (
    "Read the file {path}. It is a transcript between a user and an AI coding "
    "assistant. Extract concrete, TRANSFERABLE facts about HOW THE USER OPERATES: "
    "their preferences, conventions, decision patterns, working style, what they "
    "correct, what they value, and how they want agents to behave. Ignore "
    "topic-specific content (the actual task or domain). Return UP TO {n} facts. "
    "Output ONLY a compact JSON array of objects with keys: claim (one sentence), "
    "category (snake_case), evidence (a short verbatim quote from the transcript). "
    "No prose, no markdown fence, no explanation."
)

# codex prints its final answer last; grab the last JSON array in the output.
JSON_ARRAY_RE = re.compile(r"\[\s*\{.*?\}\s*\]", re.DOTALL)


def run_codex(rel_path: str, n: int, effort: str, proj: Path) -> str:
    prompt = PROMPT_TMPL.format(path=rel_path, n=n)
    cmd = [
        _CODEX, "exec", prompt,
        "-C", str(proj),
        "-s", "read-only",
        "--skip-git-repo-check",
        "-c", f'model_reasoning_effort="{effort}"',
    ]
    res = subprocess.run(
        cmd, stdin=subprocess.DEVNULL, capture_output=True,
        text=True, encoding="utf-8", errors="replace", timeout=300,
    )
    return res.stdout


def parse_facts(out: str):
    """Return the last valid JSON array of fact objects in codex output, or None."""
    candidates = JSON_ARRAY_RE.findall(out)
    for raw in reversed(candidates):
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            continue
        if isinstance(data, list) and all(isinstance(x, dict) for x in data):
            return data
    return None


def render_page(session: str, facts: list[dict]) -> str:
    lines = [
        "---",
        "source_harness: claude",
        f"source_session: {session}",
        "type: operating-facts",
        f"fact_count: {len(facts)}",
        "---",
        "",
        "# Operating facts (distilled)",
        "",
    ]
    for f in facts:
        claim = str(f.get("claim", "")).strip()
        cat = str(f.get("category", "uncategorized")).strip()
        ev = str(f.get("evidence", "")).strip()
        if not claim:
            continue
        lines.append(f"- **{cat}**: {claim}")
        if ev:
            lines.append(f'  - evidence: "{ev}"')
    return "\n".join(lines) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser(description="Distill operating-facts from harvested sessions via codex.")
    ap.add_argument("--harvest", default="./harvest", help="dir of harvested session markdown")
    ap.add_argument("--out", default="./distilled", help="output dir for distilled fact pages")
    ap.add_argument("--claims", default="./claims.jsonl", help="append-only structured claims log")
    ap.add_argument("--facts-per-session", type=int, default=8)
    ap.add_argument("--effort", default="low", choices=["low", "medium", "high"])
    ap.add_argument("--limit", type=int, default=0, help="process only first N sessions (0 = all)")
    ap.add_argument("--force", action="store_true", help="re-distill even if a fact page already exists")
    args = ap.parse_args()

    proj = Path.cwd()
    harvest = Path(args.harvest)
    files = sorted(harvest.glob("*.md"))
    if not files:
        print(f"ERROR: no harvested sessions in {harvest}", file=sys.stderr)
        return 2
    if args.limit:
        files = files[: args.limit]

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    claims_fh = open(args.claims, "a", encoding="utf-8")

    total_facts = ok = failed = skipped = 0
    for i, f in enumerate(files, 1):
        session = f.stem
        rel = f"{harvest.name}/{f.name}"
        out_page = out_dir / f"facts-{session}.md"
        if out_page.exists() and not args.force:
            print(f"[{i}/{len(files)}] {session} ... already distilled, skip", flush=True)
            skipped += 1
            continue
        print(f"[{i}/{len(files)}] {session} ...", flush=True)
        try:
            out = run_codex(rel, args.facts_per_session, args.effort, proj)
        except subprocess.TimeoutExpired:
            print("  TIMEOUT", flush=True)
            failed += 1
            continue
        facts = parse_facts(out)
        if not facts:
            print("  no parseable facts (skipped)", flush=True)
            failed += 1
            continue
        for fact in facts:
            claims_fh.write(json.dumps({
                "claim": fact.get("claim", ""),
                "category": fact.get("category", "uncategorized"),
                "evidence": fact.get("evidence", ""),
                "source_session": session,
                "source_harness": "claude",
            }, ensure_ascii=False) + "\n")
        claims_fh.flush()
        out_page.write_text(render_page(session, facts), encoding="utf-8")
        total_facts += len(facts)
        ok += 1
        print(f"  {len(facts)} facts", flush=True)

    claims_fh.close()
    print()
    print(f"sessions distilled: {ok}/{len(files)}  (skipped existing: {skipped}, failed/empty: {failed})")
    print(f"total facts:        {total_facts}")
    print(f"claims log:         {Path(args.claims).resolve()}")
    print(f"fact pages:         {out_dir.resolve()}")
    print("next:  export GBRAIN_HOME=\"$PWD/.brain\"; gbrain import ./distilled/; gbrain embed --all")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
