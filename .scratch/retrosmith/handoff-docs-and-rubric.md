# Handoff: docs reference, drop BUILTIN_COMMANDS, rubric update

Written 2026-10-24 before a `/clear`. The user approved three changes (A, B, C below) out of a list of ten improvement ideas. Build only these. Ideas not approved are listed at the end for reference.

## Before you start

- The working tree holds uncommitted work from [handoff-speed-and-context.md](handoff-speed-and-context.md): changes to `retro/SKILL.md` and `retro/retro.py`, plus the untracked `retro/briefs/`, `retro/agents/`, `README.md` and `CONTEXT.md`. It hasn't been run end to end yet. Don't lose it. Ask the user whether to commit it first. The current branch is a detached `HEAD`, so branch before committing.
- That handoff said "don't change the rubric". The user has now approved changing it (C).
- Rules: ponytail (smallest working change), `retro.py` is stdlib only, BSD `sed` on macOS (use Edit instead), don't change the Findings layout.

## Facts checked this session

- `https://code.claude.com/docs/llms.txt` (64KB) is only an index: 275 links, each with a title and a one-line description. It doesn't list every feature. To get the content, an agent would have to WebFetch each link.
- `https://code.claude.com/docs/llms-full.txt` (9.8MB, about 2.4M tokens, 124k lines) is the full text of every page: 231 pages, each starting `# <title>` then `Source: https://code.claude.com/docs/en/<slug>`. It's too big to read, but cheap to grep. It includes Agent SDK and admin pages, which are noise here; grep handles that.
- `https://code.claude.com/docs/en/commands.md` (59KB) is the commands reference. Its "All commands" table has 120 rows of the form ``| `/name [args]` | Purpose |``. 21 rows are marked `**[Skill](…)**` (bundled skill) or `**[Workflow](…)**` (bundled workflow). The same page is inside `llms-full.txt` at `Source: https://code.claude.com/docs/en/commands`.
- `BUILTIN_COMMANDS` (`retro/retro.py:39`) is hand-kept and has 47 names. It's missing `/workflows`, `/auto-mode-setup`, `/background`, `/branch`, `/tasks`, `/autocompact` and more. It's used in two places:
  - `build_toolkit` (`retro/retro.py:725`), which adds each name with origin "built-in command" and **no description**, so Agent C can't match built-ins to tasks (S1/S6).
  - news scoring (`retro/retro.py:1283`), where built-in names are excluded from the Toolkit word list.
- `http_get(url)` (`retro/retro.py:1161`) already exists (urllib, 30s timeout). Feeds that fail go into an `errors` list, and the main session lists them under Failed parts.
- Digest turns already carry `ts` and `ms` (`durationMs`, `retro/retro.py:355-361`), so idle and long-turn detection needs no new parsing.
- `RUBRIC_ITEMS` (`retro/retro.py:756`) gives rows only to A, B and C. The main session (context, cost, permissions) gets no rubric rows. **10 of the 42 items reach no one: C1, C4, C7, C9, C10, C11, C12, C13, C14, C15.** C7 is half-covered by the `instruction_files` sentence in `SKILL.md`. (I told the user 11 earlier; 10 is right.)
- The briefs name their item IDs by hand: `briefs/a.md:3` "P1-P12, plus C2, C3, C6 and C8", `briefs/b.md:3` "W1-W8, plus C5 and C6", `briefs/c.md:3` "S1-S7".

## A. Docs reference for the agents

The user's point: `llms.txt` doesn't list everything, so the index alone isn't enough. Use `llms-full.txt` instead.

1. In `prepare`, download `llms-full.txt` with `http_get` into `<temp folder>/docs.txt`. On failure, add to `upstream.json` `errors` (or wherever feed errors go) so it reaches Failed parts. Don't stop the Retro.
2. Add one sentence to each brief (`a.md`, `b.md`, `c.md`, `web.md`) and to `SKILL.md` for the main session, roughly: "`<temp folder>/docs.txt` is the current Claude Code docs, the full text of every page, each starting `# <title>` then `Source: <url>`. Grep it, never read it whole. Before you name a command, setting, flag, hook event or feature in a solution, confirm it there and use its Source URL." The briefs use `<temp folder>` placeholders, which `prepare` fills in.
3. Don't filter, cache or parse it beyond B. No catalog and no used/unused counting: the agent compares with the digest's slash commands itself.

## B. Drop BUILTIN_COMMANDS

The user agreed: no hand-kept lists.

1. Delete `BUILTIN_COMMANDS`. Parse the commands table from the commands section of `docs.txt` (the block after `Source: https://code.claude.com/docs/en/commands` up to the next `\nSource: `). Take rows matching `^\| \`/([\w:-]+)`, plus the Purpose cell as the description, with markdown links stripped to their text and capped like other descriptions. Rows marked `[Skill]` or `[Workflow]` get origin "bundled skill" or "bundled workflow"; the rest get "built-in command".
2. `build_toolkit` (`:725`) adds them **with descriptions**. Avoid a duplicate row when a name already came from `dg["skill_listings"]` (`:723`). Check what `add()` does on a repeat name.
3. News scoring (`:1283`) excludes these names, as now.
4. `prepare` must fetch the docs before `build_toolkit` runs. Check the order in `prepare` (`:1314`) and in the `tk = build_toolkit(dg)` call sites (`:750`, `:1042`).
5. **Open question for the user:** if the docs fetch fails, there are no built-in names, and `dead_slash` would wrongly report every built-in command the user typed. My recommendation: on a failed fetch, skip `dead_slash` (an empty list) and say so in `errors`. Don't keep a hand-kept fallback list.
6. Update the README line "built-in commands, from `BUILTIN_COMMANDS` in `retro.py`" (in "Each agent gets an input and a brief").

