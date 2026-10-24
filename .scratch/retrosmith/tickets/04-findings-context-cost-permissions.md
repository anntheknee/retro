# 04: Findings for context, cost and permissions

**What to build:** The first real Findings. The script computes the context, cost and permission metrics, and Claude writes Findings for categories 2, 5 and 7 in the Finding layout, ordered by weight and numbered.

Details: [spec](../spec.md), sections "Script vs. Claude", "Main session merge", "Findings file contract".

**Blocked by:** 03: Transcript parsing and digest

**Status:** done

- [x] Context metrics: peak and mean context per Session, compactions with their sizes, `/clear` and `/compact` counts, long Sessions, and candidate runs of corrections without `/clear`.
- [x] Context metrics also cover instruction files: CLAUDE.md files over 200 lines, and instruction files that changed or grew during the Window (a Finding suggests `/doctor prompt-audit`; it isn't called).
- [x] Cost metrics: deduped tokens and USD by Session, project, model, skill and effort, plus the cache hit ratio, turns heavy on cache writes, expensive subagents and fixed per-Session overhead.
- [x] Permission metrics: prompts the user had to answer, and rejections and denial kinds by tool and command head.
- [x] The script flags rubric candidates but writes no Finding. Claude writes every Finding.
- [x] The Finding layout below, from the findings-file prototype ticket. Each Finding has up to 3 self-contained solutions. A category 7 solution may point to the built-in `fewer-permission-prompts` skill.

  ```
  ### <n>. <category> · <project or "all"> · via <Retro | /insights | web>
  **Problem**: <one or two lines>
  **Solutions**:
  - **a.** <the exact change: file and edit, or command>. Fit: <…>. Adoption: <…>.
  - **b.** …
  ```

- [x] Findings are ordered by weight across categories, then numbered. No evidence lines and no status.
- [x] Verify: `/retro redo`. Spot-check one Session's token total by hand, and judge the Findings.
