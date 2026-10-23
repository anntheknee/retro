---
name: retro
description: Monthly self-review of how I use Claude Code. Use when the user types /retro or /retro redo.
---

# Retro

Run `retro.py` (beside this file) with Bash. The user never runs subcommands.

1. Run `retro.py prepare` (or `retro.py prepare --redo` if the user typed `/retro redo`).
2. Repeat its user-facing lines (the days-left refusal, or the plan-usage and format-drift lines) in your first message. If it printed days left, stop there, except for step 6.
3. Otherwise it printed a temp folder holding `metrics.json`, `digest.json`, `agent_a.json` and `draft.md`. Start Agent A first (below), then read `metrics.json` and write Findings for context (2), cost (5) and permissions (7), using this layout. Merge A's Findings with yours under `## Findings` in `draft.md`: drop duplicates (same problem and fix; keep the better one), then number everything by weight. The script flags candidates and writes no Finding; you judge each one. Skip a category with nothing worth saying.

   ```
   ### <n>. <category> · <project or "all"> · via Retro
   **Problem**: <one or two lines, with the numbers>
   **Solutions**:
   - **a.** <the exact change: file and edit, or command>. Fit: <…>. Adoption: <…>.
   ```

   Up to three self-contained solutions each. Order Findings by weight across categories, then number them from 1. No evidence lines, no status. For context, `instruction_files` entries with `over_limit` or growth may suggest `/doctor prompt-audit` (suggest it; don't run it). A permissions solution may point to the built-in `fewer-permission-prompts` skill. Deliberate denials (for example `railway`) stay denied.
   **Agent A** (prompting quality (1) and rework (6)): spawn one subagent with `model: opus`. Tell it to read `<temp folder>/agent_a.json`, `~/.claude/skills/retro/rubric.md` (items P1-P12, plus C2, C3, C6 and C8 for rework) and nothing else, and to return only Findings in the layout above, with categories `prompting` and `rework`, no numbers, origin `via Retro`. `agent_a.json` holds each Session's typed prompts; turns with `flags` (interrupted, steered, edit_churn, error_loop) carry `prev_tail`, the end of Claude's previous reply. When the digest isn't enough it runs `~/.claude/skills/retro/retro.py context <session> <i> <temp folder>` for one turn. It never reads raw transcripts. Vague prompts count only when they led to rework or wasted reads. Fixes are exact: a CLAUDE.md line, a hook, a habit with the keystroke. Wait for Agent A's result before step 4; if it fails, say so under Failed parts and go on.
4. Run `retro.py commit <temp folder>/draft.md`. Do not write frontmatter yourself; `commit` sets the Findings count.
5. Tell the user the findings file path it printed.
6. If `prepare` printed a statusline hint (on a refusal too), last of all offer the edit, and make it only after a yes (a decline isn't stored):
   - statusLine names a script: append `~/.claude/skills/retro/retro.py status`, joined to the existing output with ` · `;
   - statusLine is an inline command: append `; ~/.claude/skills/retro/retro.py status`;
   - no statusLine: set it to `~/.claude/skills/retro/retro.py status`.
