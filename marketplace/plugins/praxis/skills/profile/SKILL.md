---
name: profile
description: Build the user's portable operating-profile from their lived agent sessions across every harness on this machine (Claude Code, codex, hermes, ...). Harvests sessions, distills how the user operates into cited facts, and synthesizes a clean AGENTS.md the user's agents can load. Use when the user says "profile me", "build my operating profile", "what does my agent know about how I work", or invokes /praxis:profile.
---

# Praxis — Operator Profile

Turn the user's scattered agent sessions into one portable operating-profile. You (the
harness) are the language model for this job, so there is no API key and no external
model: you read the sessions and distill them yourself.

Everything is local. Nothing leaves the machine.

## Step 0 — orient
Tell the user what you're about to do in one line: harvest their agent sessions from
every harness on this machine, distill how they operate, and write a portable
`AGENTS.md` profile. All local, secrets scrubbed. Then proceed.

Use `${CLAUDE_PLUGIN_DATA}` as the working directory for all output (it persists across
plugin updates). Use `${CLAUDE_PLUGIN_ROOT}` to find bundled scripts.

## Step 1 — harvest (deterministic, a script)
Run the bundled harvester. It sweeps `~/.claude`, `~/.codex`, and the hermes sessions
dir, keeps only sessions with more than 10 messages, drops tool-call noise, and scrubs
obvious secrets:

```bash
python "${CLAUDE_PLUGIN_ROOT}/scripts/harvest.py" --out "${CLAUDE_PLUGIN_DATA}/harvest"
```

Report the per-harness counts it prints (claude / codex / hermes). The harvested files
are provenance-headed markdown at `${CLAUDE_PLUGIN_DATA}/harvest/*.md`.

If zero sessions are harvested, tell the user and stop.

## Step 2 — distill (you are the LLM; use subagents for speed)
Extract TRANSFERABLE, CONTEXTUAL operating-facts. The value is in the CONDITIONS each
fact applies under and the relationships between facts, not flat rules. Before writing
any claims, read the rules at `${CLAUDE_PLUGIN_ROOT}/skills/distill/SKILL.md` — they
govern the claim schema (including the all-important `condition` field) and how to treat
apparent contradictions (context-dependent, never flattened).

For speed, dispatch subagents (the Task/Agent tool) over batches of ~5 session files, in
parallel. In each subagent's prompt: (a) resolve `${CLAUDE_PLUGIN_ROOT}` to an absolute
path and tell the subagent to read `<that path>/skills/distill/SKILL.md` FIRST and follow
it, (b) give it its batch of files. Each subagent returns a JSON array of objects with
keys `claim`, `condition` (WHEN it applies; empty string for a general default),
`category`, `evidence` (verbatim quote), and `source_session` (the file stem).

Aggregate every fact into `${CLAUDE_PLUGIN_DATA}/claims.jsonl` — one JSON object per line.
Drop any fact whose evidence contains a secret.

## Step 3 — synthesize the profile
From `claims.jsonl`, write a clean operating-profile to `${CLAUDE_PLUGIN_DATA}/AGENTS.md`:

- Open with a 2-3 sentence summary of how this person operates.
- Then 6-10 themed sections (e.g. Code quality, Safety & secrets, Git discipline,
  Autonomy & collaboration, System & environment, Verification, Communication), each a
  few short imperative bullets ("Do X", "Avoid Y").
- **Preserve conditions.** When a fact has a `condition`, write it as conditional
  guidance, not a flat rule: "When running experiments or throwaway code, defer tests to
  move fast; for existing or production systems, require green CI before done." Never
  flatten a context-dependent pair into one averaged rule, and never drop one side.
- Merge true duplicates. A fact that recurs across different harnesses is high-confidence.
- Cut anything true of almost any developer; keep only what is distinctive to THIS user.

## Step 4 — deliver and offer to install
Show the user the synthesized profile. Then offer to install it so their agents actually
use it. Get explicit consent and show exactly what you'll write before writing:

- **Global:** append/merge it into `~/.claude/CLAUDE.md` (every Claude Code session loads it).
- **Project:** write `AGENTS.md` into the current project (loaded by agents that read AGENTS.md).
- **Neither:** leave it at `${CLAUDE_PLUGIN_DATA}/AGENTS.md` for them to use however they like.

## Governance (always)
- Local only. Nothing is uploaded.
- Secrets are scrubbed at harvest; drop any that slip into a fact.
- The user owns the output. Deleting `${CLAUDE_PLUGIN_DATA}` removes everything.
- Re-running refreshes the profile from the latest sessions.

## Notes
- This is the in-harness path: the model is free (it's you). The standalone CLI and
  `profile.py` (bring-your-own OpenAI-compatible LLM) cover users outside Claude Code.
- The harvester reads every harness, not just Claude Code — the value is the merged
  picture no single harness has.
