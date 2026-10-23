#!/usr/bin/env python3
"""Helper for the /retro skill. Claude runs these subcommands; the user never does."""
import json, math, re, shutil, subprocess, sys, tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

GATE_DAYS = 30
HOME = Path.home() / ".claude"
STATE = HOME / "retro"
FINDINGS = STATE / "findings.md"
PREV = STATE / "findings.prev.md"
HISTORY = HOME / "history.jsonl"

SKELETON = """Sessions: 0 · Projects: 0 · Findings: 0

## Failed parts

## Follow-through

## Findings

## Toolkit updates

## Meta

## `/insights` review
"""


def now():
    return datetime.now(timezone.utc)


def findings_timestamp(path):
    m = re.search(r"^retro_timestamp: (\S+)$", path.read_text().split("---")[1], re.M)
    return datetime.fromisoformat(m.group(1))


def last_retro_start():
    """Start of the gate period: the Retro Timestamp, else the oldest history entry."""
    if FINDINGS.exists():
        return findings_timestamp(FINDINGS)
    try:
        with HISTORY.open() as f:
            first = json.loads(f.readline())
        return datetime.fromtimestamp(first["timestamp"] / 1000, timezone.utc)
    except (OSError, ValueError, KeyError):
        return None


def status():
    if not FINDINGS.exists():
        print("retro due")
        return
    days = (now() - findings_timestamp(FINDINGS)).days
    if days == GATE_DAYS:
        print("retro due")
    elif days > GATE_DAYS:
        lost = days - GATE_DAYS
        color = "38;5;208" if lost < 7 else "31"
        print(f"\033[{color}mretro overdue · {lost}d lost\033[0m")


def statusline_hint():
    """Return a hint when the user's statusLine doesn't call `retro.py status`, else None."""
    try:
        cmd = json.loads((HOME / "settings.json").read_text())["statusLine"]["command"]
    except (OSError, ValueError, KeyError, TypeError):
        return "Statusline hint: no statusLine set; offer to set it to the `retro.py status` call."
    text = cmd
    for word in cmd.split():
        try:
            f = Path(word).expanduser()
            if f.is_file():
                text += f.read_text()
        except (OSError, ValueError, RuntimeError):
            pass  # unreadable word in the command: judge by what we have
    if "retro.py status" in text:
        return None
    return f"Statusline hint: statusLine ({cmd}) has no `retro.py status` call; offer to add it."


def usage_line():
    try:
        out = subprocess.run(["claude", "-p", "/usage"], capture_output=True, text=True, timeout=60).stdout
        lines = [l.strip() for l in out.splitlines() if "%" in l]
        return "Plan usage: " + " | ".join(lines) if lines else "Plan usage: unavailable"
    except Exception:
        return "Plan usage: unavailable"


def prepare(redo):
    hint = statusline_hint()
    start = now()
    if not redo:
        began = last_retro_start()
        if began is None:
            print("No usable history.jsonl yet, so no Retro is possible.")
            return
        left = began + timedelta(days=GATE_DAYS) - start
        if left > timedelta(0):
            print(f"Too soon for a Retro: {math.ceil(left / timedelta(days=1))} days left.")
            if hint:
                print(hint)
            return
    tmp = Path(tempfile.mkdtemp(prefix="retro-"))
    (tmp / "state.json").write_text(json.dumps({"redo": redo, "timestamp": start.isoformat()}))
    (tmp / "draft.md").write_text(SKELETON)
    print(usage_line())
    if hint:
        print(hint)
    print(f"Temp folder: {tmp}")


def commit(draft):
    draft = Path(draft)
    tmp = draft.parent
    state = json.loads((tmp / "state.json").read_text())
    STATE.mkdir(parents=True, exist_ok=True)
    new = FINDINGS.with_suffix(".md.tmp")
    new.write_text(f"---\nretro_timestamp: {state['timestamp']}\n---\n\n{draft.read_text()}")
    if not state["redo"] and FINDINGS.exists():
        FINDINGS.replace(PREV)
    new.replace(FINDINGS)
    if tmp.name.startswith("retro-"):
        shutil.rmtree(tmp)
    print(FINDINGS)
    subprocess.run(["open", str(FINDINGS)])


if __name__ == "__main__":
    cmd, args = (sys.argv[1], sys.argv[2:]) if len(sys.argv) > 1 else ("", [])
    if cmd == "prepare":
        prepare("--redo" in args)
    elif cmd == "status":
        status()
    elif cmd == "commit" and args:
        commit(args[0])
    else:
        sys.exit("usage: retro.py prepare [--redo] | commit <draft.md> | status")
