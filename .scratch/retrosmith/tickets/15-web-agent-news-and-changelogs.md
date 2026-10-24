# 15: Web agent: news and changelogs

**What to build:** The web agent also reads AI-tooling news filtered at zero tokens, new official plugins, and changelogs of Toolkit items the user relies on. The results fill the Meta section and the Toolkit updates.

Details: [spec](../spec.md), section "Feeds and news filter". Sources and endpoints: [AI landscape sources](../research/04-ai-landscape-sources.md).

**Blocked by:** 14: Web agent: solutions for top problems

**Status:** done

- [x] The script fetches the shortlist's RSS, Atom and JSON sources with stdlib and date-filters them by the cursor. The two HTML-only sources (claude.com/blog, GitHub Trending) go to the web agent through WebFetch with narrow prompts. Reddit and X aren't used.
- [x] The marketplace diff compares the official `marketplace.json` at the commit before the cursor with `main` and lists new plugins.
- [x] Stage 1 scores each item by keywords: title hits 3, body hits 1, plus a bonus for official sources and high HN points. Terms come from Toolkit names, installed CLI names, platform terms, and the problem terms for categories with detected problems. Official items always pass. About 20 to 40 items survive.
- [x] The web agent also reads the changelogs of used outdated Toolkit items (tickets 10 and 11) and writes their **What changed** against the problem list.
- [x] Stage 2 keeps an item only if it changes how an installed item should be used, or addresses a detected problem. It becomes a Meta item, or a solution inline in a problem's Finding.
- [x] Verify: `/retro redo`. The Meta section is short and relevant, and the ponytail update explains what changed.
