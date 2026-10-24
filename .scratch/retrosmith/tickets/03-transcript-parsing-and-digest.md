# 03: Transcript parsing and digest

**What to build:** A Retro reads the Window's Sessions tolerantly and builds the compact per-Session digest that every later analysis uses. The header line shows real Session and project counts, and the user sees how many records couldn't be parsed.

Details: [spec](../spec.md), sections "Transcript parsing and digest" and "Gate, Window, and cursor". Field-level notes: [transcript signal catalog](../research/01-transcript-signal-catalog.md) and its digest prototype.

**Blocked by:** 02: Statusline reminder

**Status:** done

- [x] Reads every project's Session transcripts, the subagent transcripts with their `.meta.json`, and `history.jsonl` trimmed to the Window start.
- [x] Window: the 30 days before `prepare` starts, filtered message by message, so a resumed Session contributes only its activity inside the Window.
- [x] Any Session where `/retro` was typed is cut from that prompt onward, subagents included. Headless `-p` Sessions the Retro started are skipped. Nothing is stored for this.
- [x] Parsing is defensive: unknown types are ignored, missing fields are tolerated, and `version` is recorded per Session. Skipped or unknown records are counted and printed as "format drift: N records skipped", and Claude repeats the line.
- [x] Token usage counts only the last line per `requestId`.
- [x] Typed prompts exclude tool results, meta and compact-summary records, slash-command echoes, interrupt markers and non-human origins. The filter works on records without `promptSource` or `origin.kind`.
- [x] One digest object per Session (subagents get their own), with the fields the spec lists. Prompts are capped at 300 characters. Skill listings are hoisted to Window level. The digest is written to the temp folder.
- [x] The header line shows Sessions and projects.
- [x] Verify: `/retro redo`. The digest is roughly the research's size (about 300 KB per month), the drift count is plausible, and the Retro's own Session is absent.
