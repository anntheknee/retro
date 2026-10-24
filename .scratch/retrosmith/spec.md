# Spec: `/retro` v1

Label: ready-for-agent
Source: [map](map.md) and its closed tickets in [wayfinder-issues/](wayfinder-issues/). Vocabulary: [CONTEXT.md](../../CONTEXT.md).

## Problem Statement

I use Claude Code every day across several projects, and I can't see how well I use it. My habits stay invisible to me. I write vague prompts and correct the same mistakes over and over. I let Sessions sprawl without `/clear` and answer the same permission prompts again and again. I ask questions I've asked before and type workflows by hand that should be skills. I also forget skills I already have.

My Toolkit keeps growing. Skills from several sources do the same job, and installed items fall behind upstream without my noticing. A plugin from a third-party marketplace can be a major version behind. Meanwhile Claude Code ships about one release a day, and new tools and practices appear that would fix problems I keep hitting. I have no regular moment where all of this gets weighed against what I actually did.

Built-in `/insights` covers part of the friction. It knows nothing about my Toolkit, doesn't scan the web, and doesn't check whether last month's advice worked. Transcripts expire after 30 days (`cleanupPeriodDays` is 30), so evidence I don't review in time is gone.

## Solution

`/retro` is a Claude Code skill plus a helper script. Once a month it runs a Retro over the Window, the last 30 days of Session activity across all projects. It:

- checks follow-through on the previous Retro's Findings, judged from what actually changed;
- analyzes nine problem categories from the transcripts;
- reviews `/insights` as a second opinion;
- inventories the Toolkit and compares it with upstream;
- scans the web for solutions to the top problems, for changelogs of Toolkit items I use, and for matched AI-tooling news;
- writes one markdown findings file and opens it.

Each Finding names a problem and up to three self-contained solutions. I apply one later by telling Claude ("apply 3b"). The script does all the counting at zero tokens, and Claude spends tokens only on judgment. A statusline segment tells me when a Retro is due and how many days I've lost by running late. `/retro redo` regenerates the latest Retro without losing its follow-through baseline.

## User Stories

### Running a Retro

1. As the user, I want to run a Retro by typing `/retro`, so that one command does the whole review.
2. As the user, I want a Retro to cover every project in one run, so that habits that cross projects show up.
3. As the user, I want a Retro to analyze exactly the 30 days before it starts, so that the Window matches transcript retention.
4. As the user, I want `/retro` to do nothing, at zero tokens, when fewer than 30 days have passed since the Retro Timestamp, so that I can't waste a run or analyze overlapping Windows.
5. As the user, I want the refusal to tell me how many days remain, so that I know when to come back.
6. As the user, I want my first Retro to run only once my oldest `history.jsonl` entry is at least 30 days old, so that the first Window is full.
7. As the user, I want the Retro's own Session to be left out of every Window from the `/retro` prompt onward, including its subagents and the headless `claude -p` runs it starts, so that the review never judges itself.
8. As the user, I want a Session that I resumed across a Retro to count only its activity inside each Window, so that no day is analyzed twice.
9. As the user, I want the Retro Timestamp to advance only when the Findings are written, so that an aborted Retro leaves the next run free to cover the same Window.
10. As the user, I want a Retro to run as long as it needs, so that the review is thorough rather than rushed.
11. As the user, I want a Retro to run on Opus, so that judgment quality matches `/insights`.
12. As the user, I want `/retro` to tell me my plan usage when it starts (session and weekly percent used, reset time), so that I can see whether I'm about to hit a limit. It never blocks the run.

### The nine problem categories

