# 11: CLIs

**What to build:** The Retro knows which installed CLIs the user relied on in the Window and which are outdated, and reports the unused outdated ones at zero tokens.

Details: [spec](../spec.md), section "Toolkit inventory and upstream"; [watch list ticket](../wayfinder-issues/14-watch-list.md).

**Blocked by:** 10: Upstream for skills, plugins and Claude Code

**Status:** done

- [x] Installed CLIs come from brew packages installed on request plus global npm packages. `claude` always counts.
- [x] Use in the Window: the first word of each Bash command is resolved through `which` and `realpath` to a Homebrew Cellar formula or a global npm package. Anything else is ignored. One use counts.
- [x] Outdated status comes from `brew outdated --json=v2` and `npm outdated -g --json`.
- [x] A CLI that was used and is outdated becomes a Toolkit update (its changelog is read in ticket 15). An unused outdated CLI gets one script line, such as `go 1.27.1 → 1.27.3 · not used this Window`, at zero tokens.
- [x] No uninstall prompt for unused CLIs.
- [x] The installed CLI names are kept in the temp folder for the news filter.
- [x] Verify: `/retro redo`. `psql` maps to `postgresql@17`, `pnpm` to `corepack`, and dependencies such as `openssl@3` are absent.
