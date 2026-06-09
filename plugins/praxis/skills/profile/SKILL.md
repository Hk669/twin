---
name: profile
description: Build the user's portable operating-profile from their lived agent sessions across every harness on this machine (Claude Code, codex, hermes, ...). Harvests sessions, distills how the user operates into layered, proper-noun-free principles, and synthesizes a portable Operating Model (plus a quarantined Environment Ledger) the user's agents can load. Use when the user says "profile me", "build my operating profile", "what does my agent know about how I work", or invokes the profile command.
---

# Praxis — Operator Profile

Turn the user's scattered agent sessions into a PORTABLE operating-profile. You (the
harness) are the language model for this job, so there is no API key and no external model.

The promise is **transfer of how the person operates**, not a log of what they did. The
single hardest part of this job is altitude: climb from behavior to principle, and keep
the portable operating model strictly separate from disposable environment specifics.

Everything is local. Nothing leaves the machine.

## Paths (harness-agnostic)
- **`<plugin-root>`** = this plugin's installed directory (`${CLAUDE_PLUGIN_ROOT}` on Claude
  Code; otherwise resolve this plugin's install path).
- **`<work-dir>`** = a writable output folder (`${CLAUDE_PLUGIN_DATA}` on Claude Code;
  otherwise `./.praxis/`).

## Step 1 — harvest
Run the bundled harvester (sweeps the harnesses, keeps sessions with more than 10 messages,
drops tool noise + eval/automation runs, scrubs secrets):

```bash
python "<plugin-root>/scripts/harvest.py" --out "<work-dir>/harvest"
```
Report the per-harness counts. If zero sessions, stop.

## Step 2 — distill (you are the LLM)
**Read `<plugin-root>/skills/distill/SKILL.md` first — it is the contract.** It governs the
climb to principle, the three layers (`mental_model` / `operating_habit` / `environment`),
the proper-noun ban on `principle`/`condition`, the north-star test, and the closed category
list.

Process every harvested session. If your harness has a parallel subagent / Task tool, batch
~5 sessions per subagent (give each the path to `skills/distill/SKILL.md` to read first);
otherwise process sequentially. Aggregate every fact (the full schema, including `layer`,
`why`, and `example`) into `<work-dir>/claims.jsonl`, one JSON object per line. Drop any fact
whose evidence contains a secret.

## Step 3 — synthesize (operating model on top, environment quarantined)
Cluster equivalent principles across all sessions; merge near-duplicates. For each cluster,
count the distinct sessions AND harnesses it appears in — that recurrence is your confidence.

Write `<work-dir>/AGENTS.md` in TWO clearly separated parts:

### Operating Model (the product — portable)
- 8–12 first-principle heuristics drawn ONLY from `mental_model` and `operating_habit` facts.
  **Zero proper nouns.** Every line must pass the north-star test: true and useful on a
  project the person has never touched.
- Group under the closed categories. Lead each group with the highest-recurrence principles.
- Preserve conditions (context-dependent guidance, never flattened into one averaged rule).
- Mark any principle seen in only one session `(tentative)`.
- Where possible, state the *why* (the mental model), not just the rule.

### Environment Ledger (quarantined — dated, disposable)
- A separate section headed: **"Context as of <today's date> — verify before relying."**
- All `environment` facts: repos, branches, files, tenants, tools, env vars, tables.
- Keep these COMPLETELY out of the Operating Model.

## Step 3.5 — self-eval (gate before you ship)
Score the Operating Model and show the user:
- **Portability %** = fraction of Operating Model lines that pass the north-star test
  (transferable, no proper nouns). Compute it and report the number.
- **Proper-noun leaks** = list any Operating Model line that still contains a proper noun.
  For each: climb it (rewrite without the noun) or move it to the Environment Ledger.
- If a large fraction of the Operating Model is environment trivia, **say so loudly and fix
  it before delivering.** Never silently ship a profile that is mostly environment.

## Step 4 — deliver and install (route the two layers differently)
Show the user both parts and the self-eval scores. Then offer to install, with consent, and
show exactly what you'll write first:
- **Operating Model → GLOBAL** instructions (`~/.claude/CLAUDE.md` for Claude Code,
  `~/.codex/AGENTS.md` for codex). It is portable, so it belongs everywhere.
- **Environment Ledger → PER-PROJECT** (the current project's `AGENTS.md`) or left in
  `<work-dir>`. Never put environment trivia into the global config.

## Governance
- Local only. Secrets scrubbed at harvest; drop any that slip into a fact.
- The user owns the output. Deleting `<work-dir>` removes everything. Re-run to refresh.
