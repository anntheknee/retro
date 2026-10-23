---
name: retro
description: Monthly self-review of how I use Claude Code. Use when the user types /retro or /retro redo.
---

# Retro

Run `retro.py` (beside this file) with Bash. The user never runs subcommands.

1. Run `retro.py prepare` (or `retro.py prepare --redo` if the user typed `/retro redo`).
2. Repeat its user-facing lines (the days-left refusal, or the plan-usage and format-drift lines) in your first message. If it printed days left, stop there, except for step 6.
3. Otherwise it printed a temp folder holding `metrics.json`, `digest.json` and `draft.md`. Read `metrics.json` and write Findings for context (2), cost (5) and permissions (7) under `## Findings` in `draft.md`, using this layout. The script flags candidates and writes no Finding; you judge each one. Skip a category with nothing worth saying.

   ```
   ### <n>. <category> · <project or "all"> · via Retro
   **Problem**: <one or two lines, with the numbers>
   **Solutions**:
   - **a.** <the exact change: file and edit, or command>. Fit: <…>. Adoption: <…>.
   ```

   Up to three self-contained solutions each. Order Findings by weight across categories, then number them from 1. No evidence lines, no status. For context, `instruction_files` entries with `over_limit` or growth may suggest `/doctor prompt-audit` (suggest it; don't run it). A permissions solution may point to the built-in `fewer-permission-prompts` skill. Deliberate denials (for example `railway`) stay denied.
4. Run `retro.py commit <temp folder>/draft.md`. Do not write frontmatter yourself; `commit` sets the Findings count.
5. Tell the user the findings file path it printed.
6. If `prepare` printed a statusline hint (on a refusal too), last of all offer the edit, and make it only after a yes (a decline isn't stored):
   - statusLine names a script: append `~/.claude/skills/retro/retro.py status`, joined to the existing output with ` · `;
   - statusLine is an inline command: append `; ~/.claude/skills/retro/retro.py status`;
   - no statusLine: set it to `~/.claude/skills/retro/retro.py status`.
