# Transcript signal catalog

Research for [issue 01](../wayfinder-issues/01-transcript-signal-catalog.md). Profiled 2026-10-20, read-only, with stdlib Python.

## Sources

- **[L] Local profile.** 170 JSONL files under `~/.claude/projects` (136 main Sessions + 34 subagent transcripts), 290 MB, timestamps 2026-09-20 to 2026-10-20, Claude Code versions 2.1.278 to 2.1.304. Also `~/.claude/history.jsonl` (1,485 lines). Every count below without another citation comes from this profile.
- **[S]** Claude Code docs, *Manage sessions*: <https://code.claude.com/docs/en/sessions.md> ("Where transcripts are stored", "Access conversations from scripts").
- **[D]** Claude Code docs, *Explore the .claude directory*: <https://code.claude.com/docs/en/claude-directory.md> ("Application data", "Cleaned up automatically").
- **[H]** Claude Code docs, *Hooks*: <https://code.claude.com/docs/en/hooks> (`transcript_path` in "Common input fields").
- **[C]** Claude Code changelog: <https://code.claude.com/docs/en/changelog.md> (generated from `anthropics/claude-code/CHANGELOG.md`).
- **[K]** Claude Code docs, *Costs*: <https://code.claude.com/docs/en/costs.md> ("Analyze your usage patterns").

## Record inventory (what exists)

Top-level `type` counts [L]: assistant 9,346 · attachment 8,828 · user 6,070 · api-request-blob 3,046 · mode 2,399 · atis-latch 2,391 · last-prompt 2,350 · api-request 1,770 · ai-title 1,702 · system 1,352 · file-history-snapshot 986 · bridge-session 582 · permission-mode 519 · queue-operation 348 · file-history-delta 170 · cost-state 154 · api-request-shape 75 · agent-color, pr-link, custom-title, artifact-* (< 15 each).

`system.subtype` [L]: turn_duration 855 · local_command 236 · away_summary 229 · informational 21 · compact_boundary 7 · bridge_status 3 · agents_killed 1.

`attachment.attachment.type` [L], top: total_tokens_reminder 4,037 · deferred_tools_record 1,760 · prompt_snapshot 329 · environment 263 · command_permissions 210 · date 189 · model 172 · skill_listing 170 · hook_success 135 · queued_command 54 · edited_text_file 53 · skill_mention 14 · invoked_skills 5 · thinking_drop 5 · dynamic_skill 2 (33 kinds in total).

Where the bytes go (of 290 MB) [L]: `user` records 144 MB, of which `tool_result` blocks are 66 MB · `api-request` + `api-request-blob` + `api-request-shape` 64 MB · `prompt_snapshot` attachments 18.7 MB · assistant `thinking` 13.9 MB · `skill_listing` 8.0 MB · assistant `tool_use` 3.8 MB · typed user text only 1.5 MB · assistant text 1.4 MB.

### Parsing traps (each one skews numbers if missed)

1. **Usage repeats per content block.** One API response is written as several `assistant` lines (one per content block, `apiBlockIndex`). 9,498 assistant lines carry only 4,347 distinct `requestId`s. 5,122 repeats have identical `usage`; 33 differ only in `output_tokens` (streaming). Dedupe by `requestId` and keep the last line, or tokens are overcounted about 2x [L].
2. **Not every `user` record is a typed prompt.** Tool results (`toolUseResult`, `tool_result` blocks), `isMeta`, `isCompactSummary`, slash-command echoes (`<command-name>…</command-name>`), interrupt markers (`[Request interrupted by user…]`), and non-human origins (`origin.kind`: task-notification, peer, coordinator, auto-continuation) all use `type: "user"`. Of 6,070 user records, about 690 are real typed prompts [L]. `promptSource` (typed/queued/system) and `origin.kind == "human"` exist only on newer records (714 and 825 records), so the filter must also work without them.
3. **`total_tokens_reminder` is not context fill.** Its text is a budget countdown (`<total_tokens>15000000 tokens left</total_tokens>`), constant in 655 records. Use `usage` for context size [L].
4. **`cost-state` can appear up to 3 times per file** (134 files have it). Treat it as cumulative within a process and take the maximum. Whether a resumed process resets it is unverified [L].
5. **Subagents are separate files** at `<session>/subagents/*.jsonl` with a sibling `*.meta.json` (`agentType`, `description`, `name`, `spawnDepth`, `requestShape`). Records inside carry `agentId` and `isSidechain` [L][D].
6. **`history.jsonl` is not swept** by `cleanupPeriodDays` unless the HIPAA configuration applies [D]. Locally it reaches back to 2026-03-09, roughly 7 months against 1 month of transcripts. Fields: `display`, `pastedContents`, `timestamp` (epoch ms), `project`, `sessionId` [L].

