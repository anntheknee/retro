# Findings file shape

Type: prototype
Status: resolved
Assignee: me
Blocked by: 01, 06

## Question

What does the findings file look like? Covers sections (follow-through on the previous Retro, findings per category, Toolkit updates, meta, cost), how a Finding cites evidence (Session title, project, `claude --resume <id>`), and how the walkthrough offers to apply each Finding. Also decide whether the file carries a short Toolkit inventory appendix: per [Toolkit inventory and upstream sources](03-toolkit-inventory-and-upstream-sources.md), it's the only way to detect removals without storing anything extra. Prototype it with real data from the current transcripts.

Note from [Relationship to built-in insights tools](11-relationship-to-built-in-insights-tools.md): each Finding records its origin (Retro, `/insights`, or web). The file records the `/insights` report date range and lists dropped `/insights` items once each, with the reason.

Note from [Script vs. skill boundary and subagent fan-out](07-script-vs-skill-boundary-and-fan-out.md): phase-1 agents return Findings in this file's Finding format, so define it as the agent contract too. The file also needs a Follow-through section (verdicts: worked, didn't work, not done, no longer relevant), solutions linked to problems, and a list of parts that failed (an agent, `/insights`, a feed). `commit` writes the file, so the LLM never edits the frontmatter.

Note from [Skill overlap and merge workflow](08-skill-overlap-and-merge-workflow.md): category 9 doesn't need the inventory appendix (removals and old habits are found without it), so only "removed upstream" and connector changes still argue for it. A merge-and-own Finding carries an outline and the sources to track, not the full `SKILL.md`, which the apply step writes. A declined overlap reappears labelled "previously declined".

Note from [Token budget and cost guardrails](09-token-budget-and-cost-guardrails.md): no cost section (drop "cost" from the sections above). The failed-parts list should say whether an agent was re-run (after a usage limit or on approval). Findings from a split agent arrive already merged by its reconcile agent.

## Answer

- **Sections**, in order: a header line (Sessions, projects, Finding count) → Failed parts (each one says whether it was re-run) → Follow-through → Findings (problems, ordered by weight across all categories, not grouped by category) → Toolkit updates → Meta → `/insights` review (its date range, confirm/merge/amend counts, and each dropped item once, with its reason). There is no cost section.
- **Finding layout**, which is also the contract for phase-1 agents (agents leave out the number, and the main session numbers Findings after merging):
  ```
  ### <n>. <category> · <project or "all"> · via <Retro | /insights | web>
  **Problem**: <one or two lines>
  **Solutions**:
  - **a.** <the exact change: file and edit, or command>. Fit: <…>. Adoption: <…>.
  - **b.** …
  ```
  - Up to 3 solutions per problem, each from the Toolkit or the web, with a short blurb on how well it fits and how widely it's adopted. Web solutions go inline in the problem's Finding, so there are no separate linked Findings.
  - Toolkit updates and Meta items have no problem behind them. They use **What changed** in place of **Problem**.
  - A merge-and-own solution carries the outline and the sources to track, not the full `SKILL.md`.
  - Each solution must be self-contained, because a later, separate Session applies it.
- **Numbers** (1…n) exist only for readability and for referring to a Finding ("apply 3b"). Nothing carries them across Retros.
- **No evidence lines.** Agents use evidence to reach a verdict, but the file doesn't cite Sessions. The user judges relevance by adopting a Finding or not.
- **No status.** Findings are never marked applied, declined or open.
- **Follow-through** is a table: a short summary of last month's fix → worked / didn't work / not adopted / no longer relevant, judged from what actually changed (settings, installs, usage, whether the problem came back). A Finding that wasn't adopted comes back only if the problem got worse. An overlap comes back every Retro while it still exists, labelled "raised before".
- **No walkthrough.** `commit` writes `~/.claude/retro/findings.md`, prints the path and runs `open` on it. The user picks the app once: VS Code, with `workbench.editorAssociations` `{"**/.claude/retro/*.md": "vscode.markdown.preview.editor"}` for a rendered view. Chrome doesn't render `.md`, and HTML stays out of scope. The user applies Findings later by telling Claude.
- **No Toolkit inventory list.** Removals upstream are caught by the per-repo compare. Unused installs are caught by agent C's usage table (categories 3 and 9). Detecting claude.ai connector additions or removals is out of scope.

Prototype: [findings file](../prototypes/10-findings-file.PROTOTYPE.md). It came before these decisions: drop its evidence lines, status, `F` ids, "you said" column and the Meta "Linked to" Finding.
