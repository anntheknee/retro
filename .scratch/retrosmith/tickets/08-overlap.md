# 08: Overlap

**What to build:** Agent C finds Overlaps in the Toolkit and gives each one a pick-one or merge-and-own verdict with its reasoning. It also catches old habits: slash names typed in the Window that match no Toolkit item.

Details: [spec](../spec.md), section "Overlap and Owned Skills".

**Blocked by:** 07: Toolkit table and agent C: unused skills

**Status:** done

- [x] C judges Overlap from descriptions and reads full `SKILL.md` files only for candidate sets. Usage counts are evidence, not the detector.
- [x] An Overlap member with 0 uses in the Window gets pick-one (uninstall it). If no member was used, C picks the better fit. If a built-in wins, the verdict is to stop using your own copy.
- [x] A merge-and-own solution carries the new name, what each original contributes, what's dropped, and the sources to track. It says the Owned Skill goes in the user's skills folder with `metadata.upstream` and a README row, and that the originals are removed through their own installers. The Finding says when removal isn't possible.
- [x] The script lists slash names typed in the Window that match no Toolkit item. C sorts them into removed-skill habits, typos and noise. The Finding only informs, and no forwarding stubs are created.
- [x] The Retro never merges, uninstalls or runs git.
- [x] Verify: `/retro redo` raises the grill-me / grill-with-docs / grilling Overlap and the review-skill Overlap.
