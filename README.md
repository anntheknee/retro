# Retrosmith

This repo holds `/retro`, a Claude Code skill that reviews how you used Claude Code over the last 30 days. It reads your Session transcripts, checks whether you adopted the previous Retro's advice, compares your installed tools with their upstream sources, and searches the web for better fixes. It writes its advice to `~/.claude/retro/findings.md`.

Each piece of advice is a Finding: a problem with the numbers behind it, and up to three solutions. A Retro doesn't apply its own advice. You apply a solution later by asking Claude.

A Retro runs only when 30 days have passed since the previous one started. `/retro redo` skips the wait and replaces the latest Retro. [CONTEXT.md](CONTEXT.md) defines the capitalized terms.

## The moving parts

`retro.py` counts and Claude judges. The script does everything that needs no judgment: it parses transcripts, computes the numbers, checks upstream sources, and fetches news. Claude decides which candidates are real problems and writes every Finding.

| Part | Role |
|---|---|
| `retro/SKILL.md` | The steps the main session follows |
| `retro/retro.py` | Helper script, Python 3 standard library only. The main session runs it. You don't |
| `retro/briefs/` | Instructions for the subagents, joined into one brief per agent |
| `retro/rubric.md` | The practices a Retro checks, each with the anti-pattern to spot and its source |
| `retro/agents/retro-worker.md` | The subagent type every Retro subagent runs as |

## How a Retro runs

1. **Prepare.** `retro.py prepare` checks that the session runs on Opus and the 30-day wait is over. It digests the transcripts, writes every input into a temp folder, and starts `/insights` in the background.
2. **Analyze.** The main session starts three `retro-worker` agents in parallel. Each reads its brief and returns Findings for its categories. Meanwhile the main session writes the context, cost, and permissions Findings from the script's numbers.
3. **Merge.** The main session merges all Findings into one draft, drops duplicates, and numbers them by weight. It also reviews the `/insights` report.
4. **Search.** A web agent looks for better solutions to the most frequent problems and reads changelogs of outdated tools.
5. **Commit.** `retro.py commit` writes `findings.md`, deletes the temp folder, and opens the file.

| Category | Covered by |
|---|---|
| `prompting`, `rework` | Agent A |
| `repeats`, `workflows` | Agent B |
| `skills`, `overlap` | Agent C |
| `context`, `cost`, `permissions` | Main session |

Large inputs split by Session, so an agent never reads more than about 100,000 tokens.

## What carries over

Retrosmith keeps two files in `~/.claude/retro/`:

- `findings.md` holds the latest Retro's Findings. Its `retro_timestamp` drives the 30-day check.
- `findings.prev.md` holds the Retro before it, as the baseline for `/retro redo`.

The next Retro judges each Finding from what changed since: settings, installs, and whether the problem came back.

`retro.py status` is for your statusline. It prints `retro due` on day 30, then `retro overdue · Nd lost`.

Most failures don't stop a Retro. A failed upstream check, news source, `/insights` run, or agent goes under `## Failed parts` in `findings.md`, and the rest still runs.

## Setup

Claude Code finds the skill and its agent through two symlinks. From the repo root:

```sh
ln -s "$PWD/retro" ~/.claude/skills/retro
ln -s "$PWD/retro/agents/retro-worker.md" ~/.claude/agents/retro-worker.md
```

Retrosmith targets macOS and needs Python 3, the `claude` CLI, `gh` (signed in), `brew`, and `npm`. It also needs `cleanupPeriodDays` set to 30 or more, because Claude Code deletes older transcripts. A missing tool costs only the checks that use it.
