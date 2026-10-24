# Retrosmith

This repo holds `/retro`, a Claude Code skill that reviews how you used Claude Code over the last 30 days. A Retro reads your Session transcripts and checks whether you adopted the previous Retro's advice and whether it worked. It also compares your installed tools with their upstream sources and searches the web for better fixes. It writes its advice to `~/.claude/retro/findings.md`.

Each piece of advice is a Finding. A Finding states a problem with the numbers behind it and offers up to three solutions. A Retro doesn't apply its own advice. You apply a solution later by asking Claude.

A Retro runs only when 30 days have passed since the previous one started. `/retro redo` skips that wait and replaces the latest Retro. [CONTEXT.md](CONTEXT.md) defines Session, Window, Finding, Toolkit, and the other capitalized terms.

## `retro.py` counts and Claude judges

When you type `/retro`, Claude follows the steps in `retro/SKILL.md`. The Claude Code session where you typed it is the main session. The main session runs `retro.py` with its Bash tool. You don't run the script yourself.

The script does all the work that needs no judgment. It parses transcripts, computes every number, checks upstream sources, and fetches news. The script also flags candidates, such as Sessions with two or more interrupts and no `/clear`, but writes no Finding. The main session and its subagents decide which candidates are real problems and write every Finding. Even the context, cost, and permissions Findings, where the script's numbers are exact, come from the main session. That way every Finding comes from Claude's judgment and goes through the same merge. Plain code costs no tokens, so Claude spends tokens only on judgment.

The skill is these files in `retro/`:

- `SKILL.md` holds the main session's steps. It names each `retro.py` call, the subagents to start, and the layout of the findings file.
- `retro.py` is the helper script. It uses only the Python 3 standard library. Its thresholds are named constants, such as `GATE_DAYS` and `SPLIT_TOKENS`, and most of them are at the top of the file.
- `briefs/` holds the subagents' instructions in parts. `prepare` joins the parts into one brief per subagent. `briefs/fixes.md` also says where each kind of fix belongs. CLAUDE.md loads into every Session, so a fix goes there only when no cheaper place, such as a hook, a lint rule, or a skill, can hold it.
- `rubric.md` lists the practices a Retro checks, each with the anti-pattern to spot in a transcript and its source. Item IDs start with P for prompting, C for context, S for skills, and W for repeated workflows.
- `agents/retro-worker.md` defines the subagent type that every Retro subagent runs as. It allows only Bash, Read, WebFetch, WebSearch, and ToolSearch. It tells the agent not to edit files outside the temp folder or its scratchpad, and not to run git.

## A Retro from start to finish

[`SKILL.md`](retro/SKILL.md) holds the exact steps. In outline, a Retro runs like this:

1. **Check.** The main session runs `retro.py prepare`, or `retro.py prepare --redo` for `/retro redo`. If the session doesn't run on Opus, or the 30-day wait isn't over, `prepare` prints a refusal. The main session repeats the refusal and stops.
2. **Prepare.** `prepare` digests the Window's transcripts, writes every input the run needs into a new temp folder, and prints the folder's path. It also starts `/insights` in the background.
3. **Phase 1.** The main session starts Agents A, B, and C in parallel, as `retro-worker` subagents on Opus. Each agent's whole prompt is `Read <temp folder>/brief_<x>.md and follow it.` Each agent first gives a verdict on the previous Retro's Findings in its own categories, then returns its new Findings. A split input gets one agent per piece.
4. **The main session's share.** While the agents work, the main session writes the Findings for context, cost, and permissions from `metrics.json`. It also gives verdicts on the rest of the previous Retro's Findings and writes the Toolkit updates from `upstream.json`.
5. **Merge.** The main session merges the agents' Findings with its own under `## Findings` in `draft.md`. It drops duplicates and numbers the Findings by weight.
6. **`/insights` review.** `retro.py insights` waits for the background run and extracts four sections of its report. The main session confirms, amends, merges, or drops each item. A confirmed or amended item becomes a Finding tagged `via /insights`.
7. **Phase 2.** The main session picks the five or so most frequent problems and runs `retro.py news` with their categories. The web agent, a `retro-worker` on Sonnet, then searches for better solutions to those problems and reads the changelogs of outdated tools you used. The main session adds the web agent's solutions to the matching Findings, so that no Finding has more than three solutions. It puts the web agent's news items under `## Meta`.
8. **Commit.** `retro.py commit` writes `~/.claude/retro/findings.md`, deletes the temp folder, and opens the file.

