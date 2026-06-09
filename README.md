# Twin

**A plugin for Claude Code and codex that turns your scattered agent sessions into a portable operating-profile — and keeps it alive.**

You run multiple agent harnesses — Claude Code, codex, a personal agent, more. Each
hoards its own session traces in its own folder, and no single tool has the merged
picture of *how you actually operate*. Twin harvests those sessions across every
harness on your machine, distills how you work into **contextual** facts, and
synthesizes one portable `AGENTS.md` profile any agent can load.

Twin is not code — it's a **playbook**. The harness already has the data and the tools;
Twin hands it the operating manual: pure-markdown skills and reference files the harness
executes itself. No API key, no model to pull, nothing to configure. It's all local,
secrets are scrubbed, and you own the output.

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

**It stays alive.** A profile built once decays into a horoscope. Twin is four playbooks,
not one: build it, refresh it incrementally, audit it against its own evidence, and query
it mid-task.

## Install

**Claude Code:**
```
/plugin marketplace add Hk669/twin
/plugin install twin@twin
/twin:profile        # then later: /twin:update · /twin:audit · /twin:query
```

**Codex:**
```
codex plugin marketplace add Hk669/twin
codex plugin add twin@twin
```
Then ask codex to "build my operating profile" (or pick the Twin starter prompt).

Either way, Twin:
1. Triages your sessions across every harness (more than 10 messages each), ignoring tool
   noise and eval/automation runs, and redacting secrets.
2. Distills them into layered, proper-noun-free principles — the harness is the LLM, no key.
   (Claude Code uses parallel subagents; codex distills sequentially.)
3. Synthesizes a portable **Operating Model** plus a dated **Environment Ledger**, and reports
   its own portability score.
4. Offers to install the Operating Model globally and the Environment Ledger per-project, with consent.

## The suite

| Skill | What it does |
|---|---|
| **`profile`** | The full build: triage → distill → synthesize → self-eval → install. |
| **`update`** | Incremental refresh — distills only sessions newer than the last run, re-synthesizes over all claims, shows you the diff. |
| **`audit`** | Adversarial grading — verifies every line against its cited evidence (supported / overreach / unfounded), screens for horoscope lines, finds unconditioned contradictions, re-scores portability. Delivers a scorecard with a trust grade. |
| **`query`** | "How do I usually handle X?" — answers from the claims with citations and conditions, or says plainly that the profile doesn't know. Works for other agents pulling your operating context mid-task. |

## How it works

**No runtime code.** Twin is pure markdown — skill playbooks plus a shared reference
registry. The harness *is* the runtime: it reads the registry, finds your sessions with its
own tools, and does the distillation itself. Nothing in this repo executes at profile time.

```
harness sessions ──▶ triage ──────────▶ distill (subagents) ──▶ synthesize ──▶ AGENTS.md
.claude/.codex/...    registry + Glob    raw JSONL, read direct,   merge, link,
                      >10-msg gate        condition per fact         keep conditions
```

Four skill playbooks share one reference library, loaded only at the step that needs it
(progressive disclosure):

```
plugins/twin/
├── skills/
│   ├── profile/SKILL.md           full build: triage → distill → synthesize → self-eval
│   ├── update/SKILL.md            incremental refresh from sessions newer than the last run
│   ├── audit/SKILL.md             adversarial grading of every claim against its evidence
│   └── query/SKILL.md             cited answers to "how do I usually handle X?"
└── references/
    ├── harnesses.md               registry: per-harness sessions + memory (Claude Code, codex,
    │                              Cursor, Gemini CLI, Aider, opencode, Copilot, hermes, …),
    │                              schemas with sample lines, noise, secrets, the gate
    ├── distillation.md            how to climb a transcript into claims — with worked examples
    ├── output-format.md           synthesis + link pass, exact templates, self-eval, install routing
    └── auditing.md                the four audit checks, verdicts, scorecard, prescribed fixes
```

Output is two files (categories are headings, not a directory): `AGENTS.md` — the portable
**Operating Model**, installs global — and `environment-ledger.md` — your dated specifics,
installs per-project. Both compile from `claims.jsonl`, the regenerable source of truth, where
each claim carries a stable id and (after synthesis) relation edges — `refines`,
`conflicts_with`, `depends_on` — that the audit and query playbooks traverse.

## Governance

- **Local only.** Nothing is uploaded. No code runs — it's the harness reading your files.
- **Secrets redacted** at read time (and any fact that would carry one is dropped).
- **You own it.** Output lives in the plugin's data dir; delete it and it's gone.

## Roadmap

- **Deeper relational structure.** Claims now carry `refines` / `conflicts_with` / `depends_on`
  edges drawn at synthesis; next is composing conditions into a navigable decision tree so an
  agent walks to the right principle instead of reading every claim.
- **Automatic freshness.** A `SessionEnd` hook that runs the `update` playbook on just the
  session that ended, and a `query_profile` MCP tool as the always-on version of the `query`
  skill.
- **An eval benchmark.** Three levels, borrowed from personalization/memory research: extraction
  faithfulness (the `audit` checks, scored against a gold set), profile quality (Barnum rate,
  portability), and downstream lift (does loading the profile measurably improve an agent on
  real tasks, with bias controls).
- **More harness adapters.** Cline, Roo, Zed, … — adding one is a few lines in the
  `plugins/twin/references/harnesses.md` registry (sessions glob + role/content fields), no code.

## Status

Early and iterative. The four playbooks work end to end; the relational claim structure and
the eval benchmark are the active work.

## License

MIT
