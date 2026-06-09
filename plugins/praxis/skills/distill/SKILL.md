---
name: distill
description: Rules for extracting operating-facts from a session transcript. Read this BEFORE writing any claims. Governs the climb from behavior to PRINCIPLE, the three layers (mental_model / operating_habit / environment), the proper-noun ban, the north-star portability test, the closed category list, and conditional (context-dependent) claims.
disable-model-invocation: false
---

# Distilling operating-facts — climb to the principle, separate the layers

Your job: read a session transcript and extract how the user OPERATES, written so it
transfers to a project they have never touched. The promise is portability of their
mental model, not a log of what they did. Two failures to avoid above everything else:

1. **Wrong altitude** — storing the behavior and its proper nouns instead of the principle
   behind it. "branches off `beta`" is a log entry; "branches off the team's integration
   branch, never assumes main is the base" is the operating model.
2. **Mixed layers** — letting disposable environment specifics (repos, branches, files,
   tenants, tools) sit in the same stream as transferable principles.

## The north-star test — apply to EVERY fact
> "Would this still be true and useful on a project the person has never touched?"

- **No** → it is `environment`. Tag it and quarantine it; it never enters the operating model.
- **Yes, but it names a specific repo / branch / file / tool / tenant / table / env-var** →
  it is UNDER-ABSTRACTED. **Climb it**: write the principle WITHOUT the proper noun, and put
  the proper noun in `example` / `evidence`.

## Climb the abstraction ladder
For every behavior, ask "what is this an instance of?" Store the principle, not the instance.
- `uses STG_TICKET_TIMELINE` → principle: "states the sample-size caveat before quoting a
  number; refuses a top-N the data can't support" · example: the table name.
- `edited Figma file X, uses v-html in Y` → principle: their taste heuristic / what they
  reject on sight · example: the file/component.
Never store a `mental_model` or `operating_habit` fact whose `principle` or `condition`
contains a proper noun. If you can't phrase it without one, you haven't climbed high enough.

## The three layers
- **`mental_model`** — how they THINK: their bar for proof, risk posture, what they optimize
  for, how they decide scope and tradeoffs. This is the asset. Prize these.
- **`operating_habit`** — how they WORK: commit style, review cadence, when they ask vs act,
  verification habits. Transferable behavior.
- **`environment`** — current repos, branches, files, tenants, tools, env vars, tables.
  Disposable, dated context. Never the operating model.

## Claim schema — one JSON object per fact
```json
{
  "principle":  "<one sentence; transferable; NO proper nouns>",
  "layer":      "mental_model | operating_habit | environment",
  "condition":  "<when it applies; NO proper nouns; empty string for a general default>",
  "why":        "<what it optimizes for / the reasoning behind it — the mental model>",
  "category":   "<EXACTLY one from the closed list below>",
  "evidence":   "<short verbatim quote; proper nouns allowed here>",
  "example":    "<the concrete instance from this session, e.g. a branch/file/tool; allowed here>",
  "source_session": "<file stem>"
}
```
`why` is first-class — it carries the mental model; do not skip it. `principle` and
`condition` are the portable fields and MUST be proper-noun-free.

## Closed category list — use EXACTLY one; do not invent categories
`proof_and_verification`, `risk_and_safety`, `scope_and_tradeoffs`,
`code_quality_and_architecture`, `collaboration_and_autonomy`, `communication_and_reporting`,
`workflow_and_tooling`, `design_and_ux`, `data_and_analysis`, `learning_and_iteration`

## Conditions = context, not contradiction
When two principles seem to conflict, find the distinguishing condition and keep BOTH
(e.g. "defer tests when the work is experimental or throwaway" vs "require green CI before
done on existing or production systems"). Never flatten, never pick a winner. Conditions
must also be proper-noun-free.

## Skip entirely
- Topic-specific content (the actual task or domain).
- Anything true of almost any developer.
- Secrets — drop the fact.
- **Eval / benchmark / automation runs:** if the session is repeated near-identical prompts
  (a benchmark or an automated loop), it carries no preference signal — skip the whole session.

## Output
Return ONLY a JSON array of fact objects in the schema above. No prose, no fences.
