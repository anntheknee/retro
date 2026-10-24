# Handoff: make /retro faster and leaner

Goal, in the user's words: make /retro faster and use less context, with no loss in finding quality. Don't change the Findings layout or the rubric. Keep the agents' instructions as they are unless a change is clearly safe.

**Revised 2026-10-24:** the user said time and context are fine as they are. A slight reduction is best; a dramatic one isn't needed. Finding quality comes first. So build only the proposals that can't degrade the Retro.

Status (2026-10-24): 2 and 3 built, not committed, not yet run end to end. `retro/briefs/{a,b,c,web,shared,piece}.md` hold the agent text (from `SKILL.md` and last run's actual prompts, re-voiced). `prepare` writes `brief_<input>.md` per agent input and `brief_web.md`; `rubric_slice` copies rows verbatim and exits before the temp folder if an item is missing (`RUBRIC_ITEMS` in `retro.py`). `SKILL.md` prompts are now "Read <brief> and follow it" (web adds the problem list and one line on the user's tools, as last run's main session did). Checked: slices are line-for-line from `rubric.md` with the `:42`/`:78` notes; every old agent sentence has a match in the briefs. Also added (user's request): an Opus gate at the top of `prepare` (`session_model` in `retro.py`). The session's latest `/model` output wins, then `--model` in the `claude` process args, then `ANTHROPIC_MODEL`, then `settings.json` `model`. If it isn't Opus, `prepare` prints a refusal and returns with no temp folder; `SKILL.md` step 2 stops there. Tested on real `/model` records (Opus and Sonnet sessions), a `--model sonnet` process and `ANTHROPIC_MODEL`. Next step: the Verifying steps, then the user compares findings. Offer 1 only as a separate, A/B-tested step if the user wants more. 4–7 are dropped. Expected for 2 and 3: agent tokens ~340k → ~315k, main session −2.5k context, ~25s faster.

**2+3 measured (2026-10-24, session `304e0658`):** A 9 req/132s/31.5k→105.3k, B 8/112s/31.5k→76.7k, C 20/203s/31.5k→95.1k, web 6/82s/32.1k→72.3k; sum 349.4k (window moved; C spent 11 calls on openspec internals). No agent read `rubric.md`. Main 414s, all Opus. This run is the A side of the A/B for 1.

**1 built (2026-10-24):** `retro/agents/retro-worker.md`, symlinked to `~/.claude/agents/`; tools Bash, Read, WebFetch, WebSearch, ToolSearch (ToolSearch as insurance in case WebFetch is deferred). SKILL.md spawns A/B/C, pieces, reconcile and web with `subagent_type: retro-worker`. `build_toolkit` skips it.

## Quality check (2026-10-24)

| # | Verdict | Why |
|---|---|---|
| 2 rubric slice | **Build.** No quality risk. | Each agent's brief already says "items X–Y and nothing else". The slice copies those rows verbatim with every column, plus the table header and the notes outside the tables (`rubric.md:42` for A, `:78` for B). The agents see the same text minus rows they are told to ignore. Guard: `prepare` fails loudly if a named item ID isn't found in `rubric.md`, so a renumbered rubric can't silently starve an agent. |
| 3 briefs from files | **Build.** No quality risk; likely a small gain. | Today the main session paraphrases `SKILL.md` into each prompt (1.6–3.5KB), which can drop instructions. A brief file gives the agent the exact text every run. Keep everything an agent gets now: its bullet, the Follow-through paragraph, the split-piece "2 Sessions" line, and the layout block. Diff each brief against `SKILL.md` before the first run; the only allowed change is the voice ("tell it to X" → "X"). |
| 1 retro-worker | **Optional, last.** Low but real risk. | It's the biggest saving (~100k), but it's the only proposal that changes the agents' environment: a new system prompt in place of `general-purpose`'s, a smaller tool set, no skill listing. All three are probably fine (no agent needs the skill listing or Artifact), but "probably" isn't verified. Build it only if the user wants more savings, and A/B it against a 2+3 run. The ponytail persona is injected into Retro agents today; keeping it out is a separate change and the user's call. |
| 4 script lookups | **Drop.** Can degrade Toolkit updates. | Per-path commits lose repo-wide changes that affect a skill (shared scripts, renames), and they cost one GitHub call per behind skill instead of one per repo, so rate-limit errors become more likely. Sending plugin releases only to the web agent removes input the main session uses to write Toolkit updates. The saving (7–9k of main context) isn't worth it. |
| 5 faster `prepare` | **Drop.** Time isn't a goal now. | No quality effect, but it adds concurrency (`/usage` early, a detached `news`) and new race conditions for ~14s. |
| 6 web before `/insights` | **Drop.** | An `/insights` item confirmed into the top five would miss the web search. |
| 7 Haiku for phase 2 | **Drop.** | Saves no context and risks weaker solutions. |

## Baseline (last run, measured)

Retro Timestamp 2026-10-23T22:57:13Z. Session `~/.claude/projects/-Users-bloom-workspace-retrosmith/1e856763-9c48-4bfa-b25d-57e26b62aca5.jsonl`, subagents in the folder beside it. No previous Retro. Effort was medium everywhere; nothing pins it.