Last, if your statusline doesn't call `retro.py status`, the main session offers to add the call. It makes this offer after a days-left refusal too.

## Who covers which category

A Retro sorts problems into nine categories. The three agents and the main session divide them:

| # | Category | Covered by | Reads |
|---|---|---|---|
| 1 | `prompting` | Agent A | `agent_a.json` |
| 2 | `context` | Main session | `metrics.json` |
| 3 | `skills` | Agent C | `agent_c.json` |
| 4 | `repeats` | Agent B | `agent_b.json` |
| 5 | `cost` | Main session | `metrics.json` |
| 6 | `rework` | Agent A | `agent_a.json` |
| 7 | `permissions` | Main session | `metrics.json` |
| 8 | `workflows` | Agent B | `agent_b.json` |
| 9 | `overlap` | Agent C | `agent_c.json` |

Each agent also gets its own rows from `rubric.md`, which `RUBRIC_ITEMS` in `retro.py` picks. The main session writes one more kind of `skills` Finding, for Owned Skills, from `upstream.json`.

## What `retro.py` does

The script has six subcommands. The main session runs five of them, and your statusline runs `status`.

```
retro.py prepare [--redo]
retro.py context <session> <turn> [<temp folder>]
retro.py insights <temp folder>
retro.py news <temp folder> [<category>...]
retro.py commit <draft.md>
retro.py status
```

### `prepare` builds every input

#### Three checks run first

`prepare` runs these checks in order. A failed check stops it before it creates the temp folder.

1. The session must run on Opus. `prepare` takes the first model it finds in these places: the latest `/model` output in the current Session's transcript, the `--model` flag of the running `claude` process, `ANTHROPIC_MODEL`, and `model` in `~/.claude/settings.json`. It also refuses when it finds no model. The `model: opus` line in `SKILL.md` covers only the turn that started the skill. Each time an agent returns, Claude Code starts a new turn on the session's model, so the whole session must run on Opus.
2. At least 30 days must have passed since the Retro Timestamp in `findings.md`. Before the first Retro, the wait counts from the oldest entry in `~/.claude/history.jsonl`. `--redo` skips this check.
3. `rubric.md` must hold every item that `RUBRIC_ITEMS` names. This check keeps a renumbered rubric from leaving an agent without its items.

#### The digest reads the Window's transcripts

`prepare` digests every transcript under `~/.claude/projects/`, including the subagent transcripts in each Session's `subagents/` folder. It keeps only the records timestamped inside the Window, the 30 days before `prepare` started. A Session's digest holds its models, tokens, cost, peak context, compactions, tool calls, Bash commands, slash commands, skills, permission prompts, denials, and turns. A turn starts with a prompt you typed. The digest flags a turn with one or more of these:

- `interrupted`: you stopped Claude mid-turn.
- `steered`: you sent a message while Claude worked.
- `edit_churn`: Claude edited one file 3 or more times.
- `error_loop`: tool calls returned 3 or more errors.

A flagged turn also keeps the last 300 characters of Claude's previous reply, so an agent can see what you reacted to.

The digest leaves out the Retro itself. A typed `/retro` cuts its Session at that prompt, and the cut applies to that Session's subagents too. The digest also drops the headless `/usage` and `/insights` Sessions that a Retro starts.

Transcripts are an internal format that changes between Claude Code versions. `prepare` skips each record it can't parse or whose type it doesn't know, and prints their count as format drift. Only the script parses transcripts. The agents read slices of the digest, and Agent A runs `retro.py context` when it needs a whole turn. There are no automated tests, so the drift count is the only automatic sign that the parser has fallen behind.

#### The temp folder holds every input

