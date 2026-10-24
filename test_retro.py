"""Run: python3 test_retro.py"""
import sys
sys.path.insert(0, "retro")
import retro

DOCS = """# Commands
Source: https://code.claude.com/docs/en/commands

| `/clear [name]` | Start a new conversation. Aliases: `/reset`, `/new` |
| `/effort [low\\|high]` | Set the [effort level](/docs/en/model-config#adjust-effort-level) |
| `/loop [interval]` | **[Skill](/docs/en/skills#bundled-skills).** Run a prompt repeatedly |
| `/tasks` | View background work. Also available as `/bashes` |
# Next page
Source: https://code.claude.com/docs/en/other

| `/not-a-command` | Another page's table |
"""

rows = {n: (o, d) for n, o, d in retro.doc_commands(DOCS)}
assert set(rows) == {"clear", "reset", "new", "effort", "loop", "tasks", "bashes"}, rows
assert rows["loop"] == ("bundled skill", "Run a prompt repeatedly"), rows["loop"]
assert rows["effort"] == ("built-in command", "Set the effort level"), rows["effort"]
assert rows["new"][0] == "built-in command"
assert retro.doc_commands("no commands page") == []

hits = retro.destructive
assert hits("python3 - <<'EOF'\nrow = 'deny git push --force'\nEOF") == []
assert hits("git push origin main --force") == ["git push --force"]
assert hits("git push -f") == ["git push --force"]
assert hits("git push --force-with-lease") == []
assert hits("cd x && git reset --hard HEAD~1") == ["git reset --hard"]
assert hits("git clean -fd") == ["git clean -f"]
assert hits("git branch -D old") == ["git branch -D"]
assert hits("git branch -d merged") == []

assert retro.SECRET.search("use key sk-ant-api03-" + "a" * 30)
assert retro.SECRET.search("AKIA" + "A" * 16)
assert not retro.SECRET.search("ask the skill to look at task-ant-colony")
print("ok")