| Agent | Model | Requests | Time | First request | Final context |
|---|---|---|---|---|---|
| A | opus | 10 | 130s | 32.1k | 79.1k |
| B | opus | 7 | 90s | 32.1k | 83.5k |
| C | opus | 9 | 172s | 32.7k | 99.4k |
| web | sonnet | 5 | 92s | 32.4k | 60.6k |

- **Overhead** (~129k of the 323k): every `general-purpose` agent starts at 32k. Tool schemas 52.5KB, of which Artifact is 37.8KB; skill listing 26.8KB; ponytail's SubagentStart persona 5.6KB; deferred-tool names 3.9KB; a code-search system prompt 2.8KB. The prompts the main session wrote were only 1.6–3.5KB.
- **Data reads** (~126k): no agent reads its JSON whole; each prints Python views of it. B and C each read all 738 typed prompts (~30k tokens each). A read ~73KB of chosen turns. Trimming JSON fields therefore barely matters.
- **Rubric** (~32k): `rubric.md` costs ~11k tokens per read. A needs 16 rows (7.4KB), B 10 (4.5KB), C 7 (3.7KB).
- **Wall time**, 418s on the critical path: `prepare` 24 (digest 2, upstream 6, news 9, ~7 probably `claude -p /usage`) → main writes A/B/C prompts 24 → C 172 (the long pole) → `/insights` review, `news`, web prompt 35 → web 92 → main writes the draft 63 → `commit` 6.
- **The main session ran on Sonnet** from the first agent hand-back on. `model: opus` (`retro/SKILL.md:3`) covers only the turn that invoked the skill; each background-agent notification starts a new turn on the session model. The user's default is now Opus.
- The main session rewrites agent text (1 of 16 Problem lines and 0 of 30 solutions verbatim), so a script-assembled draft would change the output.

## Proposals, ranked by savings

1. **`retro-worker` agent type** (~100k, estimate). `retro/agents/retro-worker.md`, symlinked as a file into `~/.claude/agents/`; `tools: Bash, Read, WebFetch, WebSearch`; no `model` (pass it per call); body holds the shared output contract. SKILL.md spawns all four with `subagent_type: retro-worker`. Filter `agent:retro-worker` out of `build_toolkit` (`retro/retro.py:623`). Check on the first run: first request ~6–8k (estimate), no skill listing, WebFetch loads without ToolSearch (else add ToolSearch).
2. **Per-agent rubric slice** (~25k). `prepare` (`retro/retro.py:1254`) copies the agent's rows verbatim with all columns, plus the table header and the notes outside the tables (`rubric.md:42` for A, `rubric.md:78` for B). A = P1–P12, C2, C3, C6, C8; B = W1–W8, C5, C6; C = S1–S7.
3. **Briefs from files** (main −2.5k context, −2.5k output tokens, ~25s). Move the agent-facing text of `retro/SKILL.md:23-28` and the agent part of `:41` verbatim into `retro/briefs/{a,b,c,web}.md`, re-voiced from "tell it to" to direct address. `prepare` writes `<tmp>/brief_<x>.md` (one per split piece too): instructions, rubric slice, input path, and for pieces the "problems in only 2 Sessions" line. The main session's prompt becomes "Read <brief> and follow it"; for web it adds only the problem list. SKILL.md keeps what the main session itself does.
4. **Script lookups for the main session** (main −7–9k). Session rows in `compute_metrics` (`:383`) gain title and project. `skills_behind` (`:899`) fetches each skill's commits (`commits?path=<dir>&since=`) instead of up to 100 repo-wide headlines. Plugin `releases_since_cursor` goes only to the web agent. Update `retro/SKILL.md:29` to match.
5. **`prepare` 24s → ~10s.** After the gate passes, start `claude -p /usage` early and read it last (`usage_line`, `:1013`). Run `fetch_news` (`:1151`) detached like `start_insights` (`:1025`); `news` (`:1215`) waits for `news_raw.json` the way `insights` waits.
6. **Spawn the web agent before the `/insights` review** (~20s). Risk: an `/insights` item confirmed into the top five misses the web search. Last run had 0 confirmed and 0 amended.
7. **Haiku for phase 2**: saves no context. Only after an A/B on one saved `news.json`.

Rejected, with reasons given to the user: trimming digest fields, merging B and C (C becomes slower and covers four categories), a script-assembled draft, script pre-matching prompts to the Toolkit for C (loses S1 matches that depend on meaning).

Outside the repo, the user's call: `PONYTAIL_SUBAGENT_MATCHER='^(?!retro-)'` under `env` in `~/.claude/settings.json` keeps ponytail's persona out of Retro agents once proposal 1 exists.

## Verifying

1. Copy `~/.claude/retro/findings.md` aside. `/retro redo` overwrites it, because `commit` skips the `.prev` rotation on a Redo.
2. In a fresh session on Opus (agent files load at session start), run `/retro redo`.
3. Run `python3 .scratch/retrosmith/runstats.py <the new Session .jsonl>`. It prints each agent's requests, time, first and final context, plus the main session's time from `/retro` to `commit` and its models. Compare with the table above.
4. Done when the new numbers sit beside the baseline and the user has compared the two findings files. The Window has moved, so judge depth and exactness, not identical content.