`prepare` creates a `retro-` folder in the system temp directory, starts `claude -p "/insights"` there in the background, and writes these files:

| File | Holds | Read by |
|---|---|---|
| `state.json` | Whether the run is a Redo, and the Retro Timestamp | `commit` |
| `digest.json` | The Window's bounds, each Session's digest, and the Window's `history.jsonl` entries | `context` |
| `metrics.json` | Numbers and flagged candidates for context, cost, and permissions | Main session |
| `agent_a.json` | Agent A's input | Agent A |
| `agent_b.json` | Agent B's input | Agent B |
| `agent_c.json` | Agent C's input | Agent C and `news` |
| `brief_a.md`, `brief_b.md`, `brief_c.md` | Each agent's whole instructions | Agents A, B, and C |
| `brief_web.md` | The web agent's instructions | Web agent |
| `splits.json` | The piece files of each split input, or `{}` when nothing was split | Main session |
| `previous.json` | The previous Retro's Findings, Toolkit updates, and Meta, or `null` before the first Retro | Main session |
| `upstream.json` | Everything behind upstream, with update commands | Main session, web agent, and `news` |
| `news_raw.json` | News items newer than the previous Retro | `news` |
| `draft.md` | The findings file with empty sections | Main session, then `commit` |

`metrics.json` also lists each CLAUDE.md and AGENTS.md file that is over 200 lines or changed during the Window. Later, `insights` adds `insights.json` and `news` adds `news.json`. The background `/insights` run writes its own output files to the same folder.

When it finishes, `prepare` prints the format-drift count, your plan usage from `claude -p /usage`, and the temp folder's path. It also prints a line for each split input, and a statusline hint if your statusline lacks `retro.py status`.

#### Each agent gets an input and a brief

Agent A's input holds every typed prompt, Session by Session, with each turn's index for `context`. Flagged turns carry their flags and the end of Claude's previous reply.

Agent B's input holds the same prompts plus repeat candidates that the script finds by text matching:

- the same prompt typed in 2 or more Sessions
- long prompts, first prompts of Sessions, and subagent prompts that are near-identical across 2 or more Sessions, compared by their three-word sequences
- Bash commands and runs of 3 tool calls that recur in 3 or more Sessions

The candidates are leads. Agent B confirms each one against the prompts.

Agent C's input holds the Toolkit table, every typed prompt, and the slash names you typed that match nothing installed. The table has one row per skill, command, and agent, with its origin, its description, its uses in the Window, and its lifetime uses from `~/.claude.json`. It also marks each plugin as used or unused, and flags an unused plugin that ships hooks, because transcripts don't show hook use. `prepare` builds the table from these places:

- `~/.claude/skills/`, where each symlinked skill is traced to the skills CLI lock file, `~/.agents/.skill-lock.json`
- claude.ai synced skills, from `~/.claude/skills/synced/`
- `.claude/skills/`, `.claude/commands/`, and `.claude/agents/` in each project the Window touched
- `~/.claude/commands/` and `~/.claude/agents/`, except `retro-worker`
- installed plugins, from `~/.claude/plugins/installed_plugins.json`
- bundled skills, from the skill listings in transcripts
- built-in commands, from `BUILTIN_COMMANDS` in `retro.py`

Each input also carries `previous_findings`, which holds the previous Retro's Findings in that agent's categories.

Each `brief_<x>.md` joins these parts, in order:

1. `briefs/<x>.md`, the agent's own task
2. `briefs/shared.md`, the follow-through rules and the Finding layout
3. `briefs/piece.md`, only for a piece of a split input
4. `briefs/fixes.md`, only for Agents A and B
5. the agent's rows from `rubric.md`, copied unchanged

`prepare` replaces the `<input>` and `<temp folder>` placeholders with real paths. The brief holds the agent's whole task, so every run gives each agent the same instructions.

#### Large inputs split by Session

If Agent A's or Agent B's input is over 100,000 tokens, estimated as bytes divided by 4, `prepare` splits it into pieces of whole Sessions in time order. Each piece gets its own pair of files, such as `agent_a_1.json` and `brief_a_1.md`, and `splits.json` lists them. Every piece repeats the parts of the input that aren't Sessions, such as B's repeat candidates and `previous_findings`.

