# 17: Splitting and reconcile

**What to build:** An agent input that grows too large is split into pieces and reconciled before the merge, so growing volume never breaks a Retro. It won't trigger at today's volume.

Details: [spec](../spec.md), section "Failures, limits, and splitting".

**Blocked by:** 16: Failures and re-runs

**Status:** done

- [x] An agent input over 100k tokens (estimated as bytes ÷ 4) is split into ceil(size ÷ 100k) pieces of whole Sessions in time order. A Session is never cut. Each piece runs with the agent's same instructions.
- [x] Every B piece also gets the whole-Window repeat list. C is never split.
- [x] One Opus reconcile agent per split group merges the pieces' drafts and combines their evidence before frequency thresholds apply (3 + 3 counts as 6). It hands one set to the main merge.
- [x] The cap is one script constant.
- [x] Verify: lower the cap for one `/retro redo` so that A and B split, judge the merged Findings, then restore the cap.
