---
name: profile
description: Build the user's portable operating-profile from their lived agent sessions across every harness on this machine (Claude Code, codex, hermes, ...). Harvests sessions, distills how the user operates into cited contextual facts, and synthesizes a clean AGENTS.md the user's agents can load. Use when the user says "profile me", "build my operating profile", "what does my agent know about how I work", or invokes the profile command.
---

# Praxis — Operator Profile

Turn the user's scattered agent sessions into one portable operating-profile. You (the
harness) are the language model for this job, so there is no API key and no external
model: you read the sessions and distill them yourself.

Everything is local. Nothing leaves the machine.

## Paths (harness-agnostic)
- **`<plugin-root>`** = this plugin's installed directory (where `scripts/` and `skills/`
  live). On Claude Code it is `${CLAUDE_PLUGIN_ROOT}`. In other harnesses, resolve this
  plugin's install path and use it.
- **`<work-dir>`** = a writable folder for output. On Claude Code use
  `${CLAUDE_PLUGIN_DATA}`; otherwise create and use `./.praxis/`.

## Step 0 — orient
Tell the user in one line what you're about to do: harvest their agent sessions from every
harness on this machine, distill how they operate, and write a portable `AGENTS.md`. All
local, secrets scrubbed. Then proceed.

## Step 1 — harvest (deterministic, a script)
Run the bundled harvester. It sweeps `~/.claude`, `~/.codex`, and the hermes sessions dir,
keeps only sessions with more than 10 messages, drops tool-call noise, and scrubs obvious
secrets:

```bash
python "<plugin-root>/scripts/harvest.py" --out "<work-dir>/harvest"
```

Report the per-harness counts it prints. The harvested files are provenance-headed markdown
at `<work-dir>/harvest/*.md`. If zero sessions are harvested, tell the user and stop.

## Step 2 — distill (you are the LLM)
Extract TRANSFERABLE, CONTEXTUAL operating-facts. The value is in the CONDITIONS each fact
applies under and the relationships between facts, not flat rules. Before writing any
claims, read the rules at `<plugin-root>/skills/distill/SKILL.md` — they govern the claim
schema (including the all-important `condition` field) and how to treat apparent
contradictions (context-dependent, never flattened).

Process every harvested session. **If your harness has a parallel subagent / Task tool,**
dispatch subagents over batches of ~5 session files in parallel for speed (give each
subagent the absolute path to `skills/distill/SKILL.md` to read first, plus its batch).
**Otherwise, process the sessions sequentially yourself**, following the same distill rules.

Each session yields a JSON array of objects with keys `claim`, `condition` (WHEN it applies;
empty string for a general default), `category`, `evidence` (verbatim quote), and
`source_session` (the file stem). Aggregate every fact into `<work-dir>/claims.jsonl`, one
JSON object per line. Drop any fact whose evidence contains a secret.

## Step 3 — synthesize the profile
From `claims.jsonl`, write a clean operating-profile to `<work-dir>/AGENTS.md`:

- Open with a 2-3 sentence summary of how this person operates.
- Then 6-10 themed sections, each a few short imperative bullets.
- **Preserve conditions.** When a fact has a `condition`, write it as conditional guidance,
  not a flat rule: "When running experiments or throwaway code, defer tests to move fast;
  for existing or production systems, require green CI before done." Never flatten a
  context-dependent pair into one averaged rule, and never drop one side.
- Merge true duplicates. A fact that recurs across different harnesses is high-confidence.
- Cut anything true of almost any developer; keep only what is distinctive to THIS user.

## Step 4 — deliver and offer to install
Show the user the synthesized profile. Then offer to install it so their agents actually
use it. Get explicit consent and show exactly what you'll write before writing:

- **Global:** append/merge it into the harness's global instructions file — `~/.claude/CLAUDE.md`
  for Claude Code, `~/.codex/AGENTS.md` for codex.
- **Project:** write `AGENTS.md` into the current project (loaded by agents that read AGENTS.md).
- **Neither:** leave it at `<work-dir>/AGENTS.md` for them to use however they like.

## Governance (always)
- Local only. Nothing is uploaded.
- Secrets are scrubbed at harvest; drop any that slip into a fact.
- The user owns the output. Deleting `<work-dir>` removes everything.
- Re-running refreshes the profile from the latest sessions.

## Notes
- The harness is the LLM here — the model is free. The harvester reads every harness, not
  just the one you're running in; the value is the merged picture no single harness has.
