# 16: Failures and re-runs

**What to build:** A broken part never costs the user the month. Failures are listed, usage-limit pauses recover, and an empty Retro never replaces a real one.

Details: [spec](../spec.md), section "Failures, limits, and splitting".

**Blocked by:** 15: Web agent: news and changelogs

**Status:** done

- [x] The Failed parts section lists each failed agent, `/insights` run, or feed, and says whether it was re-run.
- [x] Usage limit: the Session pauses and the user types "continue" after the reset. Claude re-runs only the agents that hit the limit, from the same input files. This isn't counted as a failure.
- [x] Other agent failures (crash, garbled output, timeout) get one re-run offer, with approval. If the user declines or the re-run fails, the failure is listed and the Retro continues.
- [x] The Retro Timestamp advances despite failures. If every phase-1 agent fails, nothing is committed and the state is unchanged.
- [x] No spending cap and no cost report.
- [x] Verify: `/retro redo` with the network off for one feed shows it under Failed parts. Decline a re-run once and see it listed.
