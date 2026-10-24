# Quota-aware automatic runs

Type: grilling
Status: closed (out of scope)
Assignee: me
Blocked by: 06, 09

## Question

Now that [Usage quota visibility](02-usage-quota-visibility.md) shows quota and reset times can be read for free, does v1 include a launchd job that checks `/usage` and starts work when quota would otherwise expire unused? If so: the trigger rule (e.g. weekly use under X% with reset within N hours), what an unattended run does (a full Retro, or a pre-digest that a later interactive `/retro` finishes), where any partial digest lives and when it's deleted (given "store nothing"), what permissions the headless run gets, and what happens if the Mac is asleep or off. If not, rule it out of scope for v1.

Note from [Retro state and lifecycle](06-retro-state-and-lifecycle.md): an unattended run hits the same gate with no override (now 30 days since the Retro Timestamp, per [Script vs. skill boundary and subagent fan-out](07-script-vs-skill-boundary-and-fan-out.md)), and a pre-digest stored anywhere other than `~/.claude/retro/findings.md` would be new state.

Note from [Token budget and cost guardrails](09-token-budget-and-cost-guardrails.md): `prepare` already prints a one-line `/usage` reading (session and weekly percent and resets) with no threshold. Cost isn't a concern. An agent that hits the usage limit is re-run after the user resumes, which an unattended run can't do: decide what happens instead.

## Resolution

Ruled out of scope for v1. The Notes line "v1 is triggered manually with `/retro`, monthly" stands.

- The 30-day gate means a quota trigger could fire in about one week out of every four or five. In the other weeks it would only check the gate and exit.
- A pre-digest that lasts until a later `/retro` would be new state outside `~/.claude/retro/findings.md`.
- An unattended run has no one to type "continue" after a usage-limit pause or to approve a re-run of a failed agent ([Token budget and cost guardrails](09-token-budget-and-cost-guardrails.md)). Every permission would have to be granted in advance.
- The real risk is a late Retro and the gap it leaves. [Retro due reminder](13-retro-due-reminder.md) handles that more cheaply. That ticket received a note about showing leftover quota.