## Signal map for the 9 problem categories

**Det** = a script can compute it exactly. **LLM** = needs judgment over text. **Det→LLM** = a script mines candidates and an LLM decides.

| # | Category | Evidencing records / fields | Mode | What the script can emit |
|---|---|---|---|---|
| 1 | Prompting quality | Typed prompts (`user`, human origin): length, `imagePasteIds`, `history.jsonl` `pastedContents`. Follow-ups: `AskUserQuestion` tool_use right after a prompt, interrupt markers, quick re-prompts. `system/turn_duration.durationMs` per turn. | LLM (Det features) | Length distribution (median 71 chars, p10 13, p90 383; 228 of 696 under 40 chars [L]), per-turn tool count and duration, clarification and interrupt flags. Whether a prompt was underspecified needs judgment. |
| 2 | Context management | `system/compact_boundary.compactMetadata` (`trigger` manual/auto, `preTokens`, `postTokens`, `cumulativeDroppedTokens`). `/clear`, `/compact`, `/context` in slash echoes and `system/local_command.commandRun`. `system/informational` ("Compacted while idle…"). Per-request context = `usage.input_tokens + cache_read_input_tokens + cache_creation_input_tokens`. `attachment/thinking_drop`. Turns per Session. | Det (LLM for "should have cleared here") | Peak and mean context per Session, compactions with pre/post size, clears per Session (84 `/clear` [L]), long single-topic Sessions. Spotting a topic switch without `/clear` needs an LLM over the prompt list. |
| 3 | Skills you have but didn't use | Available: `attachment/skill_listing` (`names`, `skillCount`, `isInitial`, description text in `content`), `dynamic_skill`, `agent_listing_delta`, `deferred_tools_record`. Used: `Skill` tool_use `input.skill`, slash echoes, `attachment/skill_mention`, `invoked_skills`, `assistant.attributionSkill` / `attributionPlugin`. | Det→LLM | Never-invoked skills over the Window (68 distinct skill names listed across 13 distinct listings; 23 invoked via the `Skill` tool [L]). Matching a prompt to a skill that should have fired needs an LLM with the skill descriptions. |
| 4 | Asking the same thing repeatedly | Typed prompts across Sessions, plus `history.jsonl` (7 months, includes prompts from Sessions already swept). `ai-title.aiTitle` per Session. | Det→LLM | Exact or normalized repeats are cheap: 14 repeated prompts of 20+ chars, 41 occurrences, in history [L]. Paraphrased repeats need an LLM or embeddings over the prompt list. |
| 5 | Cost / token hotspots | `assistant.message.usage` (input, cache read, cache write split into `cache_creation.ephemeral_5m/1h`, output, `output_tokens_details.thinking_tokens`, `server_tool_use.web_search/web_fetch_requests`), `message.model`, `effort`, `attributionSkill/Plugin/McpServer/McpTool/Agent`. `cost-state.totalCostUSD` and `modelUsage[model].costUSD`. Fixed overhead: sizes of `prompt_snapshot`, `skill_listing`, `deferred_tools_record`, `hook_success` content. | Det | Per Session / project / model / skill / effort token and USD totals, cache hit ratio, cache-write-heavy turns (model or effort switches), expensive subagents, fixed per-Session overhead. Fully mechanical. |
| 6 | Corrections and rework | Interrupt markers (`[Request interrupted by user]` 9, `…for tool use]` 4), `interruptedMessageId`, `isAbortedMidStream`. `queue-operation` `remove/absorbed_mid_turn` (54: prompts typed mid-turn). Repeated `Edit`/`Write` on the same `file_path`. `/rewind`. `edited_text_file` (user edited a file Claude touched). Tool errors: `tool_result.is_error`. | Det→LLM | Interrupts, mid-turn steering, same-file edit churn, error→retry loops. A correction lexicon ("no", "actually", "revert"…) hits only 11 of 690 prompts [L], so most corrections are not lexical and need an LLM reading the prompt plus a short tail of the previous assistant text. |
| 7 | Permission-prompt friction | `user.permissionDecision` {`decision` accept/reject, `source` config / user_temporary / user_abort, `reasonType` classifier / mode / safetyCheck / subcommandResults / other}. `user.toolDenialKind` (automode-unavailable 20, automode-blocked 20, user-rejected 6, permission-rule 2). `permission-mode` records (auto 504, plan 8, default 5, acceptEdits 2). `attachment/command_permissions.allowedTools`. | Det | Prompts the user had to answer (`source` user_*), rejections by tool and command head, classifier no-verdicts. Proposing allow rules can reuse the built-in `fewer-permission-prompts` skill. This user runs auto mode almost always, so the volume is small [L]. |
| 8 | Repeated manual workflows → skill | `Bash` tool_use `input.command` (3,538 calls [L]), tool-name sequences per turn, slash commands typed (`history.jsonl`: 398 slash prompts, 60 distinct [L]), similar opening prompts across Sessions. | Det→LLM | N-gram mining of command heads and tool sequences that recur across 3+ Sessions, plus recurring prompt templates. Whether a pattern deserves a skill, and what it should do, needs an LLM. |
| 9 | Toolkit overlap | `skill_listing` names + descriptions (from `content`), `agent_listing_delta`, `deferred_tools_record` (MCP tools), `attributionPlugin`. Usage gaps: a skill present in older listings and gone from newer ones, compared with usage before and after (`Skill` input, slash echoes). | Det→LLM | Listing diffs over time and per-skill usage counts are deterministic. Duplicate detection (e.g. grill-me / grilling / grill-with-docs) and merge proposals need an LLM over descriptions and, ideally, the SKILL.md files on disk. |

