# Usage quota visibility

Type: research
Status: resolved
Blocked by:

## Question

Can a script or skill read the user's remaining Claude plan usage and its reset time (session and weekly), e.g. via `/usage`, the statusline JSON input, `claude -p`, or local files? Separately: in headless `claude -p`, can a skill be invoked and subagents be spawned? Feeds the "Automatic or pre-digest runs near a usage reset" fog.

## Answer

- Remaining usage is readable: `claude -p "/usage" --output-format stream-json --verbose` returns a structured `usage_report` with session (5h) and weekly rows (`percent`, ISO `resets_at`) at zero model tokens (verified). Needs the normal `/login` credential: not `--bare`, not a `setup-token` token.
- The statusline JSON `rate_limits` carries the same data, but only while an interactive session is running. stats-cache, `cost-state`, and transcripts hold no quota data (transcripts record resets only on 429 rejections).
- Headless `claude -p "/skill"` runs the skill, and the skill can spawn subagents (verified for $0.006). Unattended runs need `--allowedTools` or a permission mode plus `--permission-prompts none`.
- Local trigger: launchd + `claude -p` (cron is deprecated on macOS). `/schedule` runs in the cloud on a fresh repo clone and cannot read `~/.claude` (confirmed).

[findings](../research/02-usage-quota-visibility.md)
