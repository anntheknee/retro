# 14: Web agent: solutions for top problems

**What to build:** Phase 2 begins. A Sonnet web agent looks for better solutions to the top problems, and the main session places them inline in each problem's Finding.

Details: [spec](../spec.md), sections "Main session merge", "Phase 2: one Sonnet web agent".

**Blocked by:** 13: `/insights` review

**Status:** done

- [x] After the `/insights` review, the main session builds the problem list: the roughly five most frequent problems. Each is searched even when the Toolkit already has a fix.
- [x] One Sonnet subagent uses WebSearch only for follow-ups ("fix for X", "Y vs Z") and WebFetch for article bodies. No search runs without a problem behind it.
- [x] The main session adds the results as lettered solutions under the matching Finding, with fit and adoption notes and at most 3 solutions per Finding.
- [x] Verify: `/retro redo`. The top Findings show web solutions, and each one names something concrete to install or change.
