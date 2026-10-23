---
name: retro
description: Monthly self-review of how I use Claude Code. Use when the user types /retro or /retro redo.
---

# Retro

Run `retro.py` (beside this file) with Bash. The user never runs subcommands.

1. Run `retro.py prepare` (or `retro.py prepare --redo` if the user typed `/retro redo`).
2. Repeat its user-facing lines (the days-left refusal, or the plan-usage and format-drift lines) in your first message. If it printed days left, stop there, except for step 6.
3. Otherwise it printed a temp folder holding `metrics.json`, `digest.json`, `agent_a.json`, `agent_b.json`, `agent_c.json` and `draft.md`. Start Agents A, B and C in parallel, in one message (below), then read `metrics.json` and write Findings for context (2), cost (5) and permissions (7), using this layout. Merge A's, B's and C's Findings with yours under `## Findings` in `draft.md`: drop duplicates (same problem and fix; keep the better one), then number everything by weight. The script flags candidates and writes no Finding; you judge each one. Skip a category with nothing worth saying.

   ```
   ### <n>. <category> · <project or "all"> · via Retro
   **Problem**: <one or two lines, with the numbers>
   **Solutions**:
   - **a.** <the exact change: file and edit, or command>. Fit: <…>. Adoption: <…>.
   ```

   Up to three self-contained solutions each. Order Findings by weight across categories, then number them from 1. No evidence lines, no status. For context, `instruction_files` entries with `over_limit` or growth may suggest `/doctor prompt-audit` (suggest it; don't run it). A permissions solution may point to the built-in `fewer-permission-prompts` skill. Deliberate denials (for example `railway`) stay denied.
   **Agent A** (prompting quality (1) and rework (6)): spawn one subagent with `model: opus`. Tell it to read `<temp folder>/agent_a.json`, `~/.claude/skills/retro/rubric.md` (items P1-P12, plus C2, C3, C6 and C8 for rework) and nothing else, and to return only Findings in the layout above, with categories `prompting` and `rework`, no numbers, origin `via Retro`. `agent_a.json` holds each Session's typed prompts; turns with `flags` (interrupted, steered, edit_churn, error_loop) carry `prev_tail`, the end of Claude's previous reply. When the digest isn't enough it runs `~/.claude/skills/retro/retro.py context <session> <i> <temp folder>` for one turn. It never reads raw transcripts. Vague prompts count only when they led to rework or wasted reads. Fixes are exact: a CLAUDE.md line, a hook, a habit with the keystroke. 
   **Agent B** (repeats (4) and workflows (8)): spawn one subagent with `model: opus`, in the same message as A and C. Tell it to read `<temp folder>/agent_b.json`, `~/.claude/skills/retro/rubric.md` (items W1-W8, plus C5 and C6) and nothing else, and to return only Findings in the layout above, with categories `repeats` and `workflows`, no numbers, origin `via Retro`. `agent_b.json` holds every typed prompt per Session plus the script's repeat candidates: `repeated_prompts`, `long_prompt_duplicates`, `similar_openings`, `similar_agent_prompts`, and Bash heads and tool sequences seen in 3+ Sessions. Candidates are leads, not proof: it confirms each against the prompts. A repeated question or correction is a `repeats` Finding whose fix is a CLAUDE.md line or a habit. A `workflows` Finding names the trigger and proposes the matching form: a skill (a procedure Claude follows when asked), a hook (must happen every time, no asking) or a subagent (the same worker spawned with the same instructions). A proposed skill meets the W8 bar: its name, its one-line description, the steps in outline, which steps are a script, and `disable-model-invocation: true` if it has side effects. It never reads raw transcripts.
   **Agent C** (unused skills (3)): spawn one subagent with `model: opus`, in the same message as A and B. Tell it to read `<temp folder>/agent_c.json`, `~/.claude/skills/retro/rubric.md` (items S1-S7) and nothing else, and to return only Findings in the layout above, with category `skills`, no numbers, origin `via Retro`. `agent_c.json` holds the Toolkit table (`items`: name, origin, auto, description, `uses` in the Window, `lifetime` count; `plugins`: used, unused or "hooks only, can't tell") and every typed prompt per Session. It never splits its input. It finds tasks the user did by hand or Claude improvised that an installed item's description clearly covers (S1), confirming each against the prompt. Zero uses alone is not a Finding. A fix names the skill and the exact habit: the slash name to type, or a description edit when auto-triggering missed. For a plugin with status `unused`, offer `claude plugin uninstall <id>`; for "hooks only, can't tell" or "unused, but ships hooks", say so and don't advise removal.
   Wait for all three results before step 4; if one fails, say so under Failed parts and go on.
4. Run `retro.py commit <temp folder>/draft.md`. Do not write frontmatter yourself; `commit` sets the Findings count.
5. Tell the user the findings file path it printed.
6. If `prepare` printed a statusline hint (on a refusal too), last of all offer the edit, and make it only after a yes (a decline isn't stored):
   - statusLine names a script: append `~/.claude/skills/retro/retro.py status`, joined to the existing output with ` · `;
   - statusLine is an inline command: append `; ~/.claude/skills/retro/retro.py status`;
   - no statusLine: set it to `~/.claude/skills/retro/retro.py status`.
