---
name: retro
description: Monthly self-review of how I use Claude Code. Use when the user types /retro or /retro redo.
---

# Retro

Run `retro.py` (beside this file) with Bash. The user never runs subcommands.

1. Run `retro.py prepare` (or `retro.py prepare --redo` if the user typed `/retro redo`).
2. Repeat its user-facing lines (the days-left refusal, or the plan-usage line) in your first message. If it printed days left, stop there.
3. Otherwise it printed a temp folder. Run `retro.py commit <temp folder>/draft.md`. Do not write frontmatter yourself.
4. Tell the user the findings file path it printed.
