# Prompting and context best practices

Type: research
Status: resolved
Blocked by:

## Question

What do primary sources (Anthropic docs for Claude Code and prompting, official best-practice guides) recommend on prompt quality, context management (`/clear`, `/compact`, session length, CLAUDE.md, subagents), and using skills well? Distill a rubric a Retro can judge categories 1, 2, 3 and 8 against, with each item citing its source.

## Answer

Anthropic's docs build almost every practice on one constraint: context fills fast and performance degrades as it fills. The rubric has 42 checkable items: 12 for prompt quality, 15 for context management, 7 for using skills, and 8 for skill-worthy workflows. Each item names the anti-pattern a Retro can spot in a transcript and its source.
The sources give ready-made thresholds: `/clear` after two failed corrections; a mistake made twice goes into CLAUDE.md; a playbook pasted three times becomes a skill; CLAUDE.md under 200 lines; SKILL.md under 500 lines. They also name failure patterns: kitchen sink session, correcting over and over, over-specified CLAUDE.md, trust-then-verify gap, infinite exploration.
Custom commands are now skills, so category 8 proposes skills (or hooks or subagents, depending on the trigger).
The script can detect most items; each is tagged `script` or `LLM`.
For the spec: built-in `/insights`, `/doctor prompt-audit`, and `/skill-doctor` already cover part of this ground.

[findings](../research/05-prompting-and-context-best-practices.md)
