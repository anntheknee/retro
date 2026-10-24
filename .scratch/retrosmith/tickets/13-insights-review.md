# 13: `/insights` review

**What to build:** Every Retro runs `/insights` as a second opinion and reviews four of its sections against its own Findings.

Details: [spec](../spec.md), section "`/insights` and other built-ins".

**Blocked by:** 12: Owned Skill upstream

**Status:** done

- [x] `prepare` starts headless `/insights` with JSON output in the background, with no permission flags.
- [x] The script finds the new report from the JSON result, extracts the four sections by id (`section-friction`, `section-features`, `section-patterns`, `section-horizon`), and records the report's date range.
- [x] After the phase-1 merge, the main session gives each item one verdict. Confirm or amend makes it a Finding tagged `via /insights`. Merge joins it to an existing Finding. Drop lists it once, with the reason. A stale item is dropped.
- [x] The `/insights` review section shows the date range, the confirm, merge and amend counts, and the dropped items.
- [x] If `/insights` fails, the file says so and the Retro continues.
- [x] Verify: `/retro redo`, and compare the review section with the HTML report.