13. As the user, I want my prompting quality judged against a documented rubric (scoping, verification, `@` references, plan mode, golden rule, and so on), so that I learn which prompt habits cost me round-trips.
14. As the user, I want my context management measured: peak context, compactions, `/clear` use, kitchen-sink Sessions, and runs past two failed corrections. Then I can see where Sessions sprawl.
15. As the user, I want to learn which of my installed skills would have fit a task I did by hand, so that I use what I already have.
16. As the user, I want to see the questions I asked repeatedly, across Sessions and projects, so that I can put the answer in CLAUDE.md, docs, or memory.
17. As the user, I want cost and token hotspots by Session, project, model, skill, and effort, so that I know where usage goes.
18. As the user, I want corrections and rework surfaced (interrupts, mid-turn steering, edit churn on one file, error and retry loops, and non-lexical corrections), so that I can change how I steer Claude.
19. As the user, I want permission-prompt friction counted by tool and command, so that I can add allow rules or keep deliberate denials.
20. As the user, I want repeated manual workflows that recur across three or more Sessions proposed as skills (or hooks or subagents, depending on the trigger), so that I stop retyping playbooks.
21. As the user, I want Overlaps in my Toolkit found, even when only one member is used, so that I resolve them.
22. As the user, I want each Overlap to come with a verdict, pick-one or merge-and-own, and the reasoning, so that I can decide quickly.
23. As the user, I want slash names I typed in the Window that match no Toolkit item sorted into removed-skill habits, typos, and noise, so that I notice old habits after a removal or merge.
24. As the user, I want a plugin that only ships hooks reported as "hooks only, can't tell" rather than as unused, so that I don't remove something that's working.
25. As the user, I want Findings tagged by project where relevant, so that I know which repository a fix belongs to.

### Follow-through

26. As the user, I want every previous Finding judged as worked, didn't work, not adopted, or no longer relevant, from what actually changed (settings, installs, usage, whether the problem came back), so that I don't have to mark anything myself.
27. As the user, I want a Finding I didn't adopt to come back only if the problem got worse, so that I'm not nagged about advice I chose to skip.
28. As the user, I want an Overlap that still exists to come back every Retro labelled "raised before", so that I don't forget unresolved duplication.
29. As the user, I want follow-through to check that the replacement got used after a merge or removal I applied, so that I know the change stuck.
30. As the user, I want follow-through to show how each origin's advice fared (Retro, `/insights`, web), so that I learn which source to trust.

### `/insights` as a second opinion

31. As the user, I want every Retro to run `/insights` headlessly and review four of its report sections against its own Findings, so that I get a second opinion without running it myself.
32. As the user, I want each `/insights` item to get a verdict (confirm, merge, amend, or drop), so that its advice is checked rather than copied.
33. As the user, I want each dropped `/insights` item listed once with its reason, and the `/insights` date range recorded, so that I can see what was discarded and why.
34. As the user, I want surviving `/insights` items to become ordinary Findings tagged `via /insights`, so that one list holds all the advice.

### Toolkit and upstream

35. As the user, I want every Toolkit kind compared with upstream: skills, plugins and marketplaces, CLIs, and Claude Code itself. Then I learn what is behind without keeping any list.
36. As the user, I want changelogs of Toolkit items I used in the Window, and that are behind, read and judged against my problems, so that I learn which updates matter to me.
37. As the user, I want installed CLIs that are outdated but unused to get one zero-token version line, so that I see them without paying for analysis.
38. As the user, I want a CLI counted as used in the Window when any Bash command resolves to its Homebrew or npm-global package, so that the Retro knows which tools I rely on.
39. As the user, I want Claude Code releases since the previous Retro treated as the upstream of built-in commands, bundled skills, and agents, so that new built-ins reach me.
40. As the user, I want new plugins in the official marketplace since the previous Retro listed when they match my Toolkit or problems, so that I discover official tools.
41. As the user, I want the first Retro to raise a Finding to add `metadata.upstream` to hand-copied skills that have no machine-readable provenance, so that later Retros can track them.

### Owned Skills

42. As the user, I want a merge-and-own solution to carry the new name, what each original contributes, what's dropped, and which sources to track, so that a later Session can write the Owned Skill from it.
43. As the user, I want an edited install (such as `pocock-review`) treated as an Owned Skill with one tracked source, so that an upstream update can't silently overwrite my edit.
44. As the user, I want upstream changes to the parts an Owned Skill kept raised as "port this?" Findings, and changes to dropped parts skipped silently. That way I stay current without noise.
45. As the user, I want a Finding when an Owned Skill's upstream source is deleted, so that I know I'm the only maintainer now.
46. As the user, I want the Retro to never merge, uninstall, or run git on its own, so that nothing changes without me asking.

