# Map: Retrosmith

Label: wayfinder:map

## Destination

Every decision `/to-spec` needs to write a complete v1 spec for `/retro` (then `/to-tickets` and build): a Claude Code skill + helper script that runs a **Retro** over the **Window** since the last **Retro Timestamp**. It checks follow-through on the previous **Findings**, scans the web for **Toolkit** updates and AI-tooling meta, and writes a markdown findings file that the user reads and acts on.

## Notes

- **Domain**: personal Claude Code effectiveness. Vocabulary lives in `/CONTEXT.md` (Session, Retro, Window, Retro Timestamp, Toolkit, Finding). Use it.
- **Skills every session should consult**: `grilling` + `domain-modeling` for HITL tickets; `research` for research tickets. Ponytail applies: smallest thing that works.
- **Fixed by charting**:
  - Claude Code CLI only. Single user (me), macOS.
  - Form: a Claude Code skill + helper script, self-contained (uses built-in WebSearch/WebFetch and subagents; no API key, no external CLI orchestrator). Source in this repo, symlinked to `~/.claude/skills/retro`.
  - Data source: Claude Code's own transcripts in `~/.claude/projects/<cwd-slug>/<session>.jsonl` (+ `subagents/`) and `~/.claude/history.jsonl`. No recorder of our own and no archive. `cleanupPeriodDays` was set to 30 on 2026-10-21, matching the Window: always the last 30 days, so a late Retro leaves an unanalyzed gap.
  - Stores nothing of the user's except the Retro Timestamp, the latest Retro's Findings, and the ones before them (`findings.prev.md`, kept so a Redo has a follow-through baseline). Transcripts are never deleted by Retrosmith.
  - One Retro spans all projects; Findings are tagged by project where relevant.
  - Problem categories, all v1: (1) prompting quality, (2) context management, (3) skills you have but didn't use, (4) asking the same thing repeatedly, (5) cost/token hotspots, (6) corrections and rework, (7) permission-prompt friction, (8) repeated manual workflows that should become a skill, (9) **toolkit overlap**: duplicate skills (e.g. grill-me / grilling / grill-with-docs) with merge proposals, plus usage gaps after uninstalling or merging a skill.
  - Web scan, both v1: (i) updates and best practices for installed Toolkit items; (ii) AI-tooling meta and discovering new tools.
  - Toolkit CLIs: everything installed through brew or npm on request, plus `claude`. No watch list (see [Watch list](wayfinder-issues/14-watch-list.md)).
  - Skill merges: case by case. The Retro recommends merge-and-own (while still watching upstream) or pick-one, with its reasoning.
  - A Retro fans out to subagents in two phases (Opus judges the transcripts, then one Sonnet web agent searches for the problems found) and runs as long as it needs, then writes a markdown findings file and opens it. There is no walkthrough: the user applies Findings later by asking Claude.
  - v1 is triggered manually with `/retro`, monthly. `/retro redo` skips the gate and regenerates the latest Retro (see [Testing the skill](wayfinder-issues/15-testing-the-skill.md)).
  - **No automated tests**: the user judges real Retros and asks Claude for changes.
  - **`/insights` is a second opinion.** Every Retro runs it headlessly, reviews four of its report sections against its own Findings, and keeps its own analysis of all nine categories. A Retro runs on Opus. Built-in commands count as Toolkit. Each Finding records its origin.
- **Standing preference (script vs. LLM)**: the script does the heavy lifting in plain code, and the LLM only spends tokens on judgment. A Retro's own cost is neither capped nor reported.

## Decisions so far

<!-- one line per closed ticket: [title](wayfinder-issues/NN-slug.md): gist -->

