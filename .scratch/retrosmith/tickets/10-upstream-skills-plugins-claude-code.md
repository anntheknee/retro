# 10: Upstream for skills, plugins and Claude Code

**What to build:** The Toolkit updates section shows which skills, plugins and Claude Code built-ins are behind upstream, with no stored list.

Details: [spec](../spec.md), sections "Toolkit inventory and upstream", "Gate, Window, and cursor".

**Blocked by:** 09: Follow-through

**Status:** done

- [x] Each recorded pin is compared with upstream in about 6 network calls: one tree or compare call per skill source repo, the synced manifest dates, plugin and marketplace versions or commits, and Claude Code's installed version against its releases.
- [x] Skills removed upstream are flagged.
- [x] Commits and releases are scoped to the cursor: the previous Retro's Timestamp; for a Redo, the timestamp in the previous-findings file; otherwise 30 days back.
- [x] Claude Code releases count as the upstream of built-in commands, bundled skills and agents.
- [x] Each item that is behind becomes a Toolkit update with **What changed** in place of **Problem**, its use in the Window, and the exact update command. Changelog judgment arrives in ticket 15.
- [x] Verify: `/retro redo` shows ponytail behind upstream, the changed mattpocock skills, and `resolving-merge-conflicts` removed upstream.