The main session starts one agent per piece, then one reconcile agent per split input. The reconcile agent merges the pieces' results and adds up their evidence before it applies a frequency threshold. A problem seen in 3 Sessions of one piece and 3 of another counts as 6. Agent C's input is never split.

#### Upstream checks and news

`upstream.json` lists what is behind upstream, with the changes since the previous Retro started, or from the last 30 days before the first Retro:

- skills from the skills CLI whose folder changed or disappeared upstream, with the repo's commit headlines and an `npx skills update` command
- claude.ai synced skills that were updated
- plugins behind their marketplace, with release notes and a `claude plugin update` command
- Claude Code itself, compared with the latest version on npm
- the CLIs you installed with Homebrew or npm, which of them the Window used, and which are outdated
- Owned Skills whose sources, listed in `metadata.upstream`, changed or disappeared
- skills from the skills CLI whose files you edited, because `npx skills update` would overwrite the edit
- in the first Retro only, skill folders with no recorded source

`news_raw.json` collects the items newer than the previous Retro from these sources:

- Claude Code's GitHub releases
- the RSS feeds of the Claude Code changelog, the Claude Code what's-new page, and claude.dev
- the `claude-code` tag on Simon Willison's blog
- Hacker News stories with "claude code" in the title and more than 50 points
- resources added to `hesreallyhim/awesome-claude-code`
- plugins added to `anthropics/claude-plugins-official`

`FEEDS` and `fetch_news` in `retro.py` hold this list. Every GitHub request goes through `gh api`. A check or source that fails, for example with no network, goes into the `errors` list of its file, and the others still run.

### `context` prints one turn in full

`retro.py context <session> <turn> <temp folder>` reads one Session's transcript again and prints one turn in full. It prints the whole typed prompt, the last 3,000 characters of Claude's previous reply, the tools called, and the edits per file. It also prints any messages you sent mid-turn and the tool errors. Agent A runs it when the digest's 300-character excerpts aren't enough. Given the temp folder, `context` counts turns inside the same Window as `agent_a.json`, so the turn numbers match.

### `insights` extracts the `/insights` report

`prepare` starts `claude -p "/insights"` in the background, so it runs while the rest of the Retro works. `retro.py insights <temp folder>` waits up to 5 minutes for that run to finish. It then finds the HTML report the run wrote and extracts the report's date range and the text of four sections: friction, features, patterns, and horizon. It writes these to `insights.json` and prints that file's path. If any step fails, `insights.json` holds an `error` instead, and the Retro goes on without the review.

### `news` filters the feeds

`retro.py news <temp folder> <category>...` scores each item in `news_raw.json` against a word list. The word list has four parts:

- the names of your Toolkit items, other than built-in commands
- the names of your plugins and installed CLIs
- Claude Code words such as `hook` and `mcp`
- the words that `CATEGORY_TERMS` gives each category you name

Each word in an item's title scores 3, and each word in its body scores 1. An official source adds 5, and a Hacker News story with 100 or more points adds 3. `news` keeps every official item and the 40 best others that score 3 or more, and writes them to `news.json`. The file also names two pages for the web agent to fetch: the claude.com blog and GitHub's monthly trending repos. This first cut is plain code, so the web agent reads only the official items and the items that match your tools or your problems.

### `commit` writes the findings file

`retro.py commit <temp folder>/draft.md` counts the numbered Findings under `## Findings` and writes the count into the draft's first line. It writes the result to `~/.claude/retro/findings.md`, with the Retro Timestamp from `state.json` in the frontmatter. On a normal Retro, it first renames the old `findings.md` to `findings.prev.md`. A Redo skips that rename, so the Redo replaces `findings.md` and keeps `findings.prev.md` as its baseline. Last, `commit` deletes the temp folder, prints the findings file's path, and opens the file with `open`.

### `status` feeds the statusline

