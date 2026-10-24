# 01: Skeleton: gate, Redo, commit

**What to build:** Typing `/retro` either stops at the gate, at zero tokens, with the days left, or runs a Retro that writes and opens a findings file with the fixed section headings and no Findings yet. `/retro redo` skips the gate and replaces the latest Retro. This is the frame every later ticket fills in.

Details: [spec](../spec.md), sections "Form and install", "`retro.py` subcommands", "State", "Gate, Window, and cursor", "Redo".

**Blocked by:** None (can start immediately)

**Status:** done

- [x] The skill is a folder in this repo holding `SKILL.md` and `retro.py` (Python 3, stdlib only, `#!/usr/bin/env python3`), symlinked as the user's `retro` skill.
- [x] `/retro` has Claude run `prepare`. The user never runs a subcommand.
- [x] Gate: 30 days since the Retro Timestamp in the findings file's frontmatter. With no findings file, the first Retro runs once the oldest `history.jsonl` entry is 30 or more days old.
- [x] Below the gate, `prepare` prints the days left and Claude repeats it and stops. Nothing changes on disk.
- [x] Above the gate, `prepare` captures the Retro Timestamp at its start and creates a fresh temp folder, printing its path. It records in that folder whether this is a Redo and which timestamp `commit` must write.
- [x] `prepare` prints one plan-usage line from headless `/usage` (session %, weekly %, reset time), and Claude repeats it. It never blocks; if the call fails, the line says so.
- [x] `/retro redo` runs `prepare --redo`, which skips the gate.
- [x] `commit <draft>` on a normal Retro renames the findings file to the previous-findings file, then writes the new findings file atomically with the Retro Timestamp in its frontmatter. On a Redo it overwrites the findings file and leaves the previous-findings file alone.
- [x] `commit` deletes the temp folder, prints the file's path, and runs `open` on it. Claude never writes the frontmatter.
- [x] An abort before `commit` leaves the Retro Timestamp and both files unchanged.
- [x] The file has the header line and the sections in order: Failed parts, Follow-through, Findings, Toolkit updates, Meta, `/insights` review.
- [x] Verify: `/retro redo` (the first Retro, run early) opens the file. A following `/retro` refuses with the days left. A second `/retro redo` replaces the file without creating a previous-findings file.