## C. Rubric update

Recommendation the user accepted: **no new categories**, because each one would touch `AGENT_CATEGORIES`, `CATEGORY_TERMS`, the `SKILL.md` category lists, the README category table and "nine categories". Fold new practices into existing categories instead:

1. **Main-session slice:** add `RUBRIC_ITEMS["main"]` = the orphaned C items (C1, C4, C7, C9–C15) plus the new cost and permissions rows. `prepare` writes it to `<temp folder>/rubric_main.md`. `SKILL.md` step 3 tells the main session to read `rubric_main.md` with `metrics.json` and `briefs/fixes.md`. The `rubric_slice` guard (`:762`) already fails loudly on a missing ID. Check that `brief_*` generation loops don't choke on a `"main"` key with no brief, since `slices` is built from `RUBRIC_ITEMS.items()` at `:1333`.
2. **New rubric sections for cost (5) and permissions (7),** same columns as the existing tables (Practice | Anti-pattern to spot | Detect | Source). Pick ID prefixes that are word characters (`row_id` uses `\w+`) and don't collide with P, C, S, W. Suggestion: `M` for cost, `A` for permissions/access. Confirm with the user. Candidate rows, each needing a primary-source URL found by grepping `llms-full.txt` (don't invent anchors):
   - **Cost:** model per task (Sonnet for routine work, Opus for hard work, `opusplan`); effort level per task; the model a subagent inherits (pass `model` per Agent call; last Retro's Finding 6 had research agents inherit Opus at `max`, $53); fast mode costs more. Main source: `costs.md`.
   - **Permissions:** allow rules for prompts answered again and again (`/permissions`, the `fewer-permission-prompts` skill); auto mode and `/auto-mode-setup`; the sandbox (`sandboxing.md`); deliberate denials stay denied.
   - **Safety (under permissions):** secrets pasted into prompts (script detector: a regex over typed prompts; **never copy the secret into any output**, report only Session and turn); `--dangerously-skip-permissions` / bypass mode outside a sandbox (the digest already records permission modes); destructive git commands (`push --force`, `reset --hard`, `clean`, `branch -D`) with no guardrail hook (Bash heads are in the digest; the user has a `git-guardrails-claude-code` skill to point to).
   - **Parallelism and idle time (under context, new C rows):** long turns the user waited through (`ms` per turn) → background agents (`/background`, `/tasks`), a Notification hook, a second Session or a worktree; polling by hand → `/loop` or `/schedule`.
3. Script detectors only for rows marked `script`: the secrets regex, bypass-mode count, destructive git heads with no hook, and long-turn counts from `ms`. They go into `metrics.json` next to the context, cost and permissions candidates (`compute_metrics`, returns at `:471`). Rows marked `LLM` need no code.
4. If any agent's rows change, update the hand-written ID lists in `briefs/a.md`, `b.md` and `c.md`.
5. Update the docs: `rubric.md` intro (it says it covers categories 1, 2, 3 and 8), README ("Item IDs start with P, C, S, W", the "Each agent also gets its own rows" line, and say the main session now gets a slice), and `.scratch/retrosmith/spec.md` ("The 42-item rubric").

## Verify

1. Quick checks with no Retro: `rubric_slice(RUBRIC_ITEMS[k])` for every key, and the commands parser on a saved `docs.txt`. Expect about 120 names, the 21 Skill/Workflow rows tagged, and `/workflows`, `/auto-mode-setup` and `/clear` present with descriptions.
2. Leave one small runnable check for the parser, per ponytail (an `assert` block or one `test_*.py`).
3. Full run: copy `~/.claude/retro/findings.md` aside, then in a fresh Opus session run `/retro redo`, then `python3 .scratch/retrosmith/runstats.py <session .jsonl>`. See the Verifying section of the speed handoff. Check that the agents grepped `docs.txt` and cited Source URLs, and that context, cost and permissions Findings now use the C, M and A rows.

## Not approved, for reference

From the same list of ten: mine the user's "is there a way…" questions (2), fact-check every solution against `docs.txt` before `commit` (3, cheap once A exists), a "This month's 3" block at the top (4), teaching inside Findings: prompt makeovers, a term defined on first use, Learning/Explanatory output styles (5), an apply step at the end or `/retro apply 3b` (6), the statusline showing the top habit (7), numbers carried in frontmatter for trends (8), regression fixtures (10), `cleanupPeriodDays: 90` with a Window that runs from the last Retro Timestamp. Raise them only if the user asks.
