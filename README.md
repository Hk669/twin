# Praxis

**A Claude Code plugin that turns your scattered agent sessions into a portable operating-profile.**

You run multiple agent harnesses — Claude Code, codex, a personal agent, more. Each
hoards its own session traces in its own folder, and no single tool has the merged
picture of *how you actually operate*. Praxis harvests those sessions across every
harness on your machine, distills how you work into **contextual** facts, and
synthesizes one portable `AGENTS.md` profile any agent can load.

Inside Claude Code the harness *is* the LLM — so there's no API key, no model to pull,
nothing to configure. It's all local, secrets are scrubbed, and you own the output.

## The core idea: context, not flat facts

A flat fact like *"the user skips tests"* is usually wrong. The truth is conditional:
skip tests *when running an experiment*, require green CI *for an existing system*. The
apparent contradiction only exists because the context got stripped.

So every fact Praxis extracts carries a **condition** — when it applies. Contradictions
are treated as context, not conflicts to flatten. Those conditions are meant to compose
into a decision tree your agents can follow: *in situation A do X, in situation B do Y*.
That relational, conditional knowledge is the gold — not the bare claims.

## Install

```
/plugin marketplace add <this-repo-url>
/plugin install praxis@praxis
/praxis:profile
```

`/praxis:profile`:
1. Harvests your sessions from every harness on the machine (more than 10 messages each),
   dropping tool noise and scrubbing secrets.
2. Distills them with parallel subagents — Claude is the LLM, no key.
3. Synthesizes your `AGENTS.md` operating-profile.
4. Offers to install it into `~/.claude/CLAUDE.md` (global) or a project, with your consent.

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
relational claim structure are the active work. See `docs/` for design and learnings.

## License

MIT