### Web scan

47. As the user, I want the roughly five most frequent problems searched on the web, even when the Toolkit already has a fix, so that I find better tools.
48. As the user, I want AI-tooling news from a fixed shortlist of feeds filtered by date and by Toolkit and problem keywords before the LLM sees it, so that only 20 to 40 relevant items cost tokens.
49. As the user, I want no web search without a problem or a Toolkit item behind it, so that the scan stays on target.
50. As the user, I want web solutions placed inline in the Finding for the problem they solve ("you keep hitting X; Y solves it"), so that I read problem and fix together.

### The findings file

51. As the user, I want one markdown file, opened automatically when the Retro finishes, so that I read the result in VS Code's rendered preview.
52. As the user, I want the sections in a fixed order: header line, Failed parts, Follow-through, Findings by weight, Toolkit updates, Meta, `/insights` review. Then every Retro reads the same way.
53. As the user, I want Findings ordered by weight across all categories, not grouped by category, so that the most important comes first.
54. As the user, I want each Finding numbered, with its category, project, and origin in the heading, so that I can say "apply 3b".
55. As the user, I want up to three lettered solutions per Finding, each with a fit note and an adoption note, so that I can choose.
56. As the user, I want every solution self-contained (the exact file and edit, or the command), so that a fresh Session can apply it without this Retro's context.
57. As the user, I want the file to have no evidence lines, no status, and no Toolkit inventory list, so that it stays short.
58. As the user, I want each failed part (an agent, `/insights`, a feed) listed with whether it was re-run, so that I know what the Retro couldn't see.

### Failures and limits

59. As the user, I want a Retro to continue past a failed agent, `/insights` run, or feed, so that one broken part doesn't cost me the month.
60. As the user, I want nothing committed if every phase-1 agent fails, so that an empty Retro never replaces a real one.
61. As the user, I want an agent that hit the usage limit re-run from its same input after I type "continue", without counting as a failure, so that a limit only delays the Retro.
62. As the user, I want to be offered one re-run, with approval, for an agent that crashed, timed out, or returned garbled output, so that I decide whether to spend more.
63. As the user, I want an oversized agent input split into pieces of whole Sessions and reconciled before the merge, so that volume growth doesn't break the Retro.
64. As the user, I want `/retro` to tell me how many transcript records it couldn't parse ("format drift: N records skipped"), so that I notice when a Claude Code release changes the transcript format.

### Reminder and Redo

65. As the user, I want a statusline segment that shows nothing before day 30, `retro due` on day 30, then `retro overdue · Nd lost` (orange for 1 to 6 days lost, red from 7), so that I run the Retro before transcripts expire.
66. As the user, I want the segment to show `retro due` before my first Retro, so that I'm prompted to start. The gate still refuses an early run.
67. As the user, I want every `/retro` run, above or below the gate, to check whether my statusline calls `retro.py status` and offer to add it, so that the reminder gets set up without an installer.
68. As the user, I want a declined statusline offer to come back next run, with nothing stored, so that state stays minimal.
69. As the user, I want `/retro redo` to skip the gate and replace the latest Retro, so that I can regenerate it after I change the skill.
70. As the user, I want a Redo to check follow-through against the Findings the replaced Retro checked, so that regenerating never judges Findings written minutes earlier.
71. As the user, I want a Redo to move the Retro Timestamp to when the Redo started, so that the gate restarts from it.
72. As the user, I want a Redo before any Retro exists to be simply a first Retro run early, so that I can try the skill right away.

### Applying Findings later

