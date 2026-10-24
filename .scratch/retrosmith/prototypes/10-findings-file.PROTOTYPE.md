---
retro_timestamp: 2026-10-22T07:19:50Z
window: 2026-09-22T07:19:50Z .. 2026-10-22T07:19:50Z
insights_range: 117 sessions | 2026-09-20 to 2026-10-21
---
<!-- PROTOTYPE, throwaway, superseded by the Answer in wayfinder-issues/10-findings-file-shape.md (no evidence, no status, no F ids, solutions inline): answers "Findings file shape" (ticket 10). Real Sessions, invented verdicts. -->
<!-- `commit` writes the frontmatter. Claude writes only the body and changes only `status:` lines during the walkthrough. -->

# Retro 2026-10-22

149 Sessions · 5 projects · 18 Findings (12 retro, 3 web, 3 /insights)

## Failed parts

- Feed `simonwillison.net/atom`: HTTP 503. Skipped.
- Agent B: hit the usage limit, re-ran after resume. OK.

## Follow-through

Previous Retro: 2026-09-21. Verdicts: worked, didn't work, not done, no longer relevant.

| Prev | Finding | Status then | Verdict | Why |
|---|---|---|---|---|
| F2 | Merge grill-me / grilling / grill-with-docs | applied | worked | `/grilling` 14×, no `/grill-me` typed since |
| F5 | `/clear` after 2 failed corrections | applied | didn't work | 3 Sessions ran past 2 corrections ("Oncoming car speed in report.md", …) |
| F7 | Turn the opsx apply→verify→archive loop into one skill | declined | — | not re-raised: problem didn't get worse |

## Findings

### F1 · prompting · temp · status: open
origin: retro

**Problem**: Five Sessions in a row re-explain the radar-speed task from scratch after `/clear`, each starting with a vague prompt ("what speed is the oncoming car").
**Evidence**:
- "Oncoming car speed in report.md" · temp · 2026-10-18 · `claude --resume 575f4865-8d34-4abf-ac4d-5100fb7f1a71` · turn 1
- "Report.md oncoming car peak speed" · temp · 2026-10-18 · `claude --resume e16e72e6-c6fd-4ce7-a9ab-e4b58263ba14` · turn 1
- +3 more Sessions
**Advice**: Keep the task's facts in a file (`report.md` already exists) and open with "read report.md, then …".
**Apply**: advice only.

### F2 · permission friction · stealth · status: open
origin: retro

**Problem**: 8 denials in 30 days, 6 of them for `Write(.env.local)` and `Bash(git merge …)`.
**Evidence**: "Writing .env.local DATABASE_URL" · stealth · 2026-10-18 · `claude --resume c6f8f9e6-08de-4178-b0d5-67ddc9bd3b5e` · 3 denials
**Advice**: The `.env.local` denials are deliberate: keep them. Allow `Bash(git merge:*)` in stealth.
**Apply**: add `"Bash(git merge:*)"` to `stealth/.claude/settings.json` `permissions.allow`.

### F3 · toolkit overlap · all · status: open
origin: retro

**Problem**: `pocock-review`, `code-review` (bundled) and `ponytail-review` overlap. `pocock-review` was used 3×, `ponytail-review` 0×.
**Evidence**: "Pocock, code-review, ponytail reviews" · stealth · 2026-10-20 · `claude --resume fc865938-7390-4620-9477-7b1d574a6302`
**Verdict**: merge-and-own → `review` (previously declined: no)
- from `pocock-review`: Standards + Spec axes, parallel subagents
- from `ponytail-review`: the over-engineering pass, as a third axis
- dropped: `code-review` (bundled, can't remove; stop invoking it by hand)
- track: `mattpocock/skills@<sha>:pocock-review/`, `ponytail@5.3.2:skills/ponytail-review/`
**Apply**: write `~/.claude/skills/review/SKILL.md` from this outline, `npx skills remove pocock-review`, `claude plugin` can't remove one skill from ponytail, so leave it.

### F4 · toolkit overlap · all · status: open
origin: retro

**Problem**: You typed `/bro` once. It matches no Toolkit item.
**Evidence**: "Report.md oncoming car peak speed" · temp · 2026-10-18 · `claude --resume e16e72e6-c6fd-4ce7-a9ab-e4b58263ba14`
**Advice**: Typo, no action.
**Apply**: advice only.

### F5 · unused skills · stealth · status: open
origin: /insights (amended)

**Problem**: You looked up California LLC fees by hand over 11 prompts. `/research` would have run it in the background with sources.
**Evidence**: "California LLC registration fees" · stealth · 2026-10-19 · `claude --resume 37fd9ab1-...` · turns 2–9
**Solution** (web): —
**Apply**: advice only.

<!-- …F6–F12: one Finding per problem, ordered by category 1–9, then by weight -->

## Toolkit updates

### F13 · ponytail 4.13.0 → 5.3.2 · status: open
origin: web

**Why it matters**: you used `ponytail` in 31 Sessions. 5.x adds `ponytail-debt`, renames levels. Third-party marketplaces don't auto-update.
**Source**: <https://github.com/…/ponytail/releases/tag/v5.0.0>
**Apply**: `claude plugin update ponytail`.

### F14 · port this? `grilling` upstream changed · status: open
origin: web

**Change**: upstream `grilling/SKILL.md` adds a "stop after 3 unanswered" rule (base `a1b2c3d` → `HEAD`).
**Apply**: port the hunk into `~/.claude/skills/grilling/`, bump `base`.

## Meta

### F15 · solves F2? `/permissions suggest` (Claude Code 2.4.0) · status: open
origin: web

**Linked to**: F2
**Source**: <https://github.com/anthropics/claude-code/releases/tag/v2.4.0>
**Apply**: advice only (try it in stealth).

## /insights review

Range: 117 sessions | 2026-09-20 to 2026-10-21. Confirmed 1, merged 1 (into F2), amended 1 (F5).

Dropped:
- "Set up a `/commit` command": already done (`commit-commands` plugin installed 2026-10-12).
- "Use Plan Mode for the video analysis": outside the Window's projects.
