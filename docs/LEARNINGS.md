# Learnings

Running notes from building Praxis. Captured iteratively; expect churn.

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

## 3. BYO-LLM, kept trivial
One OpenAI-compatible client. The provider selects the base URL; OpenAI and Anthropic run
through the same code path (Anthropic ships an OpenAI-compatible endpoint). No CLI
shelling, no engine detection — just a `PROVIDERS` table.

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