Cross-cutting fields for tagging Findings: `cwd` (project), `gitBranch`, `sessionId`, `timestamp`, `version`, `ai-title.aiTitle`, `pr-link` [L].

Prior art to note: the built-in `/insights` command already reports "friction points such as misunderstood requests or buggy code, and suggestions" over up to 200 unseen Sessions and writes `~/.claude/usage-data/report.html` [K]. It overlaps categories 1 and 6. It is worth a look before building those parts.

## Format stability

- **Officially undocumented and unstable.** "The entry format is internal to Claude Code and changes between versions, so scripts that parse these files directly can break on any release. To build on session data, use `/export` or the script interfaces instead." [S] The hooks reference calls the file "conversation JSON" and gives no schema [H].
- **Documented parts:** location `~/.claude/projects/<project>/<session-id>.jsonl` (non-alphanumerics in the cwd become `-`, truncated to 200 chars plus a hash) [S], `subagents/` subfolder [D], 30-day default retention via `cleanupPeriodDays` [D], and `history.jsonl` purpose and fields at a high level [D].
- **Release cadence:** 32 releases between 2.1.270 (2026-09-12) and 2.1.304 (2026-10-19), roughly one a day [C]. The local month spans 18 versions; only 4 of 170 files mix versions [L].
- **Drift actually observed within one month [L], with changelog matches:**
  - `api-request`, `api-request-blob`, `api-request-shape` appeared at 2.1.300, now 22% of bytes. Changelog 2.1.300: "Changed local session transcripts to also record each API request's system prompt, tools and parameters" [C].
  - `user.permissionDecision` first seen at 2.1.293, `toolDenialKind` at 2.1.282, `attributionPlugin` at 2.1.291, `attributionMcpServer/McpTool` at 2.1.289, `requestedModel` and `thinkingDisplay` at 2.1.296, `isAbortedMidStream` at 2.1.303. Before those versions, the same facts are absent rather than renamed.
  - Changelog 2.1.304: "the safety classifier's context is no longer stored with every request" [C]. 2.1.299: PDF bytes no longer kept in the transcript [C].
  - Changelog 2.1.275 through 2.1.285 fix crashes on transcripts holding "malformed" entries (compaction markers, message blocks, attachments) [C]. Even Claude Code's own reader meets shapes it did not expect.
