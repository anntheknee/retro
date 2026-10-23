---
name: retro
description: Monthly self-review of how I use Claude Code. Use when the user types /retro or /retro redo.
---

# Retro

Run `retro.py` (beside this file) with Bash. The user never runs subcommands.

1. Run `retro.py prepare` (or `retro.py prepare --redo` if the user typed `/retro redo`).
2. Repeat its user-facing lines (the days-left refusal, or the plan-usage line) in your first message. If it printed days left, stop there, except for step 5.
3. Otherwise it printed a temp folder. Run `retro.py commit <temp folder>/draft.md`. Do not write frontmatter yourself.
4. Tell the user the findings file path it printed.
5. If `prepare` printed a statusline hint (on a refusal too), last of all offer the edit, and make it only after a yes (a decline isn't stored):
   - statusLine names a script: append `~/.claude/skills/retro/retro.py status`, joined to the existing output with ` · `;
   - statusLine is an inline command: append `; ~/.claude/skills/retro/retro.py status`;
   - no statusLine: set it to `~/.claude/skills/retro/retro.py status`.
