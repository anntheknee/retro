# 02: Statusline reminder

**What to build:** The statusline shows when a Retro is due and how many days a late one has lost, and every `/retro` run offers to wire it up.

Details: [spec](../spec.md), section "Statusline reminder".

**Blocked by:** 01: Skeleton: gate, Redo, commit

**Status:** done

- [x] `retro.py status` reads the Retro Timestamp from the findings file and prints: nothing before day 30; `retro due` on day 30; `retro overdue · Nd lost` after that, orange for 1 to 6 days and red from 7; `retro due` when no findings file exists. No quota.
- [x] The 30-day constant and the frontmatter format are shared with the gate and live only in `retro.py`.
- [x] On every run, above or below the gate, `prepare` checks the user's `statusLine` setting (and the script it names) for a `retro.py status` call, and prints a hint when it's missing.
- [x] When the hint is printed, Claude's last step offers the edit: append one call joined with ` · ` to a statusline script; append the call to an inline command; or set `statusLine` to the call when none exists. Claude edits with its normal tools after a yes.
- [x] `retro.py` holds no installer code, and a decline isn't stored.
- [x] Verify: run `status` with no findings file, and with the frontmatter timestamp moved back by hand to 20, 30, 33 and 40 days. Accept the offer once and see the segment.
