# Retrosmith

A periodic self-review of how one person uses Claude Code, with advice on working more effectively.

## Language

**Session**:
One Claude Code conversation, as recorded by Claude Code's own transcript.
_Avoid_: chat, conversation log

**Retro**:
One run of the review. It analyzes the Window, checks follow-through on the previous Retro's Findings, scans the web, and produces new Findings.
_Avoid_: report, analysis run

**Window**:
The Session activity a Retro analyzes: the 30 days before the Retro starts. Retros are at least 30 days apart, so no activity falls in two Windows; a late Retro leaves a gap that no Window covers. A Session resumed across a Retro contributes only its activity inside each Window.

**Retro Timestamp**:
The moment the previous Retro started. The next Retro may run 30 days after it. Advances only when a Retro's Findings are written; an aborted Retro leaves it unchanged. The only state carried between Retros besides the previous Findings.
_Avoid_: watermark

**Redo**:
A Retro that replaces the latest one instead of following it. It skips the 30-day gate and checks follow-through against the Findings the latest Retro itself checked, so regenerating never loses that baseline. Before any Retro exists, it is simply a first Retro run early.
_Avoid_: force, rerun

**Toolkit**:
Everything Claude or the user can invoke: installed skills, plugins, MCP servers, and CLIs such as openspec, plus Claude Code's own built-in commands, bundled skills and agents.

**Finding**:
One piece of advice from a Retro, backed by evidence from specific Sessions or sources. Offers up to three solutions. The user applies one later by asking Claude. The next Retro judges whether it was adopted from what actually changed; a Finding carries no status. Each has an **origin**: the Retro itself, `/insights` (a second opinion the Retro reviewed), or the web.

**Overlap**:
Two or more Toolkit items that do the same job, whether or not both are used. A Retro resolves it with **pick-one** (keep one, remove the rest) or **merge-and-own** (combine them into an Owned Skill and remove the originals).
_Avoid_: duplicate (for an overlap whose members differ in detail)

**Owned Skill**:
A skill the user maintains, built from one or more upstream skills (or from an edited install). The Retro keeps watching each upstream source and offers to port changes to the parts the skill kept.
_Avoid_: fork, custom skill

## Relationships

- A **Retro** analyzes exactly one **Window** and produces many **Findings**
- The next **Retro** reads only the previous Retro's **Findings**; older ones are discarded, except that a **Redo** reads the Findings the Retro it replaces read
- A **Window** ends when the Retro starts and reaches back 30 days
- A **Retro** runs only when 30 days have passed since the **Retro Timestamp** (or, for the first Retro, since the user's first recorded prompt); otherwise it does nothing and the **Retro Timestamp** stays put. A **Redo** skips this gate
- A **Retro**'s own Session, from `/retro` onward, belongs to no **Window**

## Flagged ambiguities

- "timestamp" alone collides with the per-message timestamps inside transcripts; resolved as **Retro Timestamp**.
