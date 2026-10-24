# AI landscape sources

Ticket: [04-ai-landscape-sources](../wayfinder-issues/04-ai-landscape-sources.md)
Tested: 2026-10-20, with Claude Code WebFetch / WebSearch, plus `curl` for headers and item counts. Every "fetchability" result below is a live test from that day.

## Question

Which high-signal sources track Claude Code and agentic-coding news and best practices? How well can built-in WebSearch/WebFetch read each one? Recommend a shortlist and a relevance filter tied to the Toolkit and detected problems.

Scope note: upstream release tracking for each *installed* Toolkit item (openspec, gh, individual plugins) belongs to ticket 03. This ticket covers the general meta and discovery of *new* tools. Claude Code itself appears in both places, because it is the platform.

## Recommended shortlist

| # | Source | Endpoint to read | Signal | Fetch result (2026-10-20) | Why |
|---|---|---|---|---|---|
| 1 | Claude Code releases (official) | `https://api.github.com/repos/anthropics/claude-code/releases?per_page=100` (filter `published_at > Retro Timestamp`) | Official updates | OK. JSON with `tag_name`, `published_at`, and full `body` per release. 100 releases span v2.1.186 (2026-06-22) to v2.1.304 (2026-10-19). 23 of them fall after 2026-09-20. | The only official feed deep enough for a monthly Window. About one release per day, so a month holds roughly 25–30 releases. |
| 2 | Claude Code changelog RSS (official) | `https://code.claude.com/docs/en/changelog/rss.xml` | Official updates | OK. RSS 2.0 with dated items and `<ul>` bullets in `content:encoded`. **Only 15 items** (2.1.288 to 2.1.304, back to 2026-10-02). | Cleanest format for a short Window. Fall back to #1 when the Window starts before the oldest item. |
| 3 | Claude Code "What's new" weekly digest (official) | `https://code.claude.com/docs/en/whats-new/rss.xml`, index at `https://code.claude.com/docs/en/whats-new` | Official updates plus "why it matters" | OK, but **lagging**. The newest entry is Week 37 (Sep 7–11, 2026), with nothing for weeks 38–42. RSS `pubDate`s are re-stamped (several share 2026-09-15 00:33:44) and out of order, so filter on the week label or version range, not `pubDate`. | Curated headline features with usage context. Higher signal per token than raw release notes when it is current. |
| 4 | claude.dev blog (Anthropic developers) | `https://claude.dev/rss.xml` | Practitioner tips (first party) | OK. RSS 2.0 with summaries only (no `content:encoded`). Latest: "How the Claude Code team does code review", 2026-10-15. | "Tips, tricks, and POVs from Anthropic's developers": playbooks, skills, mods. Directly about how to use Claude Code better. |
| 5 | claude.com blog (Anthropic) | `https://www.claude.com/blog` (HTML page, no feed) | Official announcements plus engineering posts | OK through WebFetch. Dated list; latest "Redesigning source control at Anthropic", 2026-10-19. No RSS (`/blog/rss.xml` returns 404). The page is not strictly chronological. | Product launches (for example "Code Review is now generally available", 2026-10-15). Also republishes anthropic.com/engineering posts, so it supersedes that page. |
| 6 | Hacker News via Algolia API | `https://hn.algolia.com/api/v1/search_by_date?query=claude%20code&tags=story&restrictSearchableAttributes=title&numericFilters=created_at_i>{ts},points>50&hitsPerPage=50` | Community meta, new tools, problems | OK. JSON with `title`, `url`, `points`, `num_comments`, `created_at`. The 2026-09-20 to 2026-10-20 query returned 208 hits. Without `restrictSearchableAttributes=title`, unrelated Show HNs leak in. | Native date and points filters make "since last Retro" one request. The best community signal reachable without login. Run a second query for `"agent skills" OR "coding agent"`. |
| 7 | GitHub Trending (weekly/monthly) | `https://github.com/trending?since=monthly` (HTML) | New tools | OK through WebFetch. 4 of the top 8 weekly repos were agent-related, for example `mksglu/context-mode` ("context window optimization for AI coding agents") and `anthropics/claude-plugins-official`. | Fast discovery of tools that are gaining traction. `since=monthly` roughly matches a monthly Window. |
| 8 | Official plugin marketplace diff | `https://raw.githubusercontent.com/anthropics/claude-plugins-official/{ref}/.claude-plugin/marketplace.json` at `{ref}` = the commit before the Retro Timestamp (`/commits?until={ts}&per_page=1`) versus `main` | New tools (official) | OK. Stateless diff from 2026-09-20 to now: 310 to 315 plugins. New: `amazon-selling-partner`, `data-agent-kit`, `govtribe`, `linq-alpha`, `math-proof`, `vanguard-advisor-tools`. The commit feed alone is useless: 100 of 100 recent `marketplace.json` commits are `bump(...)`. | Gives exactly the plugins added since the last Retro, needs no stored state, and respects "store nothing". |
| 9 | awesome-claude-code | `https://api.github.com/repos/hesreallyhim/awesome-claude-code/commits?since={ts}&per_page=100`, keep messages starting `Add resource:` | New tools (community-curated) | OK. 12 of the last 100 commits are `Add resource: …` (for example Cubicle Crew, geoai-skills, Mycelium). The rest are bot `chore: update repo ticker` commits, so page through or filter. The Atom feed works but is mostly bot noise. 56.1k stars. | A human-curated intake of skills, hooks, status lines, and plugins. Each commit names one vetted resource. |
| 10 | Simon Willison, `claude-code` tag | `https://simonwillison.net/tags/claude-code.atom` | Practitioner tips, notable people | OK. Atom with dates. Latest 2026-10-16 ("Quoting Addy Osmani…"), with earlier quotes of Thariq Shihipar and Boris Cherny. | The most reliable single practitioner feed. It also relays posts by Claude Code team members whose own channels (X) are unreachable. |

