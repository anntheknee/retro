# Testing the skill

Type: grilling
Status: resolved
Assignee: me
Blocked by:

## Question

How is `/retro` tested? Two layers, per [Script vs. skill boundary and subagent fan-out](07-script-vs-skill-boundary-and-fan-out.md): `retro.py` (`prepare` / `context` / `commit`, Python 3 stdlib) and the `SKILL.md` steps Claude follows (subagents, merge, `/insights` review, web agent).

- **Script**: tests against a fixture `~/.claude` tree (transcripts, `subagents/`, `history.jsonl`, `~/.claude.json`, skill and plugin lock files). Is the fixture hand-written, or trimmed and scrubbed from real transcripts? Per [Transcript signal catalog](01-transcript-signal-catalog.md), the format changes between versions, so how is tolerant parsing covered?
- **No force option** ([Retro state and lifecycle](06-retro-state-and-lifecycle.md)): how do tests get past the 30-day gate and the Window? Options: an overridable state directory, "now", and home directory (environment variables or flags) that only tests use, without opening a force path for real runs.
- **Skill**: evals (fixed inputs, judged outputs) vs. replaying a recorded Window end to end vs. a manual dry run on real data. What counts as passing, given that Findings are LLM judgment?
- **Side effects in tests**: `prepare` runs `claude -p "/insights"` and `/usage`, and fetches feeds. `commit` runs `open`. Which of these get stubbed?

Note from [Retro due reminder](13-retro-due-reminder.md): `retro.py` gains a fourth subcommand, `status` (statusline segment from the Retro Timestamp: nothing, `retro due`, or `retro overdue · Nd lost`), and `prepare` now reads `~/.claude/settings.json` `statusLine` (and the script it names) to detect a missing `retro.py status` call. Both need the overridable home and "now".

Note from [Watch list](14-watch-list.md): `prepare` shells out to `brew leaves --installed-on-request`, `npm ls -g --depth=0`, `brew outdated --json=v2`, `npm outdated -g --json`, and resolves Bash command names with `which` + `realpath` into Cellar or npm-global paths. The fixture needs those outputs and paths faked too.

## Answer

- **No automated tests.** No `test_retro.py`, fixture tree, stubbed `sh()`/`fetch()` seams, or injected home and "now". Acceptance is the user running a real Retro, judging it, and telling Claude what to change in `SKILL.md` or `retro.py`. The only guard is the "format drift: N records skipped" line `prepare` already prints ([Transcript signal catalog](01-transcript-signal-catalog.md)).
- **Redo** (see `CONTEXT.md`): `/retro redo` runs `retro.py prepare --redo`, which skips the 30-day gate and replaces the latest Retro. The Window is the last 30 days from now, the result overwrites `findings.md`, and the Retro Timestamp moves to when the redo started (so the gate restarts from the redo). Before any Retro has been committed, a redo is just the first Retro run early. Supersedes "no force option" in [Retro state and lifecycle](06-retro-state-and-lifecycle.md).
- **`findings.prev.md`**: a normal `commit` first renames the old `~/.claude/retro/findings.md` to `findings.prev.md`, then writes the new file. A redo reads `findings.prev.md` as its follow-through baseline and doesn't rotate the files, so regenerating never checks follow-through on Findings written minutes earlier, and never loses the previous Retro's Findings. Rejected: a plain `--force` that only skips the gate, which overwrites the real baseline and makes every Finding come back "not adopted".
- State is now the Retro Timestamp plus two Findings files (`findings.md`, `findings.prev.md`).
