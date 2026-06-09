# Packaging & Distribution — Open-core collector + adapter SDK

Decision (2026-06-09): package the harvest+govern engine as an **open-source
collector with a plugin SDK**, plus a **commercial governed team backend**.
This is NOT a package manager (microsoft/apm owns that — pushing authored context
INTO harnesses). This is the inverse: pull lived traces OUT of every harness into
one governed place.

## Mental model: the OTel-collector / Vector, for agent traces
A shape devs already trust for "collect all of X into one spot and govern it."

```
INPUT ADAPTERS              PROCESSORS (govern)         SINKS
.claude  ┐                  redact secrets              gold lake (gbrain)
.codex   ┼──▶ collect ────  consent / scope ────▶ emit  OTel backend
.cursor  ┤                  retention / TTL             AGENTS.md / APM pack
hermes   ┘                  egress policy (local-first) jsonl
```

## The three SDK contracts (this is the distribution multiplier)
You will never write a clean adapter for every harness (Cursor, Windsurf, Aider,
Cline, Copilot, ...). The community will, IF the interfaces are tight.

- **Adapter (input):** `discover() -> [sources]`; `parse(source) -> Iterator[Session]`
- **Processor (govern):** `process(Session) -> Session | None` (redact, consent, TTL, min-messages, drop)
- **Sink (output):** `write(Session)` (gold lake, OTel spans, AGENTS.md, APM pack)

Normalized `Session = {harness, session_id, turns[], provenance, used_tools, ts}`.

## We are already ~60% there
| v0 today | becomes |
|---|---|
| `harvest.py` per-harness parsers (`iter_claude/codex/hermes`) | built-in **Adapters** |
| `scrub_secrets` + `>10-msg` + `--stateless-only` | **Processors** |
| `gbrain import` / `embed` | a **Sink** |
| `distill.py` | a post-sink **gold-layer** stage |

The refactor = lift these into the three interfaces + a declarative `pipeline.yml`.

## pipeline.yml — the governance artifact devs commit
```yaml
adapters: [claude, codex, cursor]
processors:
  - redact: { patterns: default }
  - min_messages: 10
  - egress: local_only        # nothing leaves the machine
sinks: [gbrain, agents_md]
```

## OSS vs commercial (open-core)
- **OSS (MIT):** collector core, the 3 SDK interfaces, built-in adapters,
  local sinks (gbrain / jsonl / AGENTS.md), secret-scrub, `pipeline.yml`, OTel sink.
  This is the adoption wedge.
- **Commercial (governed backend):** the governed team backend sink — central lake,
  cross-dev policy enforcement, cross-dev distillation, retention + audit,
  right-to-forget, hosted adapter registry. This is the business: a catalog +
  governance layer pointed at agent traces instead of data assets (a natural fit for
  an enterprise data-governance product).

## OTel hook (lower the cost to try it)
Map `Session` <-> OpenTelemetry GenAI spans so devs pipe agent traces into the
observability backend they already run (Langfuse / Phoenix / Arize). No new
backend required just to evaluate it.

## Distribution mechanics
- `pipx` / `npm` / `brew` single-command install.
- Zero-config first run: auto-discover harnesses (already works — found
  `.claude`, `.codex`, hermes on this machine), consent per source, secret-scrub
  on by default, local by default.
- Adapter registry so the community ships harness coverage.
- Emit distilled context to AGENTS.md / APM — the output rails from the
  office-hours design (`adopt the rails, own the engine`).

## Why governance is not optional
Real finding during the build: a live OAuth token sat in plaintext in the
openclaw folder. Anything harvesting agent dirs MUST redact before store/egress.
Governance is the product surface, not a checkbox.

## Name (placeholder)
Project codename stays "Praxis". The collector could ship as `lode` (a vein of
ore), `tracelake`, or `agentlake`. TBD.

## v1 distribution: Claude Code plugin (BUILT 2026-06-09)
Flagship channel = a Claude Code plugin. Decisive reason: the harness provides the two
hardest things for free — the LLM (Claude distills the sessions itself; no key, no model)
and the install/run surface (`/praxis:profile`). `profile.py`'s BYO OpenAI client is the
OUT-of-harness path; in-harness needs no key.

Structure (`marketplace/`):
```
marketplace/.claude-plugin/marketplace.json
marketplace/plugins/praxis/.claude-plugin/plugin.json
marketplace/plugins/praxis/skills/profile/SKILL.md   -> /praxis:profile
marketplace/plugins/praxis/scripts/harvest.py        (bundled engine)
```
The plugin is a THIN skin over the engine: SKILL.md runs `harvest.py`, dispatches
subagents to distill (the harness is the LLM), synthesizes `AGENTS.md`, offers to install
it into `~/.claude/CLAUDE.md` or a project. `claude plugin validate` passes. Output lives
in `${CLAUDE_PLUGIN_DATA}`; local-only; secrets scrubbed.

Install/test locally:
```
claude --plugin-dir ~/projects/agent-context-engine/marketplace/plugins/praxis   # then /praxis:profile
# or, simulating distribution:
/plugin marketplace add ~/projects/agent-context-engine/marketplace
/plugin install praxis@praxis
```

Same thin-skin pattern later gives a codex/cursor wrapper. The standalone CLI (below)
stays the harness-neutral path.

## Next
1. Refactor v0 scripts into `adapters/ processors/ sinks/` + a `pipeline.yml` runner.
2. Keep `distill.py` as the gold-layer stage after the sink.
3. Add an `otel` sink + map the normalized Session to GenAI spans.
4. Spec the Adapter SDK + a CONTRIBUTING guide (the contributor experience is
   what makes the community-adapter bet pay off).
