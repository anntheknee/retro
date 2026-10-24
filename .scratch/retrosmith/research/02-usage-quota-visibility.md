# Usage quota visibility, headless skills, and local triggers

Research for [ticket 02](../wayfinder-issues/02-usage-quota-visibility.md). Checked 2026-10-20 against Claude Code **2.1.304** (local install), the docs at code.claude.com, and the [CHANGELOG](https://github.com/anthropics/claude-code/blob/main/CHANGELOG.md).

## Answer

- **Yes, a script can read remaining plan usage and reset times.** `claude -p "/usage" --output-format stream-json --verbose` returns a structured `usage_report` with a session (5h) row and a weekly row, each with `percent` and an ISO `resets_at`. It costs **zero model tokens** (verified locally). The statusline JSON carries the same data as `rate_limits`, but only while an interactive session is running.
- **Yes, headless `claude -p` can invoke a skill and the skill can spawn subagents.** Verified locally with one call ($0.006).
- **Local trigger: launchd + `claude -p`.** `/schedule` runs in Anthropic's cloud on a fresh clone of GitHub repos, so it cannot read `~/.claude/projects` (confirmed). Desktop scheduled tasks are local but need the Desktop app open, and the map rules out non-CLI surfaces.

## 1. Reading remaining plan usage

### 1a. `claude -p "/usage"` (best for a script)

The docs say that when you send `/usage` as a prompt, "Claude Code delivers the report as an assistant message whose `message.content` holds the text" and attaches a structured `usage_report` (type `SDKUsageReport`, marked experimental) when the session uses a claude.ai credential that "shows a known plan type or carries the `user:profile` scope" and the account isn't on usage-based billing ([Agent SDK TypeScript reference, SDKAssistantMessage / SDKUsageReport](https://code.claude.com/docs/en/agent-sdk/typescript)). Each `limits` row has `kind` (`session`, `weekly_all`, `weekly_scoped`), `group`, `percent` (0–100), `resets_at` (ISO 8601), `severity`, and `is_active`. The docs say to classify rows on `kind`, never on a label ([same page](https://code.claude.com/docs/en/agent-sdk/typescript)).

Verified locally (run from the scratchpad with `--no-session-persistence`, so nothing was written to `~/.claude/projects`):

```bash
claude -p "/usage" --no-session-persistence --output-format stream-json --verbose < /dev/null \
  | jq -c 'select(.type=="assistant") | .usage_report.rate_limits.limits'
```

Output (trimmed):

```json
[{"kind":"session","group":"session","percent":23,"resets_at":"2026-10-20T14:29:59.927028+00:00","severity":"normal","is_active":true},
 {"kind":"weekly_all","group":"weekly","percent":14,"resets_at":"2026-10-26T05:59:59.927047+00:00","severity":"normal","is_active":false}]
```

- `usage_report` sits at the **top level** of the assistant event, not inside `.message`. Observed locally.
- The `result` event reported `total_cost_usd: 0`, `num_turns: 0`, and all token counts 0. `/usage` is a local command, not a model turn. Observed locally.
- The text body also includes the **plan usage breakdown**: usage share by skill, subagent, plugin, and MCP server, plus behavior flags such as "% at >150k context" and "% at max effort" over 24h and 7d. The docs describe this breakdown as "computed from local session history on this machine" ([costs: Plan usage breakdown](https://code.claude.com/docs/en/costs#plan-usage-breakdown)). This is directly useful to problem category 5 (cost/token hotspots). The breakdown is text only. The structured `usage_report` carries `session` and `rate_limits`, not the attribution.

Caveats:
- **Do not use `--bare`.** Bare mode "never reads OAuth credentials or the system keychain" and needs `ANTHROPIC_API_KEY` ([headless: bare mode](https://code.claude.com/docs/en/headless#start-faster-with-bare-mode)). An API-key session gets no `usage_report` ([SDK reference](https://code.claude.com/docs/en/agent-sdk/typescript)).
- **A `claude setup-token` token is not enough by default.** As `CLAUDE_CODE_OAUTH_TOKEN` it "carries only the `user:inference` scope", so no `usage_report` ([SDK reference](https://code.claude.com/docs/en/agent-sdk/typescript)). Use the normal `/login` keychain credential.
- **The usage endpoint can be rate limited.** `/usage` then falls back to "last-known usage" from the past 60 minutes ([costs: When the usage request fails](https://code.claude.com/docs/en/costs#when-the-usage-request-fails)). Poll no more often than every few minutes.
- `usage_report` is experimental, and its shape may change ([SDK reference](https://code.claude.com/docs/en/agent-sdk/typescript)). Fall back to parsing the text lines `Current session: N% used · resets …` and `Current week (all models): …`.

### 1b. Statusline JSON `rate_limits` (interactive sessions only)

The statusline script receives `rate_limits.five_hour.{used_percentage,resets_at}` and `rate_limits.seven_day.{…}`, where `resets_at` is Unix epoch seconds ([statusline: available data](https://code.claude.com/docs/en/statusline)). This field was added in v2.1.80 ([CHANGELOG 2.1.80](https://github.com/anthropics/claude-code/blob/main/CHANGELOG.md)). Limits on when it is available:
- It "appears only for claude.ai Pro and Max subscribers … and only after the first API response in the session. Each window … may be independently absent, and Claude Code drops a window once its `resets_at` time passes" ([statusline](https://code.claude.com/docs/en/statusline)).
- The script runs only on session events: start, new assistant message, `/compact`, a mode change, an optional `refreshInterval` timer, or a window reaching `resets_at` ([statusline: When the status line updates](https://code.claude.com/docs/en/statusline)). No session running means no data.

Locally, `~/.claude/context-statusline.sh` already dumps its stdin to `$TMPDIR/statusline-probe.json` (marked TEMP). That file contained `"rate_limits":{"five_hour":{"used_percentage":8,"resets_at":1792506600},"seven_day":{"used_percentage":11,"resets_at":1792994400}}`. A statusline could cache this to a file, but the cache is stale whenever no session is running. Option 1a has no such gap, so prefer it.

### 1c. Other sources (none give remaining quota)

- `~/.claude/stats-cache.json` has keys `dailyActivity`, `dailyModelTokens`, `hourCounts`, `modelUsage`, `totalSessions`, and similar: activity counts only, with no limits or resets (local inspection).
- Transcript `cost-state` records hold per-session `totalCostUSD` and per-model token counts, with no quota fields (local inspection).
- Transcripts record quota **only on rejection**: a 429 assistant message with `apiError: "usage_limit_reached"` and `quotaLimits: {status:"rejected", resetsAt, rateLimitType:"five_hour", …}` (local inspection). This is useful history for a Finding ("you hit the 5h limit N times"), but it doesn't help predict a reset.
- Headless stream-json emits `rate_limit_event` (`rate_limit_info.status` = `allowed` | `allowed_warning` | `rejected`, plus optional `resetsAt` and `utilization`) "when the session encounters a rate limit" ([SDK reference: SDKRateLimitEvent](https://code.claude.com/docs/en/agent-sdk/typescript); headless warnings improved in [CHANGELOG 2.1.295](https://github.com/anthropics/claude-code/blob/main/CHANGELOG.md)). It is passive and arrives mid-run, so it can't drive scheduling.

## 2. Skills and subagents in headless `claude -p`

- **Skills:** "User-invoked skills and custom commands work. Include `/skill-name` in the prompt string and Claude Code expands it before running." Built-in terminal-only commands such as `/login` aren't available ([headless: command support note](https://code.claude.com/docs/en/headless#create-a-commit)). Without `--bare`, `-p` "discovers and loads [hooks, skills, subagents, plugins, MCP, CLAUDE.md] as an interactive session would, including anything configured in the working directory or `~/.claude`" ([headless: bare mode](https://code.claude.com/docs/en/headless#start-faster-with-bare-mode)).
- **Subagents:** stream-json documents subagent and forked-skill messages, tagged by `parent_tool_use_id`, including for "a forked skill you start by passing `/<skill-name>` as the prompt" ([headless: Follow subagent messages](https://code.claude.com/docs/en/headless#follow-subagent-messages)). A `-p` run waits for background subagents before exiting, because "its result is part of the final output" ([headless: Background tasks at exit](https://code.claude.com/docs/en/headless#background-tasks-at-exit)).
- **Verified locally:** I used a throwaway project skill `probe` in the scratchpad, not under `~/.claude`, whose body says to call the Agent tool once. I ran `claude -p "/probe" --model haiku --max-budget-usd 0.5 --no-session-persistence --output-format stream-json --verbose`. Results:
  - `system/init` listed the `probe` skill.
  - The main thread emitted an `Agent` tool_use.
  - The subagent's messages carried that tool_use ID as `parent_tool_use_id`.
  - The result was `"SKILL_OK pong"`, `subtype: success`, at $0.0063. The Agent tool needed no permission grant.
- **Permissions for unattended runs:** since v2.1.302, `-p` starts in Manual mode, where calls that need approval are denied. Pre-approve tools with `--allowedTools` (for example `Bash(python3 ~/.claude/skills/retro/*)`) or choose a `--permission-mode`. Add `--permission-prompts none` for scheduled jobs ([headless: Auto-approve tools / Turn off permission prompts](https://code.claude.com/docs/en/headless#auto-approve-tools)).
- Locally, `-p` printed `Warning: no stdin data received in 3s` when stdin was not redirected. Pass `< /dev/null` from launchd.

## 3. Local triggers

| Option | Runs where | Can read `~/.claude/projects` | Notes |
| - | - | - | - |
| **launchd + `claude -p`** | Your Mac | Yes | Apple: cron "has been deprecated in favor of `launchd`". With `StartCalendarInterval`, a job missed during sleep "will run when the computer wakes up" (but not if powered off) ([Apple: Scheduling Timed Jobs](https://developer.apple.com/library/archive/documentation/MacOSX/Conceptual/BPSystemStartup/Chapters/ScheduledJobs.html)). Auth: the `/login` credential lives in the macOS Keychain ([authentication: Credential management](https://code.claude.com/docs/en/authentication#credential-management)). A per-user LaunchAgent should be able to read it; not tested. |
| cron + `claude -p` | Your Mac | Yes | Deprecated on macOS. Jobs missed while asleep are skipped ([Apple](https://developer.apple.com/library/archive/documentation/MacOSX/Conceptual/BPSystemStartup/Chapters/ScheduledJobs.html)). |
| `/loop` / `CronCreate` | Inside an open CLI session | Yes | Session-scoped: "Tasks only fire while Claude Code is running and idle", and recurring tasks expire after 7 days ([scheduled tasks](https://code.claude.com/docs/en/scheduled-tasks#limitations)). |
| Desktop scheduled tasks | Your Mac, via the Desktop app | Yes | Fire "only while the app is open and your computer is awake"; one catch-up run on wake ([desktop scheduled tasks](https://code.claude.com/docs/en/desktop-scheduled-tasks)). Not CLI. |
| `/schedule` (cloud scheduled tasks, formerly routines) | Anthropic cloud | **No** | See below. |

**The `/schedule` claim is confirmed.** Cloud scheduled tasks "execute on Anthropic-managed cloud infrastructure". "Each repository is cloned at the start of a run", and the comparison table lists "Access to local files: No (fresh clone)". Locally added MCP servers "are stored on your machine … so they do not appear in the connectors list". The minimum interval is 1 hour ([routines](https://code.claude.com/docs/en/routines); [scheduled tasks: Compare scheduling options](https://code.claude.com/docs/en/scheduled-tasks#compare-scheduling-options)). Transcripts never reach the cloud run, so a cloud task can't run a Retro.

## Implications for the "pre-digest near a usage reset" fog

A launchd agent can poll `claude -p "/usage"` at zero model cost. When `session.resets_at` is near and `percent` is low, it can start `claude -p "/retro …" --allowedTools … --permission-prompts none < /dev/null`, and the skill can fan out to subagents. The sketch below shows the polling half:

```bash
# ponytail: sketch only; the real script decides thresholds
claude -p "/usage" --no-session-persistence --output-format stream-json --verbose < /dev/null \
  | jq -r 'select(.type=="assistant") | .usage_report.rate_limits.limits[]
           | select(.kind=="session") | "\(.percent) \(.resets_at)"'
```

Open points for the spec, outside this ticket's scope:
- How partial digests square with "store nothing".
- Whether an unattended Retro may apply Findings. The current design needs approval, so an unattended run can only produce the findings file.
