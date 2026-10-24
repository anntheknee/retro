# Retro state and lifecycle

Type: grilling
Status: resolved
Assignee: me
Blocked by:

## Question

Where do the Retro Timestamp and the previous Findings file live? How does a Retro exclude its own Session from the next Window? What does the first Retro do with no Retro Timestamp (the whole 90 days?)? What happens if a Retro is aborted partway: is the Retro Timestamp advanced at the start, at the end, or only when the Findings are written?

## Answer

- **State**: one file, `~/.claude/retro/findings.md`. The Retro Timestamp is in its frontmatter, and each Retro overwrites the file. It lives outside the repo, so it works however the skill is installed (repo symlink, a skills repo, or no repo). The state is per machine, the same as the transcripts.
- **Window**: all Session activity after the Retro Timestamp, filtered message by message. A resumed Session that straddles a Retro contributes only its later part, so nothing is judged twice.
- **First Retro**: with no timestamp, the Window covers every transcript on disk (30 days today, at most 90 with `cleanupPeriodDays`). `history.jsonl` is trimmed to the same start.
- **Lifecycle**: the timestamp is captured when the Retro starts, which is where the Window ends. It is written atomically with the Findings once they are produced, before the walkthrough. An abort before that changes nothing, and the next run covers the same Window plus whatever came after.
- **Finding status**: `applied`, `declined`, or `open`, marked in place during the walkthrough. A Finding nobody answered stays `open`. The file holds only one Retro, so it stays small.
- **Gate**: a Retro needs at least ~150 typed prompts in its Window. Slash commands don't count, and neither does anything after `/retro` in the Retro's own Session. The 150 is about a typical week of current use (758 prompts in the last 30 days, a median of 17 per active day). It is a script constant. Below the threshold the Retro does nothing: it prints progress ("84 of 150 prompts since the last Retro"), costs zero tokens, and leaves the timestamp in place. There is no force option.
- **Own Session**: in any Session where `/retro` was invoked, everything from that prompt onward is skipped, subagent transcripts included. This is detected from the transcript, so nothing is stored, and headless or aborted Retros are caught too. The walkthrough ends by suggesting a fresh Session.

Superseded in part by [Script vs. skill boundary and subagent fan-out](07-script-vs-skill-boundary-and-fan-out.md): the gate is now 30 days since the Retro Timestamp (first Retro: the oldest `history.jsonl` entry is 30+ days old), not ~150 prompts. The Window is the 30 days before the Retro starts. The rest stands.

Superseded in part by [Findings file shape](10-findings-file-shape.md): Findings have no status and there is no walkthrough. `commit` writes the file and opens it, and the timestamp still advances at `commit`.

Superseded in part by [Testing the skill](15-testing-the-skill.md): `/retro redo` skips the gate and replaces the latest Retro, and `commit` keeps the previous Findings as `findings.prev.md` so a Redo has a follow-through baseline.
