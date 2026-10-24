# Toolkit inventory and upstream sources

Research for ticket [03](../wayfinder-issues/03-toolkit-inventory-and-upstream-sources.md). Observed on 2026-10-20 on the user's machine (Claude Code 2.1.304, macOS). Everything was inspected read-only.

## Summary

Every Toolkit kind already has a machine-readable record of what is installed, where it came from, and a version or content hash. A Retro does not need its own inventory store. It can answer two separate questions without a stored snapshot:

1. **Behind upstream?** Compare the installed pin (tree SHA, commit SHA, version) with upstream HEAD or the latest release. This check is stateless.
2. **Changed since the last Retro?** Filter upstream commits, releases, and publish times, plus local install timestamps, by the Retro Timestamp.

Question 1 decides whether there is anything to report. Question 2 limits how much changelog the LLM reads. The script can do both with about one GitHub API call per source repository, `npm outdated -g --json`, and `brew outdated --json=v2`.

One gap: without a stored inventory, the script cannot see that a skill was **removed** since the last Retro. Additions show up through install timestamps, but removals do not. See [Open points](#open-points-for-the-spec).

## Per kind: enumerate, metadata, upstream, "changed since"

### 1. Skills installed with the `skills` CLI (mattpocock/skills)

- **Enumerate**: in `~/.claude/skills/`, each entry that is a symlink into `~/.agents/skills/<name>`. Claude Code supports symlinked skill folders and loads `SKILL.md` from the target ([skills docs](https://code.claude.com/docs/en/skills), "Symlinked folders"). The README in that folder documents this source ([`~/.claude/skills/README.md`](file:///Users/bloom/.claude/skills/README.md), "Sources" table).
- **Origin and version metadata**: `~/.agents/.skill-lock.json` (lock `version: 3`). Each skill records `source` (`mattpocock/skills`), `sourceType` (`github`), `sourceUrl`, `skillPath` (for example `skills/productivity/grilling/SKILL.md`), `skillFolderHash`, `installedAt`, and `updatedAt`. The CLI's own source defines `skillFolderHash` as the "GitHub tree SHA for the entire skill folder. This hash changes when ANY file in the skill folder changes", fetched through the GitHub Trees API ([vercel-labs/skills `src/skill-lock.ts` @a80e4c9](https://github.com/vercel-labs/skills/blob/a80e4c9d12d607631249d4d7d059f835d4b2f13a/src/skill-lock.ts)).
- **Upstream change source**: the GitHub repository. One call returns every folder's tree SHA: `gh api repos/mattpocock/skills/git/trees/HEAD?recursive=1`. The CLI uses the same method ("ONE API call to get the entire repo tree, then extracts the SHA for the specific skill folder", same file). The CLI also has `npx skills check` and `npx skills update` ([vercel-labs/skills README](https://github.com/vercel-labs/skills#other-commands)), but the CLI sends telemetry and runs through npx, so the script should call the Trees API itself. Releases also exist (latest `v1.3.1`, 2026-10-04, from `gh api repos/mattpocock/skills/releases`).
- **Check result on 2026-10-20**: of 26 locked skills, 9 have the same tree SHA as upstream and 16 have changed upstream. `resolving-merge-conflicts` no longer exists upstream; the last commit on its path is `daa01d8` "Remove resolving-merge-conflicts" (2026-09-24). 54 commits have landed since the install on 2026-09-29.
- **Local edits**: a local git tree hash of each `~/.agents/skills/<name>` folder, compared with `skillFolderHash`, shows whether the installed copy was edited. Only `code-review` differs. It is linked as `pocock-review` and its `SKILL.md` says `name: pocock-review`. `npx skills update` would overwrite this edit. The README warns about this ("Any edit made here is lost on the next update"). Method: copy the folders into a temporary git repository, commit, and run `git rev-parse HEAD:<name>`. This works offline.
- **Changed since last Retro**: `gh api "repos/mattpocock/skills/commits?since=<RetroTimestamp>&path=<skill dir>"`. Run it only for skills whose tree SHA differs, so the LLM reads only the relevant commit messages.

### 2. Skills copied by hand (michael-denyer/pstack-claude)

- **Enumerate**: real directories in `~/.claude/skills/` that are not symlinks and are not `synced/`: `blast-radius`, `bro`, `correct`, `principles`, `technical-writing`, `unslop`.
- **Origin and version metadata**: no file on disk records it. The `SKILL.md` frontmatter has only `name`, `description`, and sometimes `disable-model-invocation`. The only record is the README ("Copied by hand on 2026-10-05 from commit `0389988`", with a per-skill "Changes from upstream" column). Claude Code defines no `version` field for skills. The closest field is `metadata`, a "free-form YAML map … read by your own tooling" ([skills docs](https://code.claude.com/docs/en/skills), frontmatter reference).
- **Upstream change source**: the GitHub repository. Upstream skills now live at `plugins/pstack/skills/<name>`. The repository also has a `VERSION` file (now `0.9.94`), a `CHANGES.md`, and releases (latest `v0.9.93`, 2026-10-18). `gh api repos/michael-denyer/pstack-claude/compare/0389988...HEAD` returns `ahead_by: 63` and the changed files. Filtered to the copied skills, upstream changed `blast-radius`, `correct`, `technical-writing`, `unslop`, and 12 of the 13 merged `principle-*` sources. It also added principles that were not migrated, such as `principle-guard-the-context-window`.
- **Changed since last Retro**: the same compare or commits call with `since=<RetroTimestamp>`. Upstream changes do not apply directly, because each copy carries local edits. The Retro should surface them as "upstream changed X; your copy diverges by Y" and let the user decide.
- **Recommendation**: record the base commit per skill in machine-readable form, for example `metadata: {upstream: michael-denyer/pstack-claude, path: plugins/pstack/skills/unslop, base: 0389988}` in each `SKILL.md`. Claude Code ignores `metadata`, so this is safe. Today the base commit exists only in prose.

### 3. Skills synced from claude.ai

- **Enumerate**: `~/.claude/skills/synced/<uuid>_<uuid>/manifest.json` lists 13 skills with `skillId`, `name`, `description`, `source` (`anthropic` or `anthropic-example`), `updatedAt`, and sometimes `creatorType`. The file also has a top-level `lastUpdated` (epoch ms). Claude Code rewrites the folder; it also holds a `.last-complete-round` marker. The docs list "claude.ai account" as a skill location ("skills enabled for your claude.ai account … load in … terminal sessions where you sign in with that account", [skills docs](https://code.claude.com/docs/en/skills)). The on-disk layout is not documented, so treat it as observed behavior that can change. In sessions these skills appear as `anthropic-skills:<name>`, for example `anthropic-skills:docs` in `~/.claude.json` → `skillUsage`.
- **Upstream change source**: claude.ai manages them, and the user does not edit them (README). The `source: anthropic` skills (`pdf`, `docx`, `xlsx`, `pptx`) and `skill-creator` also appear in the public repository [anthropics/skills](https://github.com/anthropics/skills/tree/main/skills). The `anthropic-example` ones, such as `docs`, `morning`, and `computer-use`, have no public upstream.
- **Changed since last Retro**: per-skill `updatedAt` > Retro Timestamp. No network call is needed. Recent examples: `google-workspace` 2026-10-14 and `computer-use` 2026-10-08.

### 4. Project-scoped skills (OpenSpec)

- **Enumerate**: `<repo>/.claude/skills/*/SKILL.md`, plus `<repo>/.claude/commands/opsx/*.md`. Project skills load only in that repository ([skills docs](https://code.claude.com/docs/en/skills)). Repositories to scan: the paths that Claude Code knows, from `~/.claude.json` → `projects` keys and `githubRepoPaths`. On this machine: `~/workspace/mirador` and `~/workspace/stealth`, 8 `openspec-*` skills each.
- **Version metadata**: `SKILL.md` frontmatter `metadata.generatedBy` holds the OpenSpec CLI version that generated the file. mirador has `"1.14.0"`, stealth has `"1.14.1"`, and the installed CLI is 1.14.2. Both repositories are therefore stale. The README says to run `openspec update` "to regenerate them after a CLI upgrade".
- **Changed since last Retro**: compare `generatedBy` with `openspec --version`. The check is stateless and needs no network.

### 5. Plugins and marketplaces

- **Enumerate**: `claude plugin list --json` returns one object per install with `id`, `version`, `scope`, `enabled`, `installPath`, `installedAt`, and `lastUpdated`. With `--available`, it also lists what the marketplaces offer, including entry `version` ([plugin CLI reference](https://code.claude.com/docs/en/plugins/cli-reference), "plugin list" → "JSON output"). `claude plugin marketplace list --json` returns `name`, `source`, `repo`, and `installLocation` (same page). The raw records are `~/.claude/plugins/installed_plugins.json` (`scope`, `installPath`, `version`, plus `gitCommitSha` on disk) and `known_marketplaces.json` (`source`, `installLocation`, `lastUpdated`, `autoUpdate`) ([plugin loading reference](https://code.claude.com/docs/en/plugins/loading), "Check which stage a plugin reached"). Settings declare intent in `enabledPlugins` and `extraKnownMarketplaces` (same page). Cache layout: `cache/<marketplace>/<plugin>/<version>/`, and marketplace clones are in `marketplaces/<name>/` (same page, "Find plugins on disk").
- **How the version is resolved**: the manifest `version` wins, then the marketplace entry `version`. If neither is set, a github or url source uses a 12-character commit SHA. "A manifest that pins `"version": "1.0.0"` keeps every user on the cached copy until its author changes the string, however many commits they push" ([plugin loading reference](https://code.claude.com/docs/en/plugins/loading), "How Claude Code computes the version"; also the `version` field in the [manifest reference](https://code.claude.com/docs/en/plugins-reference)).
- **Auto-update defaults**: on for Anthropic's official marketplaces such as `claude-plugins-official`, and "off for every other marketplace". An `autoUpdate` value in `extraKnownMarketplaces` or `known_marketplaces.json` overrides the default. `DISABLE_AUTOUPDATER=1` turns the whole pass off unless `FORCE_AUTOUPDATE_PLUGINS=1` is also set (same page, "Which marketplaces and plugins auto-update").
- **Upstream change source**: the marketplace's git repository (`repo` in `known_marketplaces.json`), and the plugin's own repository when its source points elsewhere. For a version-pinned plugin, read `version` in upstream `.claude-plugin/plugin.json`. For an unpinned plugin, compare commit SHAs. Releases and tags are optional extras.
- **Check result on 2026-10-20**: `ponytail@ponytail` is installed at `4.13.0` (commit `b9a1051`). Upstream `plugin.json` is now `5.3.2`, release `v5.3.2` was published 2026-10-16, and the repository is 53 commits ahead. The ponytail marketplace is third-party with no `autoUpdate` set, so it never auto-updated. Its `lastUpdated` is 2026-10-05, while `claude-plugins-official` refreshed on 2026-10-20. The official marketplace directory is a download, not a git clone. Its `.gcs-sha` file (`a0b04d9…`) matches the HEAD commit of `anthropics/claude-plugins-official`, so it can serve as that marketplace's version.
- **Changed since last Retro**: locally, `installedAt` or `lastUpdated` > Retro Timestamp. Upstream: the version or SHA comparison above, then `commits?since=` or releases filtered by `published_at` to scope the changelog.
- **Built-in plugins**: `~/.claude.json` → `pluginUsage` also shows `@builtin` ids (`cc-plugin-diff`, `agents-md`, `telemetry`, `cc-plugin-plugin-authoring`). They ship with the Claude Code binary, so the Claude Code changelog covers them (section 7). Observed, not documented.

### 6. MCP servers

- **Enumerate**: `claude mcp list`, which also runs a health check per server ([MCP docs](https://code.claude.com/docs/en/mcp), "Listing and inspecting servers"). Without the network, read the scope files: local scope is `~/.claude.json` under `projects.<path>.mcpServers`, user scope is `~/.claude.json` → `mcpServers`, and project scope is `.mcp.json` at the repository root. Plugin servers come from the plugin's `.mcp.json` or `plugin.json`, and claude.ai connectors appear automatically when the user signs in with claude.ai (same page, scope table and precedence list). `claude plugin list --json` includes `mcpServers` per plugin ([plugin CLI reference](https://code.claude.com/docs/en/plugins/cli-reference)).
- **On this machine**: there are no local, project, or user servers. `mcpServers` is empty in `~/.claude.json` and in every project, and `~/workspace` has no `.mcp.json`. The installed plugin declares no MCP servers. The only servers are 4 claude.ai connectors, all connected: Claude Docs, Google Drive, Google Calendar, and Gmail.
- **Version metadata**: none in config. A stdio server's version is the package it launches, so treat it like the CLIs in section 7 (npm or brew). Remote connectors are run by their vendor and have no version that can be tracked.
- **Changed since last Retro**: for remote connectors, only additions and removals, which need a stored list. For stdio servers, use the package registry. Low value for this user today.

### 7. CLIs (watch list)

| CLI | Install source | Installed version | Upstream / change source | Cheap check |
|---|---|---|---|---|
| `openspec` | npm global under nvm (`~/.nvm/versions/node/v24.21.0`) | 1.14.2 | npm `@fission-ai/openspec` (latest 1.14.3, 2026-10-17); [Fission-AI/OpenSpec](https://github.com/Fission-AI/OpenSpec) releases and `CHANGELOG.md` | `npm outdated -g --json` (`current`/`latest`); `npm view <pkg> time --json` gives per-version publish dates to filter by Retro Timestamp |
| `gh` | Homebrew formula | 2.101.0 | Homebrew `gh` 2.102.0; [cli/cli releases](https://github.com/cli/cli/releases) (v2.102.0, 2026-09-30) | `brew outdated --json=v2` (uses the local formula index, so its accuracy depends on the last `brew update`) |
| `claude` | native installer (`~/.claude.json` → `installMethod: "native"`, `autoUpdates: false`) | 2.1.304 | [anthropics/claude-code CHANGELOG.md](https://github.com/anthropics/claude-code/blob/main/CHANGELOG.md); npm `@anthropic-ai/claude-code` `time` map (2.1.304 published 2026-10-19) | `~/.claude/cache/changelog.md` is a local copy of the changelog that Claude Code fetches (`changelogLastFetched` in `~/.claude.json`), and `lastReleaseNotesSeen` (`2.1.304`) records what the user has seen. Changelog headings have no dates, so use npm `time` to map versions to dates |

`npm outdated -g` also flags `npm` itself (11.19.0 → 12.2.0), and `brew outdated` lists 25 formulae. The map's watch list decides which of these to report.

## Cheapest Retro procedure (for the script)

1. **Inventory, local only**: read `~/.agents/.skill-lock.json`, the symlink targets in `~/.claude/skills`, the synced `manifest.json`, `claude plugin list --json`, `claude plugin marketplace list --json`, the MCP scope files, and project `.claude/skills/*/SKILL.md` `metadata.generatedBy`. Detect local edits by comparing git tree hashes.
2. **Upstream, about 6 network calls**: one recursive Trees API call each for `mattpocock/skills`, `michael-denyer/pstack-claude` (or a compare from the base commit), and each plugin marketplace repository; plus `npm outdated -g --json`, `brew outdated --json=v2`, and `npm view @anthropic-ai/claude-code time --json`. `gh` is authenticated, which allows 5,000 requests per hour (`gh api rate_limit`).
3. **Scope to the Window**: for items that are behind, fetch only the commits or releases after the Retro Timestamp, and give their messages or notes to the LLM to judge. Items that are not behind cost no tokens.

## Overlapping skills (input for problem category 9)

`~/.claude.json` → `skillUsage` holds a lifetime `usageCount` and `lastUsedAt` (epoch ms) for each skill, keyed by invocation name (`pocock-review`, `anthropic-skills:docs`, `opsx:apply`, `ponytail:ponytail`). This is a cheap local signal for unused or duplicate skills (categories 3 and 9). It is observed, not documented, and it counts invocations, not each time a skill is read. Skills with no entry have no recorded invocation, for example `grill-me`, `diagnosing-bugs`, `blast-radius`, `principles`, `correct`, `to-spec`, and `to-tickets`.

- **grill-me / grill-with-docs / grilling** (all mattpocock). `grill-me` and `grill-with-docs` are manual only and describe the same interview; `grill-with-docs` also writes ADRs and glossary entries. `grilling` is the auto-invoked form. Lifetime usage in `~/.claude.json` → `skillUsage`: `grilling` 20, `grill-with-docs` 1, `grill-me` 0.
- **Code review**: `pocock-review` (mattpocock `code-review`, renamed locally; used 9 times), the bundled `/code-review` (8) and `/simplify` (0), and `ponytail-review` (over-engineering only; 5). The official marketplace also offers `code-review` and `pr-review-toolkit` plugins, which are not installed.
- **Laziness / YAGNI**: the `ponytail` plugin (auto-invoked on every coding task, plus hooks) overlaps with `principles` → `laziness-protocol`. `ponytail-audit` overlaps with `improve-codebase-architecture`.
- **Research**: `research` (mattpocock) and `anthropic-skills:deep-research` (synced).
- **Writing skills**: `writing-for-agents` (mattpocock) and `anthropic-skills:skill-creator` (synced).
- **Prose**: `technical-writing` applies `unslop` on purpose. They are layered, not duplicates.
- **Planning**: `wayfinder` / `to-spec` / `to-tickets` (personal) and the per-repository `openspec-propose` / `openspec-explore`. The README already chose to skip pstack's `swarm` and `poteto-mode` "because they compete with OpenSpec".

## Drift found along the way

- `wait-what` is installed and locked in `~/.agents/skills` but has no symlink in `~/.claude/skills`, so it never loads. The README does not mention it.
- The README says OpenSpec is 1.14.0. The CLI is 1.14.2, and the projects were generated by 1.14.0 and 1.14.1.
- The README lists 6 OpenSpec skills. Both repositories now have 8 (`openspec-onboard` and `openspec-verify-change` were added).
- `resolving-merge-conflicts` is removed upstream but still installed and listed.

## Open points for the spec

- **Removals and connector changes need a list from the last Retro.** Option: the Findings file includes a short inventory appendix (names and pins), which fits the rule that only the Retro Timestamp and the previous Findings are stored. Otherwise, the Retro reports only additions and "behind upstream".
- **pstack provenance is prose only.** Adding `metadata.upstream/base` to those six `SKILL.md` files would make them as checkable as the locked skills.
- **Undocumented layouts**: `skills/synced/*/manifest.json`, `@builtin` plugin ids, and `.gcs-sha` were observed, not documented. The script should tolerate their absence.

## Appendix: current inventory (2026-10-20)

**Personal skills, `skills` CLI from mattpocock/skills (25 linked, plus 1 unlinked)**: ask-matt, codebase-design, diagnosing-bugs, domain-modeling, git-guardrails-claude-code, grill-me, grill-with-docs, grilling, handoff, implement, improve-codebase-architecture, pocock-review (→ `code-review`, locally edited), prototype, research, resolving-merge-conflicts (removed upstream), setup-matt-pocock-skills, tdd, teach, to-questionnaire, to-spec, to-tickets, triage, wayfinder, wizard, writing-for-agents. Unlinked: wait-what.

**Personal skills, copied by hand from michael-denyer/pstack-claude @0389988 (6)**: blast-radius, bro, correct, principles, technical-writing, unslop.

**claude.ai synced skills (13)**, source in parentheses: built-in-browser (anthropic-example), chrome-browser (anthropic-example), computer-use (anthropic-example), deep-research (anthropic-example), docs (anthropic-example), docx (anthropic), google-workspace (anthropic-example), import-memory (anthropic-example), morning (anthropic-example), pdf (anthropic), pptx (anthropic), skill-creator (anthropic-example), xlsx (anthropic).

**Project skills (OpenSpec, generated by `openspec init`/`update`)**: in `~/workspace/mirador` (generatedBy 1.14.0) and `~/workspace/stealth` (1.14.1): openspec-apply-change, openspec-archive-change, openspec-explore, openspec-onboard, openspec-propose, openspec-sync-specs, openspec-update-change, openspec-verify-change; plus `/opsx:*` commands.

**Plugins**: `ponytail@ponytail` 4.13.0, user scope, enabled (marketplace `DietrichGebert/ponytail`; upstream 5.3.2). Skills: ponytail, ponytail-audit, ponytail-debt, ponytail-gain, ponytail-help, ponytail-review. Hooks: SessionStart, SubagentStart, UserPromptSubmit, and others. Built-in plugins seen in usage records: agents-md, telemetry, cc-plugin-diff, cc-plugin-plugin-authoring (all `@builtin`).

**Marketplaces**: `claude-plugins-official` (anthropics/claude-plugins-official, auto-update on by default, snapshot `a0b04d9`), `ponytail` (DietrichGebert/ponytail, auto-update off). claude.ai also lists `anthropic-plugin-directory` (`~/.claude/plugins/synced/*/.marketplaces.json`), which is not added locally.

**MCP servers**: claude.ai connectors only: Claude Docs, Google Drive, Google Calendar, Gmail. No local, project, user, or plugin servers.

**CLIs**: openspec 1.14.2 (npm, latest 1.14.3); gh 2.101.0 (brew, latest 2.102.0); claude 2.1.304 (native, current). Other brew formulae installed on request: ffmpeg, postgresql@17, railway, sherlock, yt-dlp.
