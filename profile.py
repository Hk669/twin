#!/usr/bin/env python3
"""
profile.py -- synthesize claims.jsonl into a clean AGENTS.md operating-profile.

Bring-your-own LLM, kept dead simple: one OpenAI-compatible client. The provider
just selects the base URL + which API-key env var to read. OpenAI and Anthropic
models work through the same code path (Anthropic ships an OpenAI-compatible
endpoint); add a row to PROVIDERS for anything else.

Usage:
    python profile.py                                   # provider=openai, model gpt-4o-mini
    python profile.py --provider anthropic --model claude-sonnet-4-6
    python profile.py --provider ollama --model llama3.2     # local, no key
Env: reads <PROVIDER>_API_KEY (e.g. OPENAI_API_KEY, ANTHROPIC_API_KEY).
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from openai import OpenAI

# provider -> (base_url, api_key_env, default_model). That's the whole config.
PROVIDERS = {
    "openai":     ("https://api.openai.com/v1",      "OPENAI_API_KEY",     "gpt-5.5"),
    "anthropic":  ("https://api.anthropic.com/v1/",  "ANTHROPIC_API_KEY",  "claude-sonnet-4-6"),
    "groq":       ("https://api.groq.com/openai/v1", "GROQ_API_KEY",       "llama-3.3-70b-versatile"),
    "openrouter": ("https://openrouter.ai/api/v1",   "OPENROUTER_API_KEY", "anthropic/claude-sonnet-4.6"),
    "ollama":     ("http://localhost:11434/v1",      None,                 "llama3.2"),
}

SYSTEM = (
    "You synthesize a developer's scattered agent-session facts into ONE portable "
    "operating-profile that any AI coding agent loads at the start of a session to "
    "behave the way this specific developer expects. Be concrete, directive, "
    "deduplicated, and concise. Keep only what is distinctive to this person."
)

USER = """\
The facts below were extracted from one developer's AI-agent sessions across several tools
(Claude Code = coding, codex = system/terminal, a personal agent = autonomous ops). Each is
a "how they operate" claim with a category.

Write a single AGENTS.md operating-profile:
- Open with a 2-3 sentence summary of how this person works.
- Then 6-10 themed sections, each a few short imperative bullets ("Do X", "Avoid Y").
- Merge duplicates. A claim that recurs across different tools is high-confidence; keep it.
- Where claims genuinely conflict (e.g. ship fast vs always test), give context-dependent
  guidance, not a contradiction.
- Cut anything true of almost any developer; keep only what is distinctive to THIS person.
- Output ONLY the markdown. No code fences, no preamble.

FACTS ({n}):
{facts}
"""


def make_client(provider: str) -> tuple[OpenAI, str]:
    if provider not in PROVIDERS:
        sys.exit(f"unknown provider '{provider}'. options: {', '.join(PROVIDERS)}")
    base_url, key_env, _ = PROVIDERS[provider]
    api_key = os.environ.get(key_env) if key_env else "ollama"
    if not api_key:
        sys.exit(f"set {key_env} to use provider '{provider}'.")
    return OpenAI(base_url=base_url, api_key=api_key), base_url


def main() -> int:
    ap = argparse.ArgumentParser(description="Synthesize claims.jsonl -> AGENTS.md via a BYO OpenAI-compatible LLM.")
    ap.add_argument("--provider", default="openai", choices=list(PROVIDERS))
    ap.add_argument("--model", default=None, help="override the provider's default model")
    ap.add_argument("--claims", default="claims.jsonl")
    ap.add_argument("--out", default="AGENTS.md")
    args = ap.parse_args()

    rows = [json.loads(l) for l in open(args.claims, encoding="utf-8") if l.strip()]
    if not rows:
        sys.exit("no facts in claims.jsonl")

    client, base_url = make_client(args.provider)
    model = args.model or PROVIDERS[args.provider][2]
    facts = "\n".join(f"- [{r['category']}] {r['claim']}" for r in rows)

    print(f"synthesizing {args.out} from {len(rows)} facts via {args.provider}:{model} ({base_url}) ...")
    resp = client.chat.completions.create(
        model=model,
        temperature=0.3,
        messages=[
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": USER.format(n=len(rows), facts=facts)},
        ],
    )
    md = (resp.choices[0].message.content or "").strip()
    if not md:
        sys.exit("engine returned no output")

    Path(args.out).write_text(md + "\n", encoding="utf-8")
    print(f"wrote {args.out} ({len(md)} chars, {md.count(chr(10)) + 1} lines)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
