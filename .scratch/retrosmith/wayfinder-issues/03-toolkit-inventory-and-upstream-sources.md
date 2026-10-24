# Toolkit inventory and upstream sources

Type: research
Status: resolved
Blocked by:

## Question

How can every Toolkit item be listed with its version and origin: user skills in `~/.claude/skills` (including the `synced` dir and skills installed from others' repos), plugins and marketplaces (`~/.claude/plugins`), MCP servers, and CLIs like openspec (npm global)? For each kind of origin, where are upstream changes found (git repo commits/releases, marketplace, npm, changelog), and how can a Retro tell "changed since the last Retro"?

## Answer

Each Toolkit kind already records its origin and pin: `~/.agents/.skill-lock.json` stores a GitHub tree SHA per skill, the synced skills' `manifest.json` stores `updatedAt`, `claude plugin list --json` and `installed_plugins.json` store the version or commit SHA, OpenSpec project skills store `metadata.generatedBy`, and `npm`/`brew outdated --json` cover CLIs. The hand-copied pstack skills are the exception: their provenance is prose in the README only.
"Behind upstream" needs no state. Compare each pin with upstream using about 6 calls (one GitHub Trees or compare call per source repository, plus npm and brew), then scope the changelog with `since=<Retro Timestamp>`. Detecting removals needs a list kept from the last Retro.
Current state: 16 of 26 mattpocock skills changed upstream, and `resolving-merge-conflicts` was removed upstream. ponytail is on 4.13.0 while upstream is 5.3.2, because third-party marketplaces do not auto-update. OpenSpec 1.14.2 has 1.14.3 available, and both repositories' generated skills are stale. The local `pocock-review` edit would be overwritten by `skills update`. Overlaps: grill-me / grill-with-docs / grilling, plus several review skills.

[findings](../research/03-toolkit-inventory-and-upstream-sources.md)
