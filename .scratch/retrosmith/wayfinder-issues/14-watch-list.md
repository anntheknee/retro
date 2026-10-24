# Watch list

Type: grilling
Status: resolved
Assignee: me
Blocked by:

## Question

What is the watch list, where does it live, and what format is it in? Per the map's Notes, Toolkit CLIs come from Bash usage in the Window plus the watch list, and each Retro suggests watch-list changes as Findings. Per [Toolkit inventory and upstream sources](03-toolkit-inventory-and-upstream-sources.md), `npm outdated -g` and `brew outdated` flag far more than the user cares about (npm itself, 25 brew formulae), so the watch list decides which to report. Per [AI landscape sources](04-ai-landscape-sources.md), its names also feed the news-filter term list.

Settle the tension with "stores nothing of the user's except the Retro Timestamp and the previous Findings": is the watch list an exception (config the user keeps, e.g. a file beside `retro.py` or under `~/.claude/retro/`), or does it live inside `~/.claude/retro/findings.md`, rewritten by each Retro? Also decide:
- what an entry holds: just a name, or a name plus its upstream source;
- whether it lists only CLIs or any Toolkit item that isn't seen in the Window;
- how an accepted watch-list-change Finding gets applied, since there's no walkthrough and the user applies Findings later by asking Claude;
- whether a CLI used in the Window but missing from the list is reported anyway.

## Answer

- **No watch list.** Nothing new is stored, there are no watch-list-change Findings, and nothing needs applying. The "stores nothing except the Retro Timestamp and the previous Findings" rule holds.
- **Installed CLIs**: `brew leaves --installed-on-request` plus `npm ls -g --depth=0`, both local and free. Dependencies (`gcc`, `openssl@3`, `x265`, …) drop out. Today: ffmpeg, gh, go, postgresql@17, railway, sherlock, yt-dlp; @fission-ai/openspec, corepack, npm. `claude` always counts.
- **Used in the Window**: `retro.py` takes the first word of each Bash command, resolves it with `which` + `realpath`, and maps the path to its package: a Homebrew Cellar path gives the formula (`psql` → `postgresql@17`), the npm global `node_modules` gives the package (`pnpm` → `corepack`). Anything else is ignored: system tools, heredoc noise, and installs outside brew and npm (TeX Live's `pdflatex`, curl, pipx, cargo). No usage threshold: one use counts.
- **Two tiers in Toolkit updates**, from `brew outdated --json=v2` and `npm outdated -g --json`:
  - used and outdated: the Phase 2 web agent reads the changelog and judges it against the problem list (today 5: gh, railway, ffmpeg, openspec, npm);
  - installed, unused and outdated: one line the script writes at zero tokens, e.g. `go 1.27.1 → 1.27.3 · not used this Window`. Its changelog is read only when a Finding or matched news item already names the tool.
- **No uninstall prompt** for unused CLIs: 30 days unused is weak evidence for occasional tools.
- **News filter** ([AI landscape sources](04-ai-landscape-sources.md)): the term list uses all installed CLI names in place of watch-list names, so news about an unused tool still matches.
