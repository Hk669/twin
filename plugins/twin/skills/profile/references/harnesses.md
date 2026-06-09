# Reference: harness registry — where lived agent data lives, and how to read it

Read this when you need to **find and read** a user's sessions or memory. It is the map: per
harness, where files live, the exact JSONL shape (with a real sample line), where memory lives,
the noise to ignore, the secrets to redact, and the substance gate. There is no harvester
script — you are the runtime. Use Glob to find files, Read to open them, and the shell
one-liner at the bottom for cheap triage. Everything is local; nothing leaves the machine.

## Contents
- [How a transcript is shaped](#how-a-transcript-is-shaped)
- [Claude Code](#claude-code)
- [codex](#codex)
- [hermes (or any personal agent)](#hermes-or-any-personal-agent)
- [Bring your own harness (HITL)](#bring-your-own-harness-hitl)
- [Memory files (all harnesses)](#memory-files-all-harnesses)
- [What to ignore + never emit](#what-to-ignore--never-emit)
- [The substance gate](#the-substance-gate)
- [Triage one-liner](#triage-one-liner)

`~` is the home dir (`/Users/<you>` on macOS, `/home/<you>` on Linux, `C:\Users\<you>` on
Windows). `~/.claude` and `~/.codex` live in the home dir on **every** platform; only the
personal-agent app-data dir is OS-specific. Glob first — paths that don't exist are skipped;
never assume a harness is installed.

---

## How a transcript is shaped
Every harness stores a session as **JSONL** — one JSON object per line, one line per event.
Most lines are noise (tool calls, tool results, reasoning, meta events). You want only the
lines that are a **user or assistant message**, and from each you want the **plain text**. The
three things that differ per harness are: (1) the glob, (2) which field holds the role, and
(3) which field holds the content. Everything below is just those three things plus a sample.

`content` is either a plain string OR an array of blocks. Extract text by concatenating the
`.text` of every block that has one. Blocks with no `.text` field — tool calls, tool results,
thinking, images — carry no operating signal: drop them.

---

## Claude Code
- **sessions glob:** `~/.claude/projects/<project-slug>/<session-uuid>.jsonl`
- **role field:** `.type` (a turn when it is `"user"` or `"assistant"`)
- **content field:** `.message.content`
- **skip a line if:** `.isMeta` is true or `.isSidechain` is true (sub-agent / injected plumbing)
- **handy metadata on turn lines:** `.cwd`, `.gitBranch`, `.timestamp`

Sample user line (newlines added for readability — real lines are single-line):
```json
{"type":"user","isMeta":false,"isSidechain":false,
 "cwd":"/Users/you/projects/api","gitBranch":"feat/login","timestamp":"2026-05-01T10:00:00Z",
 "message":{"role":"user","content":"refactor the auth middleware to use the new token format"}}
```
Sample assistant line with blocks — keep the `text` block, drop the `tool_use` block:
```json
{"type":"assistant","timestamp":"2026-05-01T10:00:05Z",
 "message":{"role":"assistant","content":[
   {"type":"text","text":"I'll update the middleware, then run the auth tests before touching anything else."},
   {"type":"tool_use","name":"Edit","input":{"file_path":"src/auth.ts"}}]}}
```
→ Parsed: `user: "refactor the auth middleware…"` then
`assistant: "I'll update the middleware, then run the auth tests…"`.

## codex
- **sessions glob:** `~/.codex/sessions/<YYYY>/<MM>/<DD>/rollout-*.jsonl`
- **role field:** `.payload.role` (a turn when it is `"user"` or `"assistant"`)
- **content field:** `.payload.content`
- **skip a line if:** it has no `.payload.role` (most lines — reasoning, events, meta)

Sample (codex wraps the message in `.payload`; text blocks are `input_text` / `output_text`):
```json
{"timestamp":"2026-05-02T14:20:00Z",
 "payload":{"role":"user","content":[{"type":"input_text","text":"run the test suite and fix the failures, then summarize what broke"}]}}
```
A non-message line you will see often and must skip (no `payload.role`):
```json
{"payload":{"type":"reasoning","content":[{"type":"text","text":"The user wants…"}]}}
```

## hermes (or any personal agent)
Personal agents store data in the OS app-data dir, which differs by platform. Glob the app
root for your OS, then `sessions/*.jsonl` under it.
- **app root — macOS:** `~/Library/Application Support/hermes/` (also try `~/.hermes/`)
- **app root — Linux:** `~/.local/share/hermes/` or `~/.config/hermes/` (also try `~/.hermes/`)
- **app root — Windows:** `~/AppData/Local/hermes/` (`%LOCALAPPDATA%/hermes`)
- **sessions glob:** `<app-root>/sessions/*.jsonl`
- **role field:** `.role` · **content field:** `.content` (both top-level)

Sample:
```json
{"role":"user","content":"summarize today's PRs and flag anything risky before I merge","timestamp":"2026-05-03T09:00:00Z"}
```

## Bring your own harness (HITL)
If the user runs a harness not listed here (Cursor, Windsurf, Aider, Copilot, PI, …), you only
need the same three things to read it — ask for them, then treat it identically:
1. the **sessions glob** (where its JSONL/transcripts live),
2. the **role field** (where each line says who spoke — e.g. `role`, `type`, `payload.role`), and
3. the **content field** (where the message text lives — e.g. `content`, `message.content`).
Most coding-agent harnesses are line-delimited JSON with a role + content shape; once you know
those fields you can read it with no new code.

---

## Memory files (all harnesses)
Beyond transcripts, harnesses store the user's **own saved instructions and memories**. These
are strong candidates for the operating model — the user authored or confirmed them — but are
**never copied verbatim**; run them through the same climb/gate as a transcript (see
`distillation.md` → "Memory-sourced material"). Read these if present:
- **Claude Code:** `~/.claude/CLAUDE.md` (global instructions) ·
  `~/.claude/projects/<slug>/memory/*.md` and that folder's `MEMORY.md` index (auto-memory)
- **codex:** `~/.codex/AGENTS.md` (global) · any `~/.codex/**/AGENTS.md` · `~/.codex/**/memories/*`
- **hermes / personal agent:** `<app-root>/**/MEMORY.md` · `<app-root>/**/USER.md`

A fact that appears in BOTH memory and lived transcripts is the strongest signal there is:
authored intent confirmed by behavior. Rank it highest.

---

## What to ignore + never emit
**Ignore this noise** on a **user** turn — it is injected by the harness, not written by the
user. Strip these wrapper blocks and everything inside them:
- `<system-reminder>…</system-reminder>`
- `<command-message>…</command-message>`, `<command-name>…</command-name>`, `<command-args>…</command-args>`
- `<local-command-…>…</local-command-…>`
- `<environment_context>…</environment_context>` (codex) · `<user_instructions>…</user_instructions>` (codex)

**Never emit a secret.** If a value looks like a credential, treat it as `[REDACTED]` — never
copy it into a fact's evidence or example, and **drop any fact whose evidence would contain
one.** Shapes to catch:
- `sk-…`, `ghp_…`, `AKIA…` (OpenAI / GitHub / AWS keys)
- `api_key=…`, `secret=…`, `token=…`, `bearer …`, `access=…` (the word, then a value)
- JWTs: `eyJ….….…` (three dot-separated base64url segments)

---

## The substance gate
Keep a session only if BOTH hold:
1. **More than 10 user+assistant messages.** Short one-shots carry no operating signal.
2. **Not an eval / benchmark / automation run.** If the user turns are the same prompt repeated
   (≈4+ identical, or under half of them unique), it is a loop with no preference signal — skip
   the whole session.

You do not need to fully read every file to apply gate #1. **Triage cheaply first** with a line
count (a JSONL line ≈ one event, so it is a generous upper bound on messages — enough to discard
the obviously-tiny files), then confirm the real message count and the eval check while reading
the survivors during distillation.

## Triage one-liner
Run the one for your shell to list every candidate session with its line count, biggest first.
Take the files comfortably above ~12 lines as your worklist.

```bash
# macOS / Linux (bash / zsh). nullglob so missing harnesses expand to nothing.
shopt -s nullglob 2>/dev/null || setopt NULL_GLOB 2>/dev/null
for f in ~/.claude/projects/*/*.jsonl \
         ~/.codex/sessions/*/*/*/rollout-*.jsonl \
         ~/Library/Application\ Support/hermes/sessions/*.jsonl \
         ~/.local/share/hermes/sessions/*.jsonl \
         ~/.hermes/sessions/*.jsonl; do
  [ -f "$f" ] && printf '%6s  %s\n' "$(wc -l < "$f")" "$f"
done | sort -rn
```

```powershell
# Windows (PowerShell)
$globs = @(
  "$HOME\.claude\projects\*\*.jsonl",
  "$HOME\.codex\sessions\*\*\*\rollout-*.jsonl",
  "$HOME\AppData\Local\hermes\sessions\*.jsonl"
)
Get-ChildItem $globs -ErrorAction SilentlyContinue |
  ForEach-Object { [pscustomobject]@{ Lines = (Get-Content $_.FullName | Measure-Object -Line).Lines; Path = $_.FullName } } |
  Sort-Object Lines -Descending | Format-Table -AutoSize
```
