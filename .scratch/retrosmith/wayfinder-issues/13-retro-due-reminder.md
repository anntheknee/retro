# Retro due reminder

Type: grilling
Status: resolved
Assignee: me
Blocked by:

## Question

How does the user learn that a Retro is due? `cleanupPeriodDays` is now 30 and Retros are monthly, so transcripts expire on the Retro's own cycle. Per [Script vs. skill boundary and subagent fan-out](07-script-vs-skill-boundary-and-fan-out.md), the gate is 30 days since the Retro Timestamp and the Window is always the last 30 days. A late Retro leaves an unanalyzed gap, so the reminder should fire when the Retro becomes due (day 30), or a few days before as a heads-up.

The user leans toward a segment in the existing statusline, `~/.claude/context-statusline.sh` (for example `· retro due (27d)`). It would read the Retro Timestamp from the frontmatter of `~/.claude/retro/findings.md`. The alternatives are a SessionStart hook or a launchd notification.

Still to decide:
- the day it fires;
- what it shows before the first Retro, when no timestamp exists (the first-run gate is the oldest `history.jsonl` entry being 30+ days old);
- whether a reminder conflicts with the out-of-scope line "a recorder or hooks of our own", which was written about recording.

See [Relationship to built-in insights tools](11-relationship-to-built-in-insights-tools.md).

Note from [Quota-aware automatic runs](12-quota-aware-automatic-runs.md) (ruled out of scope): automatic runs are out of v1, so this reminder is the only protection against a late Retro. Decide whether it also shows leftover quota, e.g. `retro due · weekly 38%, resets 11h`, so the user can pick a good time to run `/retro`. In the statusline it could come from `rate_limits` in the JSON input. Elsewhere it could come from `claude -p "/usage"` at zero tokens.

## Answer

- **Mechanism**: a segment in the existing statusline (`~/.claude/context-statusline.sh`). No hook, no launchd job.
- **Logic**: a fourth subcommand, `retro.py status`, reads the Retro Timestamp from the frontmatter of `~/.claude/retro/findings.md` and applies the gate's 30-day rule. It prints the segment or nothing, so the frontmatter format and the 30 live only in `retro.py`.
- **What it shows**: nothing before day 30; `retro due` on day 30; then `retro overdue · Nd lost`, orange for 1 to 6 days lost and red from 7. Each lost day is a day no Window covers.
- **Before the first Retro** (no findings file): `retro due`. If that's wrong (under 30 days of history), the `prepare` gate still refuses the run at zero tokens.
- **No quota display.** A usage-limit pause mid-Retro is already recoverable, and `prepare` prints a `/usage` line.
- **Wiring**: on every `/retro` run, above or below the gate, `prepare` checks `statusLine` in `~/.claude/settings.json` (and the script it names) for `retro.py status`. If it's missing, `prepare` prints a hint, and `SKILL.md` has Claude offer the edit as its last step:
  - script: append one call, joined to the existing output with ` · `;
  - inline command: append `; ~/.claude/skills/retro/retro.py status`;
  - none: set `statusLine` to `~/.claude/skills/retro/retro.py status`.
  Claude makes the edit with its normal tools after a yes. `retro.py` contains no installer code. A decline isn't stored, so the offer returns next run.
- **Scope**: the Out of scope line now reads "A recorder of our own (via hooks or otherwise)". Displaying a reminder records nothing.

