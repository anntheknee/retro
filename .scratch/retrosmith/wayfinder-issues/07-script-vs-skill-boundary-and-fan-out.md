# Script vs. skill boundary and subagent fan-out

Type: grilling
Status: resolved
Assignee: me
Blocked by: 01, 05, 11

## Question

Exactly what does the helper script compute (digests, metrics, deterministic detections), and what do subagents judge? How is the work split across subagents: by problem category, by project, by Session chunk, plus separate web-scan agents? How does the main session merge their output into one set of Findings? What language is the script (bias: python3 stdlib, already installed)?

Note from [Relationship to built-in insights tools](11-relationship-to-built-in-insights-tools.md): the script also runs `claude -p "/insights"` in parallel with the digest and extracts four report sections. After the Retro reaches its own Findings, a review step gives each `/insights` item a verdict: confirm, merge, amend, or drop. Decide where that review runs (the main session or a subagent) and what it sees. The Retro runs on Opus. `/skill-doctor` is not called, because plugin and skill use comes from transcripts.

## Answer

- **Form**: the `/retro` skill is a folder holding `SKILL.md` (the steps Claude follows) and `retro.py` beside it. Claude runs the script with its Bash tool. The script costs no tokens. Claude spends tokens only on judgment.
- **Language**: Python 3, stdlib only, `#!/usr/bin/env python3` (Homebrew 3.13; `/usr/bin` has 3.9). Rejected: Node (nvm moves `node`), Bash + jq (unreadable at this size), Go (needs a build step).
- **Three subcommands**:
  - `prepare`: checks the gate. Below it, prints progress and the Retro stops at zero tokens. Otherwise captures the Retro Timestamp, builds the per-Session digest, computes metrics and the Toolkit inventory with upstream diffs, fetches and filters the feeds, starts `claude -p "/insights"` in the background, and writes each agent's input file into a fresh `mktemp -d` folder whose path it prints.
  - `context <session> <turn>`: prints one turn in full: the typed prompt, the end of Claude's previous reply, and the turn's tools and errors. Agents use it when the digest isn't enough and never read raw `.jsonl`, so only the script copes with the unstable format.
  - `commit <draft.md>`: writes `~/.claude/retro/findings.md` atomically with the Retro Timestamp in its frontmatter, then deletes the temp folder.
- **Script vs. Claude**: the script computes every number and flags rubric candidates (for example "3 Sessions ran past 2 failed corrections without `/clear`"), but writes no Finding. Claude writes every Finding, including those for the exact categories 2, 5 and 7, so all Findings go through one judge, dedupe and link path.
- **Gate and Window** (supersedes the gate in [Retro state and lifecycle](06-retro-state-and-lifecycle.md)):
  - The gate is 30 days since the Retro Timestamp. The ~150-prompt gate is dropped.
  - The first Retro runs once the oldest `history.jsonl` entry is 30+ days old. Transcripts would be unreliable here, because cleanup deletes them around day 30.
  - The Window is the 30 days before the Retro starts, filtered message by message. A late Retro leaves an unanalyzed gap, and no day is ever analyzed twice.
  - `cleanupPeriodDays` stays at 30, since it matches the Window.
  - There's no history command. The user opens `~/.claude/retro/findings.md`, which stays until the next Retro overwrites it.
- **Order**:
  1. `prepare`.
  2. **Phase 1**: three parallel Opus subagents. A covers prompting and rework (1, 6), B repetition and workflows (4, 8), C the Toolkit (3, 9). Each reads its own slice from the temp folder.
  3. The main session merges and dedupes, and writes Findings for 2, 5 and 7 from the script's metrics.
  4. `/insights` review in the main session: confirm, merge, amend or drop.
  5. **Problem list**: the ~5 most frequent problems. Each is searched even when a fix already exists in the Toolkit, to look for something better, because upgrading tools is a goal.
  6. **Phase 2**: one Sonnet web agent. It searches for solutions to the problem list, reads the changelogs of Toolkit items used in the Window, and reads AI-tooling news items that the script matched to the Toolkit or a problem. No search runs without a problem or a Toolkit item behind it.
  7. The main session links solutions to problems ("you keep hitting X; Y solves it").
  8. `commit`, then the walkthrough.
- **Follow-through**: each phase-1 agent checks the previous Findings in its own categories, and the main session checks 2, 5 and 7. An applied Finding passes if the change landed and the problem stopped recurring. A declined one is re-raised only if the problem got worse, labelled as previously declined. An open one is checked like an applied one. Verdicts: worked, didn't work, not done, no longer relevant.
- **Failures**: a failed agent, `/insights` run or feed is listed in the findings file, the Retro continues, and the timestamp advances. If every phase-1 agent fails, nothing is committed.
- **Left to other tickets**: the format agents return Findings in ([Findings file shape](10-findings-file-shape.md)) and spending caps ([Token budget and cost guardrails](09-token-budget-and-cost-guardrails.md)).

Superseded in part by [Findings file shape](10-findings-file-shape.md): step 8 is `commit`, which writes the file and opens it, with no walkthrough. Follow-through judges each previous Finding from what actually changed, because there's no status: worked, didn't work, not adopted, no longer relevant. A Finding that wasn't adopted comes back only if the problem got worse.
