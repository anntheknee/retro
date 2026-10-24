---
name: retro
model: opus
description: Reviews the last 30 days of Claude Code Sessions and writes a Findings file with fixes. Use when the user types /retro or /retro redo.
disable-model-invocation: true
allowed-tools: Bash(${CLAUDE_SKILL_DIR}/retro.py *)
---

# Retro

The user never runs subcommands. `prepare` has already run (with `redo` if the user typed `/retro redo`). Its output:

!`${CLAUDE_SKILL_DIR}/retro.py prepare $ARGUMENTS`

Copy this checklist and tick each item as you finish it:

- [ ] Repeat the user-facing lines
- [ ] Start Agents A, B and C
- [ ] Main Findings, Follow-through and Toolkit updates, while the agents run
- [ ] Wait, then merge
- [ ] `/insights` review
- [ ] Web solutions
- [ ] Number everything, once
- [ ] Failed parts
- [ ] `commit`
- [ ] Tell the user the path
- [ ] Statusline

## Repeat the user-facing lines

Repeat the output's user-facing lines (the Opus refusal, the days-left refusal, or the plan-usage and format-drift lines) in your first message. If it printed the Opus refusal, stop there. If it printed days left, stop there, except for Statusline.

Otherwise it printed a temp folder holding `metrics.json`, `digest.json`, `agent_a.json`, `agent_b.json` (each replaced by numbered pieces when split: see `briefs/splitting.md`), `agent_c.json`, a brief per agent input (`brief_a.md`, `brief_b.md`, `brief_c.md`, or `brief_a_1.md`, … per piece) and `brief_web.md`, `previous.json`, `upstream.json`, `news_raw.json`, `rubric_main.md`, `docs.txt` and `draft.md`, and `/insights` is already running in the background.

## Start Agents A, B and C

Spawn three subagents with `subagent_type: retro-worker` and `model: opus` in one message: Agent A (prompting quality (1) and rework (6)), Agent B (repeats (4) and workflows (8)) and Agent C (unused skills (3) and Overlap (9)). Each one's whole prompt is `Read <temp folder>/brief_<x>.md and follow it.` The brief holds its instructions, its rubric items, the Follow-through rules and the Finding layout; don't add to it. Each returns verdict rows, then Findings with no numbers and origin `via Retro`, in categories `prompting`/`rework`, `repeats`/`workflows` and `skills`/`overlap`. C's input is never split.

If `prepare` printed "input split into N pieces", read `briefs/splitting.md` before you spawn. If an agent fails or hits a usage limit, read `briefs/failures.md`.

## Main Findings, Follow-through and Toolkit updates

While the agents run, read `metrics.json`, `rubric_main.md` (your rubric rows) and this skill's `briefs/fixes.md` (where each fix goes), and write Findings for context (2), cost (5) and permissions (7), using this layout. The script flags candidates and writes no Finding; you judge each one. Skip a category with nothing worth saying.

```
### <n>. <category> · <project or "all"> · via Retro
**Problem**: <one or two lines, with the numbers>
**Solutions**:
- **a.** <the exact change: file and edit, or command>. Fit: <…>. Adoption: <…>.
```

Up to three self-contained solutions each. Findings are numbered once, in the numbering step. No evidence lines, no status. For context, read each `instruction_files` entry with `over_limit` or growth, and propose moving the lines `fixes.md` places elsewhere and cutting its no-ops. Such a Finding may suggest `/doctor prompt-audit` (suggest it; don't run it). A permissions solution may point to the built-in `fewer-permission-prompts` skill. Deliberate denials (for example `railway`) stay denied. A `secrets_in_prompts` Finding names only the Session and turn; never copy the secret into any output. `docs.txt` in the temp folder is the current Claude Code docs: the full text of every page, each starting `# <title>` then `Source: <url>`. Grep it; never read it whole. Before you name a command, setting, flag, hook event or feature in a solution, confirm it there and put its Source URL at the end of the solution's Adoption note. If the file is missing, go on without it.

**Follow-through**: `prepare` puts last Retro's Findings into the inputs (`previous_findings` in `agent_a/b/c.json` for each agent's own categories; `previous.json` holds the rest under `main`, plus `toolkit_updates` and `meta` text). `previous.json` is `null` when there was no previous Retro: write "No previous Retro." under `## Follow-through` and skip this. The briefs tell A, B and C to judge the `previous_findings` in their input and return the verdict rows first, then their Findings. Do the same yourself for `main`, `toolkit_updates` and `meta`. Each gets a verdict: worked, didn't work, not adopted, or no longer relevant. Judge from what changed (settings, installs, usage in the Window, whether the problem came back), and mark nothing in the old file. A not-adopted Finding comes back as a new Finding only if the problem got worse. An Overlap that still exists comes back every Retro, labelled "raised before". After a merge or removal that was applied, check the replacement got used. Agents return their verdicts as table rows `| <short summary of the fix> | <verdict> | <origin: Retro, /insights or web> |`, ahead of their Findings. Put all rows under `## Follow-through` in `draft.md` with the header `| Last month's fix | Verdict | Origin |`.

**Toolkit updates**: write `## Toolkit updates` in `draft.md` as `briefs/toolkit.md` says.

