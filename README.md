# Twin

**A plugin for Claude Code and codex that turns your scattered agent sessions into a portable operating-profile.**

You run multiple agent harnesses — Claude Code, codex, a personal agent, more. Each
hoards its own session traces in its own folder, and no single tool has the merged
picture of *how you actually operate*. Twin harvests those sessions across every
harness on your machine, distills how you work into **contextual** facts, and
synthesizes one portable `AGENTS.md` profile any agent can load.

Inside the harness (Claude Code or codex), the harness *is* the LLM, so there's no API
key, no model to pull, nothing to configure. It's all local, secrets are scrubbed, and you
own the output.

## The core idea: a portable operating model, not a project log

The promise is to capture **how you operate** so it transfers to a project you've never
touched — not a log of what you did last month. Four things make that real:

**Climb to the principle.** "Branches off `beta`" is a log entry; *"branches off the team's
integration branch, never assumes main is the base"* is the operating model. Twin climbs
every behavior to its principle and **bans proper nouns** (repo / branch / file / tenant
names) from the portable layer — they get demoted to evidence.

**Two layers, never mixed.** The output separates a portable **Operating Model** (how you
think and work, zero proper nouns, belongs in your global config) from a dated **Environment
Ledger** (your current repos and tools, belongs per-project).

**Context, not contradiction.** Each principle carries a **condition**: skip tests *when
experimenting*, require green CI *for an existing system* — kept as context-dependent
guidance, never flattened.

**It grades itself.** Before shipping, Twin reports a **portability %** and flags any
operating-model line still carrying a proper noun, so it can't quietly hand you a profile
that's mostly environment trivia.

## Install

**Claude Code:**
```
/plugin marketplace add Hk669/twin
/plugin install twin@twin
/twin:profile
```

**Codex:**
```
codex plugin marketplace add Hk669/twin
codex plugin add twin@twin
```
Then ask codex to "build my operating profile" (or pick the Twin starter prompt).

Either way, Twin:
1. Harvests your sessions from every harness (more than 10 messages each), dropping tool
   noise and eval/automation runs, and scrubbing secrets.
2. Distills them into layered, proper-noun-free principles — the harness is the LLM, no key.
   (Claude Code uses parallel subagents; codex distills sequentially.)
3. Synthesizes a portable **Operating Model** plus a dated **Environment Ledger**, and reports
   its own portability score.
4. Offers to install the Operating Model globally and the Environment Ledger per-project, with consent.

## How it works

```
harness sessions ──▶ harvest (script) ──▶ distill (subagents) ──▶ synthesize ──▶ AGENTS.md
.claude/.codex/...    scrub + >10-msg      condition per fact,      merge,
                                           contradictions=context    keep conditions
```

- **harvest** — `scripts/harvest.py`: deterministic multi-harness parser (Claude Code,
  codex, personal-agent logs). No LLM.
- **distill** — `skills/distill/SKILL.md`: how to write *contextual* facts (each with a
  `condition`; contradictions are context). Run by parallel subagents.
- **synthesize** — `skills/profile/SKILL.md`: merge the facts into one `AGENTS.md`,
  preserving conditions.

## Governance

- **Local only.** Nothing is uploaded.
- **Secrets scrubbed** at harvest (and dropped if they slip into a fact).
- **You own it.** Output lives in the plugin's data dir; delete it and it's gone.

## Roadmap

- **Relational claim structure (the main one).** Move facts from a flat list to a
  structured, relational form the agent can consume well: conditions composed into a
  decision tree, explicit relationships between facts (refines / contradicts / depends-on),
  and an indexed shape an agent navigates instead of reading every claim.
- **Better harness integration.** A `query_profile` MCP tool so agents pull the relevant
  operating-context mid-task, and an incremental `SessionEnd` hook that distills only the
  session that just ended (never re-running the whole history) so the profile stays live.
- **More harness adapters.** Cursor, Windsurf, Aider, Copilot — the harvester is the
  extension point.

## Status

Early and iterative. The plugin works end to end; the contextual-knowledge model and the
relational claim structure are the active work.

## License

MIT
