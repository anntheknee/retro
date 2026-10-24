# 12: Owned Skill upstream

**What to build:** Owned Skills keep tracking their upstream sources. Edited installs and skills without machine-readable provenance get Findings that would bring them under tracking.

Details: [spec](../spec.md), section "Overlap and Owned Skills".

**Blocked by:** 11: CLIs

**Status:** done

- [x] For each Owned Skill's `metadata.upstream` entries, the script runs one GitHub compare per repo from `base` to `HEAD`, filtered to the tracked paths.
- [x] Changes to content the skill kept become a "port this?" Finding that names the tracked source and the `base` range. Changes to dropped parts are skipped silently.
- [x] A deleted upstream source gets a Finding.
- [x] An install whose content differs from its locked base (such as `pocock-review`) gets a Finding to own it, with one tracked source.
- [x] Skills with no machine-readable provenance (the pstack hand copies, `principles`) get a Finding to add `metadata.upstream`.
- [x] Nothing is merged automatically and the Retro runs no git.
- [x] Verify: `/retro redo` raises the `pocock-review` and provenance Findings. Add `metadata.upstream` with an old `base` to one skill by hand and see a "port this?" Finding.