## Wait, then merge

Wait for all three results. Merge A's, B's and C's Findings with yours under `## Findings` in `draft.md`: drop duplicates (same problem and fix; keep the better one).

## `/insights` review

Run `${CLAUDE_SKILL_DIR}/retro.py insights <temp folder>` (it waits up to 5 minutes, so give the Bash call `timeout: 330000`) and read the `insights.json` it prints. If it holds `error`, list `/insights` under `## Failed parts` with the error and say it wasn't re-run; leave the review section with "`/insights` failed." and go on. Otherwise `sections` holds the text of `section-friction`, `section-features`, `section-patterns` and `section-horizon`; ignore everything else in the report. Give each item (a friction category, a suggested CLAUDE.md line, feature or pattern, horizon idea) exactly one verdict against your merged Findings and the Window: **confirm** or **amend** (it holds, or holds with a changed fix) becomes a Finding in the usual layout, tagged `via /insights`; **merge** joins it to an existing Finding (add its fix as a solution, or note it agrees; no new Finding); **drop** (already handled, stale, contradicted by the transcripts, or not worth it) is listed once with its reason. A stale item is dropped. A suggested CLAUDE.md line that `fixes.md` places elsewhere is amended to go there. Under ``## `/insights` review`` write the date range from `date_range`, the counts as `Confirmed: n · Merged: n · Amended: n · Dropped: n`, then each dropped item as a bullet with its reason.

## Web solutions

Build the problem list: the roughly five most frequent problems among the Findings (by the counts in their Problem lines), each searched even when the Toolkit already has a fix. Run `${CLAUDE_SKILL_DIR}/retro.py news <temp folder> <category>...` first, naming the categories of those problems (prompting, context, skills, repeats, cost, rework, permissions, workflows, overlap); (if it fails, list it under `## Failed parts` and go on without news) it scores `news_raw.json` and writes `news.json`: `items` (official ones plus the best 40 others, each with source, title, url, date, body), `html_sources` and `errors`. List each of `news_raw.json`'s `errors` (a feed that was down) under `## Failed parts`, not re-run. Spawn one subagent with `subagent_type: retro-worker` and `model: sonnet` whose prompt is `Read <temp folder>/brief_web.md and follow it.`, then the list, one line per problem (the Finding's category, its project and its Problem text), then one line naming the tools the user works with in the Window. The brief covers `news.json`, the outdated items in `upstream.json`, the search rules and the return format. It returns per-problem solutions, Meta items (`### <n>. <title>`, **What changed**, **Solutions**, source URL last) and **What changed** items for used outdated Toolkit items. Write the Meta items and changelog items under `## Meta` and `## Toolkit updates`, kept short. Then add its per-problem solutions yourself as further lettered solutions under the matching Finding, with fit and adoption notes, at most 3 solutions in all per Finding: when over, drop the weakest web solution first, never one that uses something already installed, then re-letter a, b, c. Put the source URL at the end of the solution's Adoption note. If the agent fails, handle it as `briefs/failures.md` says.

## Number everything, once

Order the Findings by weight across categories, then number them from 1. Number the Toolkit updates and Meta items after them, in the same sequence.

## Failed parts

Write `## Failed parts` last, just before `commit`, so it holds everything from the earlier steps. Its format and the re-run rules are in `briefs/failures.md`. A failure never stops the Retro: still run `commit`, except as `failures.md` says.

## Commit

Run `${CLAUDE_SKILL_DIR}/retro.py commit <temp folder>/draft.md`. Do not write frontmatter yourself; `commit` sets the Findings count. Then tell the user the findings file path it printed.

## Statusline

If `prepare` printed a statusline hint (on a refusal too), last of all offer the edit, and make it only after a yes (a decline isn't stored). The statusline runs outside this skill, so these use the absolute path:
- statusLine names a script: append `~/.claude/skills/retro/retro.py status`, joined to the existing output with ` · `;
- statusLine is an inline command: append `; ~/.claude/skills/retro/retro.py status`;
- no statusLine: set it to `~/.claude/skills/retro/retro.py status`.
