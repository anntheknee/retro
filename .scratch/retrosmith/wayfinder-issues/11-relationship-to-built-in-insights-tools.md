# Relationship to built-in insights tools

Type: grilling
Status: resolved
Assignee: me
Blocked by:

## Question

Claude Code already ships `/insights` (an HTML report of friction points across up to 200 recent sessions), `/skill-doctor` (skills never invoked), `/usage` (usage attributed to skills, subagents and MCP servers) and `/doctor prompt-audit` (stale or conflicting instruction files); see [Prompting and context best practices](05-prompting-and-context-best-practices.md). For each one, does a Retro call it, reuse its output, or deliberately duplicate it, and what does Retrosmith add that they don't? If they cover most of the categories, does the destination shrink?

## Answer

The destination doesn't shrink. A Retro still analyzes all nine categories itself. `/insights` is a **second opinion** that the Retro reviews, the way one agent reviews another's code.

- **`/insights`: run every Retro and review its output.**
  - The script starts `claude -p "/insights" --output-format json` at the start of each Retro, in parallel with the digest. It works headlessly with no permission flags.
  - One run cost $0.69 at list price and took about 1 minute. Most of that is fixed overhead, because `/insights` caches each Session's analysis in `~/.claude/usage-data/facets/`. Its `total_cost_usd` goes into the Retro's cost report.
  - The JSON `result` names the new timestamped report. The script extracts four sections by their stable ids:
    - `section-friction`: Where Things Go Wrong
    - `section-features`: Existing CC Features to Try
    - `section-patterns`: New Ways to Use Claude Code
    - `section-horizon`: On the Horizon
  - Together the four sections are about 17k characters. The other sections ("What You Work On", "How You Use Claude Code" and "Impressive Things You Did") are ignored.
  - The Retro checks each item against its own Findings and returns one verdict:
    - **confirm**: becomes a Finding, with the Retro's own Session evidence added.
    - **merge**: joined with a Finding the Retro already has.
    - **amend**: right, but fixed or sharpened.
    - **drop**: wrong, already done, or outside the Window. Each drop is listed once with its reason.
  - Every item that survives is an ordinary Finding with a status.
  - `/insights` has no date flag and reports on its own range of about 30 days, such as "117 sessions | 2026-09-20 to 2026-10-21". The findings file records that range. A stale item gets the drop verdict, so it needs no separate rule.
  - The headless `-p` Sessions a Retro starts are skipped from the Window, like the Retro's own Session.
- **`/skill-doctor`: not called.** Transcripts attribute plugin use exactly: Skill calls (`ponytail:ponytail`), typed commands (`/ponytail:…`), agents, and MCP tools (`mcp__plugin_<name>_…`). A plugin is unused when none of these appear in the Window.
  - Hook firings are recorded (`hookEvent`, `hookName`) without the owning plugin. A plugin that ships hooks is therefore reported as "hooks only, can't tell", not as unused.
  - Context cost per skill isn't needed.
- **`/doctor prompt-audit`: pointed to, not called.** It uses the model and only reports. When instruction files changed or grew during the Window, a Finding suggests running it.
- **`/usage`: ignored.** Cost comes from the transcripts. Reading quota belongs to [Quota-aware automatic runs](12-quota-aware-automatic-runs.md).
- **Model:** a Retro runs on Opus, the same as `/insights`.
- **Built-ins count as Toolkit.** Claude Code's built-in commands, bundled skills and agents are part of the Toolkit. Claude Code releases are their upstream.
- **Each Finding records its origin:** Retro, `/insights`, or web. Follow-through can then report how each origin's advice fared.
- **Cadence:** monthly. On 2026-10-21, `cleanupPeriodDays` in `~/.claude/settings.json` was changed from 90 to 30 at the user's request, against the recommendation to keep 90 as slack.
  - Transcripts now expire on the Retro's own cycle, so a late Retro loses the oldest days of its Window. A reminder has to fire before day 30.
  - The first Retro reads whatever is on disk, which is now at most 30 days.
- **What sets Retrosmith apart from `/insights`:**
  - Knowledge of the Toolkit: what's installed, what's used and unused, and overlap between items.
  - A web scan for best practices and Toolkit updates.
  - Follow-through on the previous Findings.
  - Applying Findings with approval.

Assets: the report sections live at `~/.claude/usage-data/report-2026-10-21-104221.html`.

Superseded in part by [Findings file shape](10-findings-file-shape.md): surviving `/insights` items are ordinary Findings (tagged `via /insights`) with no status. Findings are applied when the user later asks Claude, not with approval in a walkthrough.