Optional, high volume: **Latent Space / AINews** (`https://www.latent.space/feed`). Valid RSS, a daily issue (latest 2026-10-20), some items cut off at "Read more". It is broad AI-industry meta (885k chars per fetch) with a low share of Claude Code content. Use it only with keyword pre-filtering in the script.

## Rejected candidates

| Candidate | Result | Reason |
|---|---|---|
| Reddit r/ClaudeAI, r/ClaudeCode (`.json`, `.rss`, old.reddit) | WebFetch: "unable to fetch from www.reddit.com / old.reddit.com". curl: 403 or "Blocked" / "Welcome to Reddit" login page. | Unreachable. WebSearch with `site:reddit.com` returned no reddit threads at all. HN covers most of the same stories. |
| X / Twitter (for example `x.com/bcherny`) | HTTP 402 | Login wall. Reach these people through Simon Willison's quotes, HN, and claude.dev. |
| hnrss.org (`/newest?q=…&points=50`) | WebFetch failed with 502 twice, then worked. curl 200. | Flaky, and it is a wrapper over the Algolia API, so use the origin (#6). |
| `raw.githubusercontent.com/anthropics/claude-code/main/CHANGELOG.md` | OK, but 1,056,445 chars and no dates | Too big and undated. #1 and #2 carry the same bullets with dates. |
| `github.com/anthropics/claude-code/releases.atom` | OK, but only 10 entries | Too shallow for a monthly Window. Use the API (#1). |
| anthropic.com/news | OK, no RSS (`/rss.xml` 404) | Mostly corporate and policy news (offices, midterms, usage policy). Product news also appears on claude.com/blog. |
| anthropic.com/engineering | OK | Sparse (newest dated post 2026-05-25), and its posts also appear on claude.com/blog (#5). |
| news.smol.ai (AINews) | OK, but newest issue 2026-09-10 | AINews now publishes on latent.space (see optional item). |
| Lobsters `t/ai.rss` | OK | 0 of 6 recent items about coding agents. ML-research heavy. |
| Pragmatic Engineer feed | OK, but some items are teaser + "Read more" | Partly paywalled, and Claude Code content is incidental. |
| Armin Ronacher (`lucumr.pocoo.org/feed.atom`) | OK | Good but infrequent (about one agent post a month). Covered when HN surfaces it. |
| GitHub repo search `topic:claude-code created:>{ts}` | OK (25,650 hits) | Stars-sorted results are noisy (for example `cleanyourtv`). Trending (#7) and awesome-claude-code (#9) filter better. |
| anthropics/skills commits | OK | Only `claude-api` skill updates lately. Upstream tracking for installed skills is ticket 03's job. |
| Generic WebSearch ("Claude Code new skill plugin October 2026") | Returns SEO listicles, mostly mid-2026 or older | WebSearch has no date parameter and is US-only. Use it only for targeted follow-ups ("tool Y vs Z", "fix for problem X"), not discovery. |

## Fetching approach

- **Prefer the helper script for feeds and APIs.** Every endpoint above except #5 and #7 is RSS, Atom, or JSON. Python stdlib (`urllib`, `xml.etree`, `json`) parsed them with no API key; the unauthenticated GitHub API is enough for a handful of calls per Retro. WebFetch sends every page through a summarizing model and truncates at 100k chars per call: the releases API page was 128k, the Latent Space feed 885k. Script-side parsing is exact and costs no tokens, which fits the standing token-cost preference. Ticket 07 (script vs. skill boundary) should confirm this split.
- **Use WebFetch for HTML-only pages** (claude.com/blog, GitHub Trending, and article bodies the LLM decides to read). Give it a narrow prompt, such as "list posts dated after {Retro Timestamp}".
- **Use WebSearch only for follow-ups**, never for discovery.

## Relevance filter

Two stages, so the LLM sees about 20–40 candidates instead of hundreds.

**Stage 1, in the script (keyword score, no tokens):**

1. Build a term list from the Toolkit inventory: installed skill names, plugin names, MCP server names, CLI names from the Window plus the watch list (`openspec`, `gh`, …), and fixed platform terms (`claude code`, `skill`, `plugin`, `hook`, `subagent`, `MCP`, `marketplace`).
2. Add terms from the problems the Window detected, mapped by category:

| Problem category (map.md) | Terms |
|---|---|
| 1 prompting quality | prompt, plan mode, CLAUDE.md, AGENTS.md, instructions |
| 2 context management | context, compaction, `/clear`, memory, 1M, rewind, fork |
| 3 skills not used | skill, trigger, description, `/skill-doctor` |
| 4 repeated questions | memory, CLAUDE.md, docs, llms.txt |
| 5 cost/token hotspots | usage, token, cost, effort, `/usage`, fast mode, model |
| 6 corrections and rework | review, verify, test, `/code-review`, goal |
| 7 permission friction | permission, auto mode, allow, deny, sandbox |
| 8 manual workflows to skill | workflow, routine, loop, hook, automation, mod |
| 9 toolkit overlap | duplicate, merge, plugin list, marketplace |

3. Score each item: title hits ×3, body/summary hits ×1, a bonus for official sources (#1–#5) and for HN `points` above a threshold. Keep items over the threshold, plus every official item (official changes always pass).

**Stage 2, in the LLM (judgment):** for each surviving item, answer two questions: "Does this change how the user should use an installed Toolkit item?" and "Does it address a problem detected in this Window?" Emit a Finding only on a yes, and cite both the source URL and the Session evidence. This produces the "you keep hitting X; tool Y solves it" link listed under "Not yet specified" in map.md.

## "Since last Retro" strategy

Use the Retro Timestamp `{ts}` (ISO 8601 and Unix seconds) as the only cursor. No per-source state.

| Source | How to date-filter |
|---|---|
| #1 releases API | `published_at > ts`; if the oldest of 100 is still newer than `ts`, request `&page=2` |
| #2 changelog RSS | `pubDate > ts`; if the oldest item is newer than `ts`, switch to #1 |
| #3 What's new | parse the week label or version range; include weeks whose versions are above the last version from the previous Retro's window, or whose dates are after `ts` (do not trust `pubDate`) |
| #4 claude.dev RSS, #10 Simon Willison Atom, optional Latent Space | `pubDate` / `published > ts` |
| #5 claude.com/blog | WebFetch prompt: "list posts dated after {ts}" (the page is not strictly chronological, so scan the whole list) |
| #6 HN Algolia | `numericFilters=created_at_i>{unix_ts},points>50` |
| #7 GitHub Trending | `since=monthly` if `ts` is more than 2 weeks old, else `since=weekly`. Trending has no exact date filter (accepted approximation). |
| #8 marketplace diff | `commits?until={ts}&per_page=1` gives the old ref; diff plugin names against `main` |
| #9 awesome-claude-code | `commits?since={ts}`, keep `Add resource:` messages, page while 100 come back |

First Retro (no `ts`): default to 30 days back, matching the planned monthly cadence.

## Sources

All tested 2026-10-20:

- https://api.github.com/repos/anthropics/claude-code/releases?per_page=100
- https://github.com/anthropics/claude-code/releases.atom
- https://raw.githubusercontent.com/anthropics/claude-code/main/CHANGELOG.md
- https://code.claude.com/docs/en/changelog and https://code.claude.com/docs/en/changelog/rss.xml
- https://code.claude.com/docs/en/whats-new and https://code.claude.com/docs/en/whats-new/rss.xml
- https://code.claude.com/docs/llms.txt
- https://claude.dev/blog and https://claude.dev/rss.xml
- https://www.claude.com/blog
- https://www.anthropic.com/news and https://www.anthropic.com/engineering
- https://hn.algolia.com/api/v1/search_by_date (queries above)
- https://hnrss.org/newest?q=claude+code&points=50
- https://github.com/trending?since=weekly
- https://raw.githubusercontent.com/anthropics/claude-plugins-official/main/.claude-plugin/marketplace.json, plus the `commits` API and Atom feed for that repo
- https://github.com/hesreallyhim/awesome-claude-code, its `commits` API, and its Atom feed
- https://github.com/anthropics/skills/commits/main.atom
- https://simonwillison.net/atom/everything/ and https://simonwillison.net/tags/claude-code.atom
- https://www.latent.space/feed and https://news.smol.ai/
- https://lobste.rs/t/ai.rss
- https://newsletter.pragmaticengineer.com/feed
- https://lucumr.pocoo.org/feed.atom
- https://www.reddit.com/r/ClaudeAI/top/.json, https://old.reddit.com/r/ClaudeCode/top/.rss (blocked)
- https://x.com/bcherny (402)
- https://api.github.com/search/repositories?q=topic:claude-code