`retro.py status` prints nothing until 30 days after the Retro Timestamp. On day 30 it prints `retro due`. After that it prints `retro overdue · Nd lost`, in orange for up to 6 days lost and in red from 7. Each day past day 30 is a day of activity that no Retro will analyze. With no findings file, `status` prints `retro due`.

## What the findings file holds

`findings.md` starts with frontmatter that holds `retro_timestamp`, then a line with the counts, `Sessions: <n> · Projects: <n> · Findings: <n>`. Its sections come in this order:

| Section | Holds |
|---|---|
| `## Failed parts` | Each agent, `/insights` run, or feed that failed, and whether it was re-run |
| `## Follow-through` | A verdict on each of the previous Retro's Findings: worked, didn't work, not adopted, or no longer relevant |
| `## Findings` | The new Findings, numbered by weight across all categories |
| `## Toolkit updates` | What changed upstream for your skills, plugins, CLIs, and Claude Code, each with its update command |
| `## Meta` | News worth acting on, with the exact thing to install or change |
| ``## `/insights` review`` | Counts of confirmed, merged, amended, and dropped `/insights` items, and the reason for each drop |

Every Finding uses this layout:

```
### <n>. <category> · <project or "all"> · via Retro
**Problem**: <one or two lines, with the numbers>
**Solutions**:
- **a.** <the exact change: file and edit, or command>. Fit: <…>. Adoption: <…>.
```

The origin at the end of the heading is `via Retro` or `via /insights`. A solution from the web agent ends with its source URL.

## What carries over between Retros

Retrosmith keeps two files in `~/.claude/retro/`, and nothing else:

- `findings.md` holds the latest Retro's Findings. Its `retro_timestamp` is the moment that Retro's `prepare` started. The 30-day check, `status`, and the next Retro all read this file.
- `findings.prev.md` holds the Retro before the latest. A Redo reads its follow-through baseline from here, so the Redo judges the same Findings that the Retro it replaces judged.

Findings carry no status. The next Retro judges each one from what changed: settings, installs, use in the Window, and whether the problem came back.

The Retro Timestamp moves only when `commit` runs. A Redo writes a new one, so the 30-day wait restarts from the Redo. A Redo keeps no copy of the `findings.md` it replaces.

Each Window is the 30 days before its Retro, and Retros are at least 30 days apart, so no day falls in two Windows. A late Retro leaves a gap instead, and `status` counts the gap as days lost.

## When a part fails

Most failures don't stop a Retro. The main session lists each of these under `## Failed parts` and goes on:

- an upstream check or news source that failed, from the `errors` lists in `upstream.json` and `news_raw.json`
- a failed `/insights` run, from `insights.json`
- an agent that crashed, timed out, or returned garbled output

Before it lists a failed agent, the main session offers you one re-run of it.

An agent that hits your usage limit hasn't failed. The main session tells you which agents paused. When you type `continue` after the limit resets, it re-runs only those agents, from the same input files.

If Agents A, B, and C all fail, the main session doesn't run `commit`. It deletes the temp folder, so `findings.md` and the Retro Timestamp stay as they were.

## What Retrosmith needs on your machine

Claude Code finds the skill and its agent through two symlinks. From the repo root, these commands create them:

```sh
ln -s "$PWD/retro" ~/.claude/skills/retro
ln -s "$PWD/retro/agents/retro-worker.md" ~/.claude/agents/retro-worker.md
```

`briefs/a.md` and the statusline command call the script as `~/.claude/skills/retro/retro.py`, so the skill must live at that path. Claude Code reads agent files when a session starts, so an edit to `retro-worker.md` applies from your next session.

Retrosmith targets macOS, where `commit` opens the findings file with `open`. It also needs:

- Python 3, for `retro.py`
- the `claude` CLI on your `PATH`, for `/usage`, `/insights`, and `claude --version`
- `gh`, signed in, for the GitHub checks and three of the news sources
- `brew` and `npm`, for the CLI checks and Claude Code's latest version
- a `cleanupPeriodDays` setting of 30 or more, because Claude Code deletes older transcripts and the Window needs the last 30 days

A missing tool costs only the checks that use it, and each failed check shows up under `## Failed parts`.
