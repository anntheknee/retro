# 06: Agent B: repeats and workflows

**What to build:** A second Opus subagent finds questions the user asks repeatedly and workflows that should become skills (categories 4 and 8). It runs in parallel with agent A.

Details: [spec](../spec.md), section "Phase 1: three Opus agents".

**Blocked by:** 05: Agent A: prompting and rework

**Status:** done

- [x] The script builds a whole-Window repeat-candidate list (normalized repeats across Sessions and projects) and lists near-duplicate long prompts, similar Session openings, near-identical Agent prompts, and Bash command heads and tool sequences recurring across 3 or more Sessions.
- [x] B's input holds the typed prompts, those lists, and the rubric items for workflows, including the quality bar for proposed skills.
- [x] Category 8 Findings propose a skill, hook or subagent depending on the trigger, and meet the rubric's quality bar.
- [x] B runs on Opus in parallel with A, and the main session merges its Findings.
- [x] Verify: `/retro redo`, and judge the category 4 and 8 Findings.