73. As a later Claude Session applying a Finding, I want each solution to name the exact change, so that I can carry it out without reading transcripts.
74. As a later Claude Session applying a merge-and-own Finding, I want the outline and the sources to track, so that I can write the Owned Skill with correct `metadata.upstream` and remove the originals through their own installers.
75. As a later Claude Session applying a "port this?" Finding, I want the tracked source and the `base` range, so that I can port the change and bump `base`.

## Implementation Decisions

### Form and install

- The skill is a folder holding `SKILL.md` (the steps Claude follows) and `retro.py` beside it. The source lives in this repo and is symlinked as the user's `retro` skill (`~/.claude/skills/retro`).
- `retro.py` is Python 3, stdlib only, with `#!/usr/bin/env python3` (Homebrew 3.13; `/usr/bin` has 3.9). Claude runs it with its Bash tool.
- The skill is self-contained. It uses the built-in WebSearch and WebFetch tools and subagents, needs no API key, and uses no external orchestrator.
- `retro.py` contains no installer code. Claude edits settings with its normal tools after the user agrees.
- The ponytail rule applies: the smallest thing that works.

### Script vs. Claude

- The script computes every number, mines every candidate, and flags rubric matches (for example, "3 Sessions ran past 2 failed corrections without `/clear`"). It writes no Finding.
- Claude writes every Finding, including those for the purely numeric categories 2, 5, and 7. All Findings go through one path for judging, deduping, and linking.
- Agents never read raw transcript `.jsonl`. Only the script copes with the unstable format.

### `retro.py` subcommands

| Subcommand | Does |
|---|---|
| `prepare [--redo]` | Checks the gate (skipped by `--redo`). Below the gate: prints progress and the statusline hint if needed, then stops. Otherwise: captures the Retro Timestamp; builds the digest, metrics, Toolkit table and inventory with upstream diffs; fetches and filters feeds; starts `/insights` in the background; prints the `/usage` line, the format-drift line and the statusline hint; writes each agent's input file into a fresh temp folder whose path it prints. |
| `context <session> <turn>` | Prints one turn in full: the typed prompt, the end of Claude's previous reply, and the turn's tools and errors. Agents use it when the digest isn't enough. |
| `commit <draft.md>` | For a normal Retro, renames the existing findings file to the previous-findings file, then writes the new findings file atomically with frontmatter. For a Redo, overwrites the findings file and leaves the previous-findings file alone. Deletes the temp folder, prints the path, and runs `open` on the file. |
| `status` | Prints the statusline segment or nothing. |

- The user never runs these subcommands. `/retro` has Claude run them, except `status`, which the statusline calls.
- Claude repeats `prepare`'s user-facing lines in its own first message: the gate refusal or progress, the `/usage` line, and the format-drift line. Bash output isn't reliably shown to the user.
- The frontmatter format and the 30-day constant live only in `retro.py`. The LLM never writes frontmatter.
- `commit` learns whether the run is a Redo, and which Retro Timestamp to write, from what `prepare` left in the temp folder.

### State

- The only state is in `~/.claude/retro/`:
  - `findings.md`: the latest Retro's Findings, with the Retro Timestamp in its frontmatter.
  - `findings.prev.md`: the Findings before them, kept so a Redo has a follow-through baseline.
- State lives outside the repo, per machine, the same as the transcripts. Transcripts are never deleted by Retrosmith.
- The temp folder from `prepare` survives until `commit` deletes it, so a usage-limit pause or a re-run can reuse the agent inputs.
- There is no history command. Older Findings are discarded.

### Gate, Window, and cursor

- Gate: 30 days since the Retro Timestamp. With no findings file, the first Retro runs once the oldest `history.jsonl` entry is 30 or more days old. Transcripts aren't used for this check, because cleanup deletes them around day 30. A Redo skips the gate.
- Window: the 30 days before `prepare` starts, filtered message by message. A late Retro leaves a gap that no Window covers, and no day is analyzed twice.
- `history.jsonl` is trimmed to the Window start.
- Own-Session exclusion is detected from the transcripts, with nothing stored. Any Session where `/retro` was typed is cut from that prompt onward, subagent transcripts included. Headless `-p` Sessions the Retro started (`/insights`, `/usage`) are skipped too.
- The cursor for feeds and upstream changelogs is the previous Retro's Timestamp. For a Redo it is the timestamp in `findings.prev.md`. For a first Retro, or a Redo with no previous file, it is 30 days back. (Derived: the tickets name the Retro Timestamp as the only cursor without spelling out the Redo case.)

