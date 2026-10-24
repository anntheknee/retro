# 09: Follow-through

**What to build:** Every Retro judges the previous Retro's Findings from what actually changed, and shows the verdicts in the Follow-through table.

Details: [spec](../spec.md), user stories 26–30, and section "Redo".

**Blocked by:** 08: Overlap

**Status:** done

- [x] Baseline: a normal Retro uses the current findings file and a Redo uses the previous-findings file. With neither, the section says there was no previous Retro.
- [x] `prepare` puts the previous Findings for each agent's categories into that agent's input. The main session judges categories 2, 5 and 7, the Toolkit updates and the Meta items.
- [x] Verdicts are worked, didn't work, not adopted, or no longer relevant. They are judged from what changed: settings, installs, usage, and whether the problem came back. Nothing is marked in the old file.
- [x] A Finding that wasn't adopted comes back only if the problem got worse. An Overlap that still exists comes back every Retro, labelled "raised before". After an applied merge or removal, the Retro checks that the replacement got used.
- [x] The table gives a short summary of each previous fix, its verdict, and its origin.
- [x] Verify: copy an earlier findings file to the previous-findings file by hand, run `/retro redo`, and judge the table.