- **Stable core (present in every version seen):** `type`, `uuid`, `parentUuid`, `timestamp`, `sessionId`, `cwd`, `gitBranch`, `version`, `isSidechain`; `message.role/content/model/usage` with Anthropic Messages API block types (`text`, `thinking`, `tool_use`, `tool_result`); `system.subtype` turn_duration / local_command / compact_boundary; `attachment.type` skill_listing; `ai-title`; `cost-state` [L]. These mirror the public Messages API shape, so they are the safest base.
- **Implication for the script:** parse defensively. Use `.get()` everywhere, ignore unknown `type`s, record `version` in each digest, and count unparsed or unknown records so a Retro can report "format drift: N records skipped". Never use a transcript field as the only source for a Finding without a fallback. Keep one test fixture per breaking version seen.

## Proposed per-Session digest

The script writes one JSON object per Session (subagent transcripts get their own objects, linked by path). Prompts are truncated, everything else is counts.

```jsonc
{
  "file": "<cwd-slug>/<session>.jsonl",       // or .../subagents/agent-x.jsonl
  "agentId": null, "agent": {"type": "general-purpose", "description": "..."}, // from .meta.json
  "cwd": "/Users/.../repo", "gitBranch": "main", "title": "<ai-title>",
  "start": "ISO", "end": "ISO", "versions": ["2.1.302"],
  "models": {"claude-opus-5-5": 41}, "effort": {"high": 30},
  "perm_modes": {"auto": 3},
  "requests": 41,                               // distinct requestIds
  "tokens": {"in":0,"cache_read":0,"cache_write":0,"out":0,"thinking":0},
  "cost_usd": 0.44, "peak_ctx": 118000,
  "compactions": [{"trigger":"manual","preTokens":57690,"postTokens":6077}],
  "slash": {"clear": 2, "wayfinder": 1},
  "skills_invoked": {"grilling": 1}, "attrib_skill_out": {"grilling": 5400},
  "tools": {"Bash": 40, "Read": 12}, "bash_heads": {"git status": 5, "python3": 4},
  "tool_errors": [["Exit code 1\nTraceback…", 2]],   // first 80 chars, counted
  "denials": {"automode-blocked": 1, "pd:accept/user_temporary": 1},
  "interrupts": 1, "api_errors": 0, "informational": ["Usage limit reached…"],
  "turns": [{"ts":"ISO","len":412,"prompt":"<first 300 chars>","tools":{"Edit":3},"ms":84000,"interrupted":false}]
}
```

Window-level, outside the per-Session objects: the union of skill listings with each skill's first and last Session (the listing is 42% of digest bytes when repeated per Session, and there are only 13 distinct listings), plus counts of unknown or skipped records.

**Measured on the real data** [L], prototype at [`01-digest-prototype.py`](01-digest-prototype.py) (throwaway; omits the `.meta.json` join and the Window-level hoist, which was measured separately):

| Variant | Bytes | vs 290 MB raw |
|---|---|---|
| Digest, prompts capped at 300 chars, listing per Session | 477 KB | 0.16% (about 600x smaller) |
| Same, listing hoisted to Window level | 298 KB | 0.10% (about 970x) |
| Stats only, no prompt text | 163 KB | 0.06% |
| Prompts uncapped, listing per Session | 556 KB | 0.19% |

The 298 KB variant is about 75k tokens for a month at roughly 4 bytes per token, which a few subagents can split by project. Prompts make up about 134 KB of it. Category 6 needs a short tail of the preceding assistant text per turn. At 200 chars × 690 turns, that adds an estimated 140 KB, so add it only to the subset of turns the script flags (interrupts, edit churn, error loops).

Dropped entirely: `tool_result` bodies, `thinking`, `api-request*`, `prompt_snapshot`, `deferred_tools_record`, `file-history-*`, `mode`, `atis-latch`, `bridge-session`, `last-prompt`. The largest of these (tool results 66 MB, API-request records 64 MB, prompt snapshots 19 MB, thinking 14 MB) carry no signal for the 9 categories beyond what the counts, error snippets, and `usage` already capture. The rest of the raw size is per-record envelope fields repeated on every line, and the `toolUseResult` field, a structured second copy of each tool result (71 MB) [L].