### Transcript parsing and digest

- Data sources: `~/.claude/projects/<cwd-slug>/<session>.jsonl` plus `subagents/` (with sibling `.meta.json`), `~/.claude/history.jsonl`, and `skillUsage` in `~/.claude.json`.
- Parse defensively: `.get()` everywhere, ignore unknown `type`s, and record `version` per Session. Count unknown or skipped records and print "format drift: N records skipped". The format is officially internal and changed 18 times in one month.
- Count each API response once: keep the last line per `requestId`. Otherwise tokens are counted about twice.
- Typed prompts are a filtered subset of `user` records. The filter excludes tool results, `isMeta`, compact summaries, slash-command echoes, interrupt markers, and non-human origins, and it still works when `promptSource` and `origin.kind` are absent.
- The digest has one JSON object per Session (subagents get their own objects): metadata, models and effort, permission modes, deduped tokens, peak context, compactions, slash commands, skills invoked, tool counts, Bash command heads, truncated tool errors, denials, interrupts, and per-turn records with prompts capped at 300 characters.
- Skill listings are hoisted to Window level (the union, with each skill's first and last Session).
- A short tail of the previous assistant reply is added only to turns the script flags (interrupts, edit churn, error loops).
- Expected size: about 300 KB, or about 75k tokens, per month.

### Phase 1: three Opus agents

| Agent | Categories | Input |
|---|---|---|
| A | 1 prompting quality, 6 corrections and rework | digest turns and flagged-turn tails; rubric items for 1 |
| B | 4 repeats, 8 workflows to skills | typed prompts, the whole-Window repeat-candidate list, Bash heads and tool sequences recurring across 3+ Sessions; rubric items for 8 |
| C | 3 unused skills, 9 Overlap | the Toolkit table, dead slash names, prompts for skill matching; rubric items for 3 |

- Each agent also gets the previous Findings in its categories and checks their follow-through.
- Agents return Findings in the findings-file Finding layout, without numbers.
- The 55-item rubric (12 prompt quality, 17 context, 7 skills, 4 cost, 7 permissions and safety, 8 workflows) ships with the skill. Each item names its anti-pattern, whether it's script- or LLM-detected, and its source. Built-in thresholds:
  - `/clear` after two failed corrections;
  - a mistake made twice goes into CLAUDE.md;
  - a playbook pasted three times becomes a skill;
  - CLAUDE.md stays under 200 lines;
  - SKILL.md stays under 500 lines;
  - a description fits in 1,536 characters.
- A proposed skill follows the rubric's quality bar: concise, scripts for deterministic steps, and `disable-model-invocation: true` if it has side effects.

### Main session merge

1. Merge and dedupe the phase-1 Findings.
2. Write Findings for categories 2 (context), 5 (cost), and 7 (permissions) from the script's metrics, and check their follow-through.
3. Review `/insights`.
4. Build the problem list: the roughly five most frequent problems.
5. Run phase 2.
6. Put web solutions inline under the problems they solve.
7. Number the Findings, write the draft, and run `commit`.
8. If the statusline hint was printed, offer the statusline edit as the last step.

Category 7 solutions can point to the built-in `fewer-permission-prompts` skill.

### Phase 2: one Sonnet web agent

- Inputs:
  - the problem list;
  - the changelogs of Toolkit items that were used in the Window and are behind upstream (used and outdated CLIs included);
  - the news items the script matched.
- No search runs without a problem or a Toolkit item behind it.
- WebSearch is only for follow-ups ("fix for X", "Y vs Z"), never for discovery, because it has no date filter.
- WebFetch is for the two HTML-only sources and for article bodies the agent decides to read.

### Feeds and news filter

- Shortlist (endpoints in the AI landscape sources research):
  1. Claude Code GitHub releases API
  2. changelog RSS
  3. "What's new" digest (filter on the week label, not `pubDate`)
  4. claude.dev RSS
  5. claude.com/blog (HTML)
  6. HN Algolia with date and points filters
  7. GitHub Trending (HTML)
  8. official `marketplace.json` diff (the commit before the cursor against `main`)
  9. awesome-claude-code `Add resource:` commits
  10. Simon Willison's `claude-code` tag
- Reddit and X are unreachable and not used.
- Stage 1, in the script at zero tokens: date-filter by the cursor and score by keywords. Title hits count 3, body hits count 1, with a bonus for official sources and high HN points. The terms come from:
  - installed skill, plugin, and MCP server names;
  - all installed CLI names;
  - fixed platform terms;
  - per-category problem terms for the categories with detected problems.
  Official items always pass.
- Stage 2, in the LLM: keep an item only if it changes how an installed Toolkit item should be used, or addresses a detected problem.

### Toolkit inventory and upstream

- Every Toolkit kind records its origin and pin on disk:
  - the skills lock file (GitHub tree SHA per skill);
  - the synced skills' `manifest.json`;
  - `claude plugin list --json` and the installed-plugins file;
  - OpenSpec `metadata.generatedBy`;
  - npm and brew for CLIs.
  So "behind upstream" needs no stored state, about 6 network calls (one compare or tree call per source repository, plus npm and brew). Changelogs are scoped to the cursor. Undocumented layouts may be missing, and the script tolerates that.
- CLIs: `brew leaves --installed-on-request` plus `npm ls -g --depth=0`, and `claude` always counts.
  - Use in the Window: the first word of each Bash command, resolved with `which` + `realpath` to a Homebrew Cellar formula or an npm-global package. Anything else is ignored. One use counts.
  - Outdated: from `brew outdated --json=v2` and `npm outdated -g --json`. Used and outdated goes to the web agent. Unused and outdated gets one script line, such as `go 1.27.1 → 1.27.3 · not used this Window`.
  - No uninstall prompt for unused CLIs.
- The Toolkit table for agent C has one row per invocable item: skills of every origin, plugin skills, built-in commands, bundled skills (from the latest `skill_listing`, merged with the inventory on disk, because manual-only skills are missing from the listing), and agents. Columns: name, origin, auto or manual, description, uses in the Window, lifetime `skillUsage`. MCP servers and CLIs are left out.
- A plugin is unused when none of its Skill calls, typed commands, agents, or MCP tools appear in the Window.
- Dead slash names: slash names typed in the Window (from `history.jsonl`) that match no current Toolkit item.

### Overlap and Owned Skills

- Agent C detects Overlap from descriptions. It reads full `SKILL.md` files only for candidate sets. Usage is evidence, not the detector.
- Verdicts:
  - an Overlap member with 0 uses in the Window gets pick-one: uninstall it;
  - if neither member was used, C picks the better fit;
  - if a built-in wins, the verdict is to stop using your own copy.
- An Owned Skill is written, only when the user later asks, to `~/.claude/skills/<name>/` as a real folder. Its frontmatter carries `metadata: {upstream: [{repo, path, base}]}` for every source it kept content from, and it gets a row in the skills README.
- Originals are removed through their own installers (`npx skills remove`, `claude plugin uninstall`, `rm` for hand copies). The Finding says when removal isn't possible: a plugin can only be removed whole, and a built-in can't be removed.
- Upstream changes: each Retro runs one GitHub compare per repo from `base` to `HEAD`, filtered to the tracked paths. Changes to content the skill kept become "port this?" Findings, and changes to dropped parts are skipped. A deleted source gets a Finding. Nothing is merged automatically, and the Retro runs no git actions.

### `/insights` and other built-ins

- `prepare` starts `claude -p "/insights" --output-format json` in the background. It needs no permission flags, costs about $0.69, and takes about a minute.
- The JSON `result` names the new report. The script extracts four sections by their stable ids (about 17k characters in total):
  - `section-friction`: "Where Things Go Wrong"
  - `section-features`: "Existing CC Features to Try"
  - `section-patterns`: "New Ways to Use Claude Code"
  - `section-horizon`: "On the Horizon"
- The other sections ("What You Work On", "How You Use Claude Code", "Impressive Things You Did") are ignored.
- The main session gives each item one verdict: confirm, merge, amend, or drop. A stale item gets drop.
- `/usage`: `prepare` runs `claude -p "/usage" --output-format stream-json --verbose` (zero tokens, needs the normal login) and prints one line. No threshold.
- `/skill-doctor` is not called, because transcripts attribute plugin use.
- `/doctor prompt-audit` is suggested in a Finding when instruction files changed or grew during the Window. It is not called.
- Built-in commands, bundled skills, and agents count as Toolkit. Their upstream is Claude Code's releases.

### Findings file contract

- Sections, in order:
  1. a header line (Sessions, projects, Finding count);
  2. Failed parts (each says whether it was re-run);
  3. Follow-through (a table: a short summary of last month's fix → verdict);
  4. Findings, by weight across categories;
  5. Toolkit updates;
  6. Meta;
  7. `/insights` review (its date range, the confirm, merge, and amend counts, and each dropped item once, with its reason).
- No cost section, no evidence lines, no status, and no inventory list.
- The Finding layout is also the phase-1 agent contract. It comes from the findings-file prototype ticket:

  ```
  ### <n>. <category> · <project or "all"> · via <Retro | /insights | web>
  **Problem**: <one or two lines>
  **Solutions**:
  - **a.** <the exact change: file and edit, or command>. Fit: <…>. Adoption: <…>.
  - **b.** …
  ```

  - Toolkit updates and Meta items use **What changed** in place of **Problem**.
  - Numbers exist only for reference within one file. Nothing carries them across Retros.
  - A merge-and-own solution carries the outline and the sources to track, not the full `SKILL.md`.
- VS Code opens the file through `open`, with an editor association set once by the user to the markdown preview. HTML is out of scope.

### Failures, limits, and splitting

- No spending cap and no cost report.
- A failed agent, `/insights` run, or feed is listed under Failed parts. The Retro continues, and the Retro Timestamp still advances. If every phase-1 agent fails, nothing is committed.
- Usage-limit hit: the interactive Session pauses, and the user types "continue" after the reset. Claude re-runs only the agents that hit the limit, from the same input files. These don't count as failures.
- Other agent failures: Claude offers one re-run, with approval. If the user declines, or the re-run fails, the failure is listed and the Retro continues.
- An agent input over 100k tokens (estimated as bytes ÷ 4) is split into ceil(size ÷ 100k) pieces of whole Sessions in time order.
  - Every B piece also gets the whole-Window repeat list.
  - C is never split.
  - One Opus reconcile agent per split group merges the pieces' drafts and combines their evidence before frequency thresholds apply (3 + 3 counts as 6). It hands one set to the main merge.
  - At current volume (141 Sessions, about 35k tokens per agent) splitting won't trigger.

### Statusline reminder

- `status` reads the Retro Timestamp from the findings file:
  - before day 30: prints nothing;
  - day 30: `retro due`;
  - after day 30: `retro overdue · Nd lost`, orange for 1 to 6 days and red from 7;
  - no findings file: `retro due`.
- No quota is shown.
- Wiring: `prepare` checks `statusLine` in the user's settings file (and the script it names) for a `retro.py status` call. If the call is missing, it prints a hint, and `SKILL.md` has Claude offer one of these edits:
  - a statusline script: append one call, joined to the existing output with ` · `;
  - an inline command: append `; ~/.claude/skills/retro/retro.py status`;
  - no statusline: set it to the `status` call.
- A decline isn't stored, so the offer returns next run.

### Redo

- `/retro redo` runs `prepare --redo`:
  - skips the gate;
  - uses the last 30 days as the Window;
  - judges follow-through against the previous-findings file;
  - overwrites the findings file without rotating;
  - writes the Redo's start time as the new Retro Timestamp.
- With no committed Retro, a Redo is a first Retro run early.

## Testing Decisions

- **No automated tests.** There is no test file, no fixture tree, no stubbed shell or fetch seams, and no injected home directory or "now".
- **The one seam is a real run.** A real `/retro` (or `/retro redo`) over real transcripts is the acceptance test. The user reads the findings file, judges it, and asks Claude to change `SKILL.md` or `retro.py`. A good result is judged on behavior only: are the Findings right, specific, self-contained, and worth acting on? `/retro redo` makes this loop repeatable without waiting 30 days and without losing the follow-through baseline.
- **The only automatic guard** is the "format drift: N records skipped" line `prepare` prints. A jump in N after a Claude Code update means the parser needs attention.
- **What real runs should show early.** These aren't tests, only the behaviors a reviewer should check on the first runs:
  - a below-gate refusal at zero tokens, with progress;
  - the statusline offer and the four `status` outputs;
  - the file rotation on a normal commit, and no rotation on a Redo;
  - Failed parts filled when a feed is down;
  - an abort before `commit` leaving the Retro Timestamp unchanged.
- **Prior art**: none in this repo. The throwaway digest prototype in the research folder shows the parsing approach and measured sizes. It is not a test.

## Out of Scope

- Other tools (claude.ai web and desktop, Cursor, Codex). Claude Code CLI only.
- Multi-user use and packaging. One user on macOS.
- A long-term transcript archive, or a recorder of our own (through hooks or otherwise).
- HTML or chart reports. Markdown only.
- A walkthrough, or applying Findings inside the Retro. The user applies them later by asking Claude.
- Finding status (applied, declined, open), evidence lines, and a Toolkit inventory list in the file.
- A history of past Retros beyond the two findings files, and a history command.
- A watch list, and uninstall prompts for unused CLIs.
- A spending cap, `--max-budget-usd`, and any cost report or cost section.
- Automatic or quota-triggered Retros (launchd), and pre-digests that survive between runs.
- Detecting claude.ai connector additions or removals.
- Calling `/skill-doctor` or `/doctor prompt-audit`.
- Reddit and X as sources. WebSearch for discovery.
- Automatic merging, uninstalling, or git actions by the Retro.
- Forwarding stubs for removed skill names.
- A dotfiles repo for skills and configs. That is a separate effort, and Owned Skills in `~/.claude/skills/<name>/` keep working once that folder is symlinked.
- Automated tests and test-only overrides.

## Further Notes

- **Paths in this spec.** The paths under `~/.claude` are external contracts: where Claude Code keeps its data and where Retrosmith keeps its state. They aren't source layout, so they stay in the spec.
- **Known current state the first Retro should catch** (measured 2026-10-20 to 2026-10-21):
  - grill-me / grill-with-docs / grilling Overlap;
  - review-skill Overlap (`pocock-review`, bundled `/code-review`, `ponytail-review`);
  - ponytail 4.13.0 against upstream 5.3.2;
  - 16 of 26 mattpocock skills changed upstream;
  - `resolving-merge-conflicts` removed upstream;
  - `wait-what` locked but never symlinked;
  - OpenSpec 1.14.2 with 1.14.3 available, and stale generated skills;
  - hand-copied pstack skills with no provenance.
- **Superseded decisions** to ignore when reading the tickets:
  - the ~150-prompt gate (replaced by 30 days);
  - "no force option" (replaced by Redo);
  - Finding status and the walkthrough;
  - "previously declined" (now "raised before");
  - the watch list;
  - `/usage` being ignored (`prepare` now prints one `/usage` line);
  - the `/insights` cost going into a cost report;
  - the prototype's evidence lines, status, `F` ids, "you said" column, and linked Meta Findings.
- **Derived, not decided in a ticket:** the feed and changelog cursor for a Redo (the timestamp in `findings.prev.md`), and that the rubric ships with the skill as a reference the agents read.
