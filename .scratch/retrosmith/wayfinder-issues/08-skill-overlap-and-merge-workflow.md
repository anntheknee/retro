# Skill overlap and merge workflow

Type: grilling
Status: resolved
Assignee: me
Blocked by: 03

## Question

How does a Retro detect overlapping skills (by description, by content, or by usage)? What does a merge proposal look like? Where does a merged skill live, and what happens to the originals? How do upstream changes to the originals reach a merged-and-owned skill? How are usage gaps after uninstalling or merging a skill reported (e.g. still typing `/grill-me`)?

## Answer

- **Detection (by description)**: `prepare` writes one table of every invocable Toolkit item: skills of any origin, plugin skills, built-in commands, bundled skills, and agents. Each row has the name, origin, auto or manual, description, uses in the Window, and lifetime `skillUsage`. Bundled skills come from the latest `skill_listing` in the Window. Manual-only skills are missing from that listing (`grill-me`, `wayfinder`), so the script merges it with the inventory on disk. MCP servers and CLIs are left out. Agent C (categories 3 and 9) judges which items overlap and reads the full `SKILL.md` only for the candidate sets. Usage counts are evidence, not the detector.
- **Unused duplicate**: two items that do the same job count as an overlap even when only one is used. If one has 0 uses in the Window, the verdict is pick-one: uninstall it. Lifetime use is shown as context. If neither was used, C still picks the one that fits better.
- **The proposal (a Finding)**: it gives the overlap set, the evidence, and a verdict, either **pick-one** (keep X, remove the rest) or **merge-and-own** (new name, what each original contributes, what's dropped, which sources to track), with reasoning. The merged `SKILL.md` is written only when the user approves the Finding in the walkthrough. The Retro stores only the outline.
- **Owned skills**: written to `~/.claude/skills/<name>/` as a real folder, with `metadata: {upstream: [{repo, path, base}]}` in the frontmatter (Claude Code ignores `metadata`) and a row in `~/.claude/skills/README.md`. Every source that C kept content from is tracked. For example, C made 70% from A and 30% from B tracks both. The user can remove a source when approving the Finding. The Retro does no git actions.
- **The originals**: every original is removed through its own installer: `npx skills remove`, `claude plugin uninstall`, or `rm` for hand copies. The Finding says when that isn't possible. A plugin can only be removed whole, and a built-in can't be removed, so when a built-in wins, the verdict is to stop using your own copy.
- **Edited installs**: these are owned the same way, with one tracked source. Example: `pocock-review` differs from its installed base only in `name:`, and `npx skills update` would restore `name: code-review`, which collides with the bundled `/code-review`. The six pstack copies and `principles` have no machine-readable provenance, so the first Retro raises a Finding to add `metadata.upstream` to them.
- **Upstream changes**: each Retro, the script runs one GitHub compare per repo from each owned skill's `base` to `HEAD`, filtered to the tracked paths. Changes to content the skill kept become a "port this?" Finding, and applying it means Claude ports the change and bumps `base`. Changes to dropped parts are skipped silently. A deleted upstream source also gets a Finding. Nothing is merged automatically.
- **Old habits after a removal or merge**: two checks. (1) Follow-through on the previous Retro's applied merge or removal checks that the replacement got used. Requests it should have caught are category 3. (2) The script lists the slash names typed in the Window (from `history.jsonl`) that match no current Toolkit item. C sorts them into removed-skill habits, typos (`/cleaer`, `/handover`), and noise. The Finding only informs, and no forwarding stubs are created. Neither check needs a stored inventory, so category 9 doesn't need the inventory appendix.
- **A declined overlap comes back** labelled "previously declined" in every Retro while the overlap still exists. This rule applies to overlaps only. Every other category keeps the rule that a declined Finding returns only if the problem got worse ([Script vs. skill boundary and subagent fan-out](07-script-vs-skill-boundary-and-fan-out.md)).
- **Out of scope**: a dotfiles repo for all skills and configs is a separate effort. `~/.claude/skills/<name>/` stays valid once that folder is symlinked from the repo.

Superseded in part by [Findings file shape](10-findings-file-shape.md): there is no walkthrough. The merged `SKILL.md` is written when the user later asks Claude to apply that Finding, so the Finding's solution carries the outline and the sources to track. An overlap that is still present is labelled "raised before", not "previously declined".
