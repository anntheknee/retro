# AI landscape sources

Type: research
Status: resolved
Blocked by:

## Question

Which high-signal sources track Claude Code / agentic-coding tooling news and best practices (Anthropic changelog and blog, Claude Code GitHub releases, HN, subreddits, curated "awesome" lists, newsletters, notable people)? How well can each be read with built-in WebSearch/WebFetch (paywalls, login walls, JS-only pages)? Recommend a shortlist plus a way to filter for relevance to the user's Toolkit and problems.

## Answer

Shortlist of 10 sources. Official updates: Claude Code releases API (100 releases deep; the changelog RSS holds only 15 and the Atom feed 10), the "What's new" digest (lagging since Week 37), claude.dev RSS, and claude.com/blog. Community and new tools: HN Algolia API with date and points filters, GitHub Trending, a stateless official marketplace.json diff, awesome-claude-code `Add resource:` commits, and Simon Willison's claude-code tag.
Reddit and X are unreachable (blocked, 403, 402). WebSearch has no date filter, so use it only for follow-ups.
Everything except two HTML pages is RSS, Atom, or JSON, so the helper script should fetch and date-filter with stdlib, and score items by Toolkit and problem keywords. The LLM judges only the survivors. The Retro Timestamp is the only cursor.

[findings](../research/04-ai-landscape-sources.md)
