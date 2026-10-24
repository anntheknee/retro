# Transcript signal catalog

Type: research
Status: resolved
Blocked by:

## Question

For each of the 9 problem categories on the map, which transcript records and fields show it (e.g. `usage`, `compact_boundary`, `total_tokens_reminder`, `local_command` for `/clear`, `attributionSkill`, `skill_listing`, tool_use/tool_result, interruptions, permission events)? Can a script detect it deterministically, or does it need LLM judgment? Also: how stable is this undocumented JSONL format across Claude Code versions, and what does a compact per-Session digest look like that keeps the evidence while cutting most of the bytes? (A month is ~268 MB raw.)

Sources: the local transcripts in `~/.claude/projects` (read-only), Claude Code docs and changelog.

## Answer

Every category has evidence in the transcripts. Cost (5), permission friction (7), and context management (2) are fully deterministic from `usage`, `permissionDecision`/`toolDenialKind`, `compact_boundary`, and `/clear` echoes. Unused skills (3), repeats (4), corrections (6), workflows (8), and overlap (9) work as script-mined candidates plus an LLM verdict. Prompting quality (1) is mostly LLM judgment. Correction words match only 11 of 690 prompts, so rework detection needs the LLM.
The format is officially internal and "changes between versions" (sessions docs). In one month, 18 versions added fields and new record types (`api-request*` at 2.1.300), so the parser has to be defensive.
Traps: usage repeats per content block (dedupe by `requestId`, about 2x overcount otherwise), and only about 11% of `user` records are typed prompts.
A per-Session digest (counts + 300-char prompts, skill listing hoisted to Window level) measures 298 KB against 290 MB raw (about 970x smaller, about 75k tokens per month).

[findings](../research/01-transcript-signal-catalog.md)
