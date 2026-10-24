# Token budget and cost guardrails

Type: grilling
Status: resolved
Assignee: me
Blocked by: 02, 07

## Question

What is the spending cap for one Retro, if any, and how is it enforced: a cap on subagent count, digest size limits, or a confirmation before fan-out? How does the Retro measure and report its own cost (it can read its own transcript's `usage`)?

Note from [Relationship to built-in insights tools](11-relationship-to-built-in-insights-tools.md): the Retro runs on Opus (fixed). Every Retro also runs `/insights`, which costs about $0.69 at list price, mostly fixed overhead; its `total_cost_usd` is reported in the JSON and belongs in the cost report.

Note from [Script vs. skill boundary and subagent fan-out](07-script-vs-skill-boundary-and-fan-out.md): the spend comes from three Opus phase-1 agents, the Opus main session (merge, `/insights` review, linking, walkthrough), one Sonnet web agent working from ~5 problems, and `retro.py context` calls (one turn each). The script and feed filtering cost nothing.

## Answer

- **No spending cap and no cost report.** The user doesn't care about a Retro's cost, so there's no USD, token, or plan cap, no `--max-budget-usd` on `/insights`, and no cost section. The map's standing preference keeps only "the script does the heavy lifting, the LLM only judges".
- **Plan usage line**: `prepare` runs `claude -p "/usage"` (zero tokens) and prints one line, e.g. "session 72%, weekly 40%, resets 14:30". It has no threshold and never blocks.
- **Usage-limit hit**: the interactive Session pauses, and the user types "continue" after the reset; nothing auto-resumes. The temp folder survives because only `commit` deletes it. Claude re-runs only the agents that hit the limit, from the same input files. These aren't counted as failures.
- **Other agent failures** (crash, garbled output, timeout): Claude offers one re-run from the same input file, with approval. If the user declines, or the re-run fails, the existing rule applies: list it and continue.
- **100k-token cap per agent input** (estimated as bytes ÷ 4):
  - An input over the cap is split into ceil(size ÷ 100k) pieces of whole Sessions in time order, never cutting a Session. Each piece runs with the agent's same instructions.
  - Every B piece also gets the script's whole-Window repeat-candidate list, so repeats spanning pieces aren't lost. A split by project would separate them too, because repeated questions cross projects.
  - C (Toolkit table) is never split.
  - Measured on 2026-10-21: 141 Sessions in 30 days, ~100k tokens of prompts in total (~35k per agent), largest Session ~7k, median ~200. The cap won't trigger at current volume.
- **Reconcile agent**: each split group (e.g. B1 + B2) gets one Opus reconcile agent. It reads all pieces' drafts, merges overlaps, and combines their evidence before frequency thresholds apply (3 + 3 counts as 6). It then hands one set to the main merge. Rejected: merge-only in the main session, and pieces reviewing each other (doubles the reading).
- **Facts found while resolving**: `cost-state` is written only as a transcript's last line at process exit. It includes subagent and internal Haiku spend. Subagent transcripts carry no `cost-state`. This was moot once cost reporting was dropped, but it matters if cost is ever wanted again.
