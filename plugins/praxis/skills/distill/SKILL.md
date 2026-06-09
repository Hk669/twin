---
name: distill
description: Rules for extracting operating-facts from a session transcript. Read this BEFORE writing any claims. Governs the claim schema, the all-important `condition` field, how to treat apparent contradictions (they are context-dependent, not conflicts to flatten), and how to build knowledge relationships instead of flat lists.
disable-model-invocation: false
---

# Distilling operating-facts — write context, not flat rules

Your job is to read a session transcript and extract TRANSFERABLE facts about how the
user operates. But a flat fact is usually a wrong fact. The value of this whole system
is the **conditions** under which a fact applies and the **relationships** between facts.
That is the gold. Bare claims are not.

## The claim schema
One JSON object per fact:

```json
{
  "claim":     "<one sentence: what the user does or prefers>",
  "condition": "<WHEN/WHERE this applies — the context. Empty string if it is a general default>",
  "category":  "<snake_case>",
  "evidence":  "<short verbatim quote from the transcript>",
  "source_session": "<file stem>"
}
```

`condition` is the most important field. Before writing any claim, ask: **under what
circumstances did the user say or do this?** Put that answer in `condition`.

## Why context is the whole point
Consider: "the user skips tests." As a flat rule this is FALSE and harmful. Read the
transcript — the user skipped tests *while running an experiment*, to move fast on
throwaway code. The same user, on an existing production system, wants green CI before
calling something done. Those are not a contradiction. They are two conditional facts:

```json
{"claim":"Defers tests to move faster","condition":"experimental, throwaway, or exploratory work","category":"verification","evidence":"lets not waste tokens for tests right now"}
{"claim":"Requires tests and green CI before done","condition":"existing or production systems","category":"verification","evidence":"we need green CI before we call it shipped"}
```

Same person, opposite behavior, fully consistent once the condition is attached.

## Read the transcript for the condition signals
Look for what situation the user was in when a preference showed up:
- New experiment / prototype / throwaway vs an existing or production system.
- High-stakes (money, infra, secrets, live automation) vs quick/low-stakes.
- Which tool/harness, which language, which phase (planning vs implementing vs shipping).
- Whether the user was learning vs operating fluently.
- Whether trust had been established (autonomy granted) vs early in a task.

If a preference clearly always holds, leave `condition` empty — that is a genuine default.
If it only showed up in a specific situation, name that situation. When unsure, describe
the situation you actually observed rather than generalizing.

## Apparent contradictions = context, not conflict
When two facts seem to conflict, DO NOT pick a winner, average them, or drop one. Find
the context that distinguishes them and write BOTH as conditional facts. If you truly
cannot find a distinguishing context, keep both and say so in their conditions
("seen in X but not clearly scoped") — never invent a resolution.

## Build relationships, not a flat list
- When a fact is a context-specific exception to a more general one, make it explicit:
  the general fact with empty condition, plus the exception with its condition.
- Prefer specific conditional facts over vague general ones.
- Over time these conditions compose into a decision tree the user's agents can follow:
  "in situation A do X, in situation B do Y." That tree is the deliverable.

## Skip
- Topic-specific content (the actual task or domain).
- Anything true of almost any developer.
- Secrets — if a candidate fact's evidence contains one, drop the fact.

## Output
Return ONLY a JSON array of fact objects in the schema above. No prose, no fences.
