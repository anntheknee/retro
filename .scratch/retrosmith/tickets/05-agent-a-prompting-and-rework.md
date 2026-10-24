# 05: Agent A: prompting and rework

**What to build:** Phase 1 begins. An Opus subagent judges prompting quality and rework (categories 1 and 6) from its slice of the digest, and the main session merges its Findings with its own.

Details: [spec](../spec.md), sections "Phase 1: three Opus agents", "Main session merge". Rubric: [prompting and context best practices](../research/05-prompting-and-context-best-practices.md).

**Blocked by:** 04: Findings for context, cost and permissions

**Status:** done

- [x] `retro.py context <session> <turn>` prints one turn in full: the typed prompt, the end of Claude's previous reply, and the turn's tools and errors. Agents use it when the digest isn't enough and never read raw transcripts.
- [x] The script flags turns with interrupts, mid-turn steering, repeated edits to one file, or error-and-retry loops, and adds a short tail of the previous reply to those turns only.
- [x] The 42-item rubric ships with the skill as a reference. Agent A reads the items for prompt quality, plus the rework-related context items.
- [x] `prepare` writes A's input file into the temp folder. A runs on Opus and returns Findings in the Finding layout, without numbers.
- [x] The main session merges and dedupes A's Findings with its own, then numbers all of them by weight.
- [x] Verify: `/retro redo`, and judge the category 1 and 6 Findings.
