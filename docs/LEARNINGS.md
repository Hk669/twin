# Learnings

Running notes from building Praxis. Captured iteratively; expect churn.

## 0. Altitude is the whole product (real-user feedback, the most important lesson)
A real user ran Praxis and got a *project field-guide*, not a *portable operating-profile*:
the output was encrusted with their repos/branches/files/tenants — "how I worked in those
repos last month," not "how I operate." ~13% was actively wrong-context in a new project.
The failure is structural (recurs for every persona) because the distiller grabs the most
concrete thing on the page (behavior + proper nouns) instead of climbing to the principle.

Fixes (v0.3.0), all in the distill/profile skills + harvest:
- **Climb to the principle.** "Branches off beta" → "branches off the team's integration
  branch, never assumes main"; the proper noun is demoted to `example`/`evidence`.
- **Three layers, separated:** `mental_model` (how they think) / `operating_habit` (how they
  work) / `environment` (repos/tools — disposable). Output = a portable Operating Model on
  top + a dated, quarantined Environment Ledger.
- **Ban proper nouns** from `principle`/`condition` (the portable fields).
- **North-star gate** on every fact: "true & useful on a project they've never touched?"
- **Rank by recurrence**, tag one-offs `(tentative)`.
- **Closed 10-category list** (was 53 categories for 343 facts).
- **Self-eval:** report a portability %, flag operating lines with proper nouns, refuse to
  silently ship a profile that's mostly environment.
- **Filter eval/automation transcripts at harvest** (repeated identical prompts = no signal).
- **Split install:** Operating Model → global; Environment Ledger → per-project.

The good part the user praised and we kept: context-dependent contradictions (#1 below).

## 1. Context is the whole point — facts are conditional
A flat fact ("user skips tests") is usually wrong. The same person skips tests *when
experimenting* and demands green CI *for an existing system*. So every fact carries a
`condition` (when it applies). Apparent contradictions are context, not conflicts —
never flatten them, never pick a winner. The conditions compose into a decision tree
("in situation A do X, in B do Y") and *that* is the gold, not the bare claims.
See `marketplace/plugins/praxis/skills/distill/SKILL.md`.

## 2. In the harness, the harness is the LLM (free)
The Claude Code plugin distills with parallel subagents — no API key, no model pull. The
whole bring-your-own-LLM problem disappears in-harness. `profile.py`'s OpenAI client is
the *out-of-harness* path only.

## 3. The harness is the LLM — so no provider was needed
We first built a bring-your-own OpenAI-compatible client (one `PROVIDERS` table, provider
sets the base URL) for a standalone CLI. Then realized the plugin doesn't use it: inside
Claude Code, subagents distill and the harness synthesizes — the model is free. We deleted
the external-LLM path and went plugin-only. One source of truth, zero provider/key config.
The standalone CLI is a future option if a non-Claude-Code audience ever shows up.

## 4. Cross-harness is meaningfully richer than one harness
Each tool sees a different facet: Claude Code = how you code; codex = how you run your
machine; a personal agent = how you run autonomous ops. No single harness has the merged
picture. Facts that recur across harnesses are the highest-confidence ones — recurrence
is the confidence signal.

## 5. Substance gate: more than 10 messages
Most sessions are short one-shots (e.g. 85 of 93 codex sessions were too thin). Keeping
only sessions with >10 messages drops the noise cheaply.

## 6. Governance is not optional
A live OAuth token was sitting in plaintext in a retired harness's folder. Anything
sweeping agent directories MUST scrub secrets before storing or emitting, and never
touch auth/cache files. Local-by-default; the user owns the output.

## 7. v2 must be incremental
A full re-distill of all sessions burned ~360k harness tokens. Fine once. The planned
SessionEnd hook must distill ONLY the session that just ended (~25k) and append — never
re-run the world on every session.

## 8. Don't reinvent the substrate
The gold layer can ride an existing local knowledge store (embeddings, graph,
contradiction detection) instead of being rebuilt. Keep it optional and local.

## Packaging direction
Open-core collector + adapter SDK (community writes per-harness adapters), governed team
backend as the commercial layer. Flagship distribution = the Claude Code plugin. See
`docs/PACKAGING.md`.
