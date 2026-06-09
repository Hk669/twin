# Praxis

**Turn your scattered AI-agent sessions into a portable operating-profile.**

You run multiple agent harnesses — Claude Code, codex, a personal agent, more. Each
hoards its own session traces in its own folder, and no single tool has the merged
picture of *how you actually operate*. Praxis harvests those sessions across every
harness on your machine, distills how you work into **contextual** facts, and
synthesizes one portable `AGENTS.md` profile any agent can load.

All local. Secrets scrubbed. You own the output.

## The core idea: context, not flat facts

A flat fact like *"the user skips tests"* is usually wrong. The truth is conditional:
skip tests *when running an experiment*, require green CI *for an existing system*. The
apparent contradiction only exists because the context got stripped.

So every fact Praxis extracts carries a **condition** — when it applies. Contradictions
are treated as context, not conflicts to flatten. Over time those conditions compose into
a decision tree your agents can actually follow: *in situation A do X, in situation B do
Y*. That relational, conditional knowledge is the gold — not the bare claims.

## Two ways to use it

### 1. Claude Code plugin (recommended)

Inside Claude Code the harness *is* the LLM, so there's no API key and no model to pull.

```bash
/plugin marketplace add <this-repo-url>
/plugin install praxis@praxis
/praxis:profile
```

`/praxis:profile` harvests your sessions, distills them with parallel subagents, writes
your `AGENTS.md`, and offers to install it into `~/.claude/CLAUDE.md` or a project.

### 2. Standalone CLI (any harness, bring-your-own LLM)

For codex / cursor / anywhere outside Claude Code. One OpenAI-compatible client; the
provider just sets the base URL (OpenAI, Anthropic, Groq, OpenRouter, local Ollama).

```bash
python harvest.py                 # sweep all harnesses (> 10 messages), scrub secrets
python distill.py                 # extract contextual facts -> claims.jsonl
export ANTHROPIC_API_KEY=...       # or OPENAI_API_KEY=...
python profile.py --provider anthropic   # claims.jsonl -> AGENTS.md
```

## How it works

```
harness sessions ──▶ harvest ──▶ distill (contextual facts) ──▶ synthesize ──▶ AGENTS.md
.claude/.codex/...   scrub +      condition per fact,            merge dups,
                     >10-msg      contradictions = context        keep conditions
```

- **harvest.py** — multi-harness adapter: reads Claude Code, codex, and personal-agent
  session logs, drops tool-call noise, scrubs obvious secrets, keeps substantial
  sessions (more than 10 messages).
- **distill.py** — extracts transferable, *conditional* operating-facts with a verbatim
  evidence quote each, into `claims.jsonl`.
- **profile.py** — synthesizes the facts into one clean `AGENTS.md` operating-profile.
- **marketplace/** — the Claude Code plugin (`/praxis:profile`).

## Governance

- **Local only.** Nothing is uploaded.
- **Secrets scrubbed** at harvest (and dropped if they slip into a fact).
- **You own it.** Delete the output and it's gone. Re-run to refresh.

## Status

Early and iterative. The engine works end to end; the contextual-knowledge model and the
collector/adapter packaging are evolving. See `docs/` for the design and learnings.

## License

MIT
