# 07: Toolkit table and agent C: unused skills

**What to build:** A Retro knows the whole Toolkit and how much of it was used. A third Opus subagent finds tasks the user did by hand that an installed skill would have handled (category 3).

Details: [spec](../spec.md), sections "Toolkit inventory and upstream", "Phase 1: three Opus agents". Inventory sources: [Toolkit inventory research](../research/03-toolkit-inventory-and-upstream-sources.md).

**Blocked by:** 06: Agent B: repeats and workflows

**Status:** done

- [x] The inventory comes from disk: skills of every origin (lock file, symlink targets, synced manifest, hand copies, project OpenSpec skills), plugins, built-in commands, bundled skills from the latest skill listing merged with the inventory on disk, and agents. Missing undocumented layouts are tolerated.
- [x] The Toolkit table has one row per invocable item: name, origin, auto or manual, description, uses in the Window, and lifetime `skillUsage`. MCP servers and CLIs are left out.
- [x] A plugin is unused when none of its Skill calls, typed commands, agents or MCP tools appear in the Window. A plugin that only ships hooks is reported as "hooks only, can't tell".
- [x] Agent C's input holds the table, the prompts to match against skills, and the rubric items for using skills. C runs on Opus in parallel with A and B, and its input is never split.
- [x] Verify: `/retro redo`. The table lists every installed skill (including `grill-me` and `wayfinder`, which the skill listing omits), and the category 3 Findings make sense.
