## Where a fix goes

Work on code runs in two stages: the Session that writes it explores, edits and debugs under the most context pressure, and review reads only a diff. CLAUDE.md loads into every Session, so it is the costliest home for a rule. Give every fix the cheapest home that still holds, including a CLAUDE.md entry the rubric suggests:

- **Mechanical** (a mistake a linter, typechecker or test catches; a fixed pattern such as a banned command or API, an import shape or a file location; a step that must run every time): build a check rather than write a rule. Pick whatever the project's language and **guardrail** (the hooks, pre-commit and CI jobs that run its checks) make cheapest: a Claude Code hook, a linter rule, a pre-commit hook or a CI job. Read the project's own check setup first (`package.json` or `pyproject.toml` scripts, the CI workflow, the pre-commit config, `.claude/settings.json` hooks): a check that exists but sits unwired or broken is the fix. A check holds only once a guardrail runs it.
- **Judgement** about code (consistency across files, matching the surrounding style): a line in the project's `CODING_STANDARDS.md`, which `/pocock-review` checks at review.
- Facts Claude keeps looking up or being told (where code lives, a command, a decision): a **navigation pointer**, one CLAUDE.md line naming the file or doc and when to read it. Point to an existing doc before writing a new one.
- Information Claude can't reach, so the user keeps pasting it (server logs, browser console, a dashboard): access, such as output teed to a file a navigation pointer names, or read-only access through a CLI or MCP server.
- A procedure: a skill.
- How Claude works with the user (when to ask, commit or explain): a CLAUDE.md line. These and navigation pointers are all CLAUDE.md should hold.

A line that changes nothing Claude does by default is a **no-op**: propose none.