- [Prompting and context best practices](wayfinder-issues/05-prompting-and-context-best-practices.md): 42-item rubric with doc thresholds (`/clear` after 2 failed corrections, a repeated playbook 3× → skill, CLAUDE.md under 200 lines); category 8 proposes skills, not commands; overlapping built-ins exist (`/insights`, `/skill-doctor`, `/usage`, `/doctor prompt-audit`)
- [Usage quota visibility](wayfinder-issues/02-usage-quota-visibility.md): `claude -p "/usage" --output-format stream-json --verbose` returns session and weekly percent used plus reset times at zero token cost (needs the normal login, experimental, rate limited); headless `-p` can run skills and subagents but needs explicit permission flags; trigger locally with launchd, since `/schedule` can't see `~/.claude`
- [AI landscape sources](wayfinder-issues/04-ai-landscape-sources.md): 10-source shortlist, all RSS/Atom/JSON except two, so the script fetches and filters by date and keyword at zero token cost and the LLM judges only the ~20–40 items that pass; Reddit and X are blocked; new plugins are found by comparing the official `marketplace.json` before the Retro Timestamp with now; Claude Code releases need the GitHub releases API (the RSS/Atom feeds are too short)
- [Transcript signal catalog](wayfinder-issues/01-transcript-signal-catalog.md): exact by script: cost, permission friction, context management; script finds candidates and the LLM decides: 5 categories; mostly LLM: prompting quality; the format is officially internal and changes between versions, so parse tolerantly; take only the last line per `requestId` or tokens count double; a per-Session digest is ~970× smaller (~75k tokens/month); `history.jsonl` survives cleanup (~7 months) and can be used to spot repeated questions
- [Toolkit inventory and upstream sources](wayfinder-issues/03-toolkit-inventory-and-upstream-sources.md): every kind records its origin and pin on disk (`~/.agents/.skill-lock.json`, `installed_plugins.json`, synced `manifest.json`, `npm`/`brew outdated`), so "behind upstream" needs no stored state (~6 network calls); hand-copied pstack skills have no machine-readable provenance; `~/.claude.json` `skillUsage` gives per-skill use counts; detecting removals needs the previous inventory
- [Retro state and lifecycle](wayfinder-issues/06-retro-state-and-lifecycle.md): state is one file, `~/.claude/retro/findings.md`, with the Retro Timestamp in its frontmatter; the Window is filtered message by message; the timestamp is captured at the start and written with the Findings before the walkthrough; Findings are marked applied, declined or open in place; a gate makes the Retro do nothing below it, with no force option (now 30 days, per Script vs. skill boundary and subagent fan-out); the Retro's own Session is skipped from `/retro` onward, with nothing stored
- [Relationship to built-in insights tools](wayfinder-issues/11-relationship-to-built-in-insights-tools.md): the destination doesn't shrink. Every Retro runs `claude -p "/insights"` (~$0.69) and reviews four report sections as a second opinion (confirm, merge, amend, or drop). `/skill-doctor` isn't called, because transcripts attribute plugin use. Findings suggest `/doctor prompt-audit` instead of calling it. `/usage` is ignored. The Retro runs on Opus. Built-ins count as Toolkit. Findings record their origin. `cleanupPeriodDays` is now 30
- [Script vs. skill boundary and subagent fan-out](wayfinder-issues/07-script-vs-skill-boundary-and-fan-out.md): `SKILL.md` + `retro.py` (Python 3 stdlib) with `prepare` / `context` / `commit`. The script computes all numbers and Claude writes every Finding. Gate: 30 days since the Retro Timestamp; the Window is the last 30 days. Phase 1: three Opus agents by category group, each also checking follow-through. The main session merges, adds 2/5/7, and reviews `/insights`. Phase 2: one Sonnet web agent for the ~5 top problems plus used-Toolkit changelogs and matched news. The main session links solutions to problems
- [Skill overlap and merge workflow](wayfinder-issues/08-skill-overlap-and-merge-workflow.md): agent C judges overlap from a table of names, descriptions, and usage. An unused duplicate means pick-one and uninstall. The merged skill is written only on approval, to `~/.claude/skills/<name>/`, with `metadata.upstream` for every source it kept, and the originals are uninstalled. Edited installs (`pocock-review`) are owned the same way. Upstream diffs from `base` become "port this?" Findings. Typed dead `/names` and follow-through catch old habits, with no inventory appendix. A declined overlap returns every Retro while it still exists
- [Findings file shape](wayfinder-issues/10-findings-file-shape.md): sections ordered Failed parts → Follow-through → Findings by weight → Toolkit updates → Meta → `/insights` review; each Finding is a numbered heading (category · project · origin), a Problem, and up to 3 lettered self-contained Solutions with fit and adoption notes; no evidence, status or inventory list; follow-through is judged from what changed; no walkthrough, since `commit` runs `open` on the file
- [Token budget and cost guardrails](wayfinder-issues/09-token-budget-and-cost-guardrails.md): no spending cap or cost report; `prepare` prints one `/usage` line; agents that hit the usage limit re-run after you resume, others get one re-run with approval; an agent input over 100k tokens splits into pieces of whole Sessions in time order (B pieces share the whole-Window repeat list), and an Opus reconcile agent merges each split group's pieces before the main merge
- [Retro due reminder](wayfinder-issues/13-retro-due-reminder.md): a statusline segment from a new `retro.py status` subcommand: nothing before day 30, `retro due`, then `retro overdue · Nd lost` (red from 7); no findings file → due; no quota shown; every `/retro` run checks `statusLine` and offers to add the call, with no stored decline
- [Watch list](wayfinder-issues/14-watch-list.md): no watch list; installed CLIs come from `brew leaves --installed-on-request` + `npm ls -g --depth=0`, and Window use from Bash command names resolved by `which` to a Cellar or npm-global path; used and outdated CLIs get their changelogs read by the web agent, unused ones get a zero-token version line; the news filter uses all installed CLI names
- [Testing the skill](wayfinder-issues/15-testing-the-skill.md): no automated tests; you judge real Retros and ask Claude for changes, with `prepare`'s drift line as the only guard; `/retro redo` (`prepare --redo`) skips the gate and replaces the latest Retro, moving the Retro Timestamp; `commit` renames the old `findings.md` to `findings.prev.md` so a Redo checks follow-through against the right baseline

## Not yet specified

<!-- nothing left in the fog; no open tickets: the map is complete and ready for /to-spec -->

## Out of scope

- Other tools (claude.ai web/desktop, Cursor, Codex): Claude Code only.
- A long-term transcript archive: rely on `cleanupPeriodDays` + Retro Timestamp.
- Multi-user use and packaging: just me.
- A recorder of our own (via hooks or otherwise): transcripts already capture what's needed.
- HTML or chart reports: markdown in v1.
- Detecting claude.ai connector additions or removals: it needs a stored inventory and is low value ([Findings file shape](wayfinder-issues/10-findings-file-shape.md)).
- Automatic or quota-triggered Retros (launchd): v1 is manual `/retro`. The 30-day gate makes a quota trigger rarely useful, a pre-digest would be new state, and an unattended run has no one to handle usage-limit pauses or approve re-runs ([Quota-aware automatic runs](wayfinder-issues/12-quota-aware-automatic-runs.md))
- A dotfiles repo for skills and configs: a separate effort. Owned skills go in `~/.claude/skills/<name>/`, which still works once that folder is symlinked from the repo ([Skill overlap and merge workflow](wayfinder-issues/08-skill-overlap-and-merge-workflow.md)).
