#!/usr/bin/env python3
"""Helper for the /retro skill. Claude runs these subcommands; the user never does."""
import collections, glob, json, math, re, shutil, subprocess, sys, tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

GATE_DAYS = 30
HOME = Path.home() / ".claude"
STATE = HOME / "retro"
FINDINGS = STATE / "findings.md"
PREV = STATE / "findings.prev.md"
HISTORY = HOME / "history.jsonl"
PROJECTS = HOME / "projects"
PROMPT_MAX = 300
# Record types the digest knows about or deliberately drops; anything else counts as format drift.
KNOWN_TYPES = {
    "assistant", "attachment", "user", "api-request-blob", "mode", "atis-latch", "last-prompt",
    "api-request", "ai-title", "system", "file-history-snapshot", "bridge-session", "permission-mode",
    "queue-operation", "file-history-delta", "cost-state", "api-request-shape", "agent-color",
    "pr-link", "custom-title",
}

SKELETON = """Sessions: {sessions} · Projects: {projects} · Findings: 0

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


def iso(dt):
    return dt.strftime("%Y-%m-%dT%H:%M:%S.000Z")


def text_of(c):
    if isinstance(c, str):
        return c
    return " ".join(x.get("text", "") for x in c if isinstance(x, dict) and x.get("type") == "text")


def digest_session(path, lo, hi, parent_cut=None):
    """Digest one transcript, keeping only records in [lo, hi). Returns (digest, own_cut, drift).

    A typed `/retro` cuts the Session from that prompt onward; a subagent is cut at its parent's cut.
    Returns digest None for a headless Session the Retro itself started.
    """
    d = {"file": str(path.relative_to(PROJECTS)), "versions": set(), "models": collections.Counter(),
         "effort": collections.Counter(), "tokens": collections.Counter(), "peak_ctx": 0,
         "tools": collections.Counter(), "bash_heads": collections.Counter(),
         "skills_invoked": collections.Counter(), "slash": collections.Counter(),
         "attrib_skill_out": collections.Counter(), "tool_errors": [], "denials": collections.Counter(),
         "interrupts": 0, "compactions": [], "api_errors": 0, "informational": [], "turns": [],
         "perm_modes": collections.Counter()}
    listing = None
    reqs, cur, first, last, cut, drift, seen_user = {}, None, None, None, None, 0, False
    cutoff = parent_cut or "￿"
    try:
        lines = path.open(errors="replace").readlines()
    except OSError:
        return None, None, 1
    for line in lines:
        try:
            r = json.loads(line)
            if not isinstance(r, dict):
                drift += 1
                continue
            t, ts = r.get("type"), r.get("timestamp")
            if ts and ts >= cutoff:
                break
            if t == "user" and not seen_user:
                seen_user = True
                if r.get("entrypoint") == "sdk-cli" and re.search(r"<command-name>/?(usage|insights)<", str(r.get("message"))):
                    return None, None, drift
            if ts and not lo <= ts < hi:
                continue
            if t not in KNOWN_TYPES:
                drift += 1
                continue
            if ts:
                first = first or ts
                last = ts
            if r.get("version"):
                d["versions"].add(r["version"])
            for k in ("cwd", "gitBranch", "agentId"):
                if r.get(k) and k not in d:
                    d[k] = r[k]
            if t == "ai-title":
                d["title"] = r.get("aiTitle")
            elif t == "permission-mode":
                d["perm_modes"][r.get("permissionMode")] += 1
            elif t == "cost-state":
                d["cost_usd"] = max(d.get("cost_usd", 0), r.get("totalCostUSD") or 0)
            elif t == "assistant":
                m = r.get("message") or {}
                reqs[r.get("requestId") or r.get("uuid")] = (m.get("model"), m.get("usage") or {}, r.get("attributionSkill"))
                d["effort"][str(r.get("effort"))] += 1
                if r.get("isApiErrorMessage"):
                    d["api_errors"] += 1
                for c in m.get("content") or []:
                    if isinstance(c, dict) and c.get("type") == "tool_use":
                        n = c.get("name")
                        d["tools"][n] += 1
                        if cur:
                            cur["tools"][n] += 1
                        inp = c.get("input") or {}
                        if n == "Skill":
                            d["skills_invoked"][inp.get("skill")] += 1
                        if n == "Bash":
                            cmd = (inp.get("command") or "").strip().split()
                            if cmd:
                                d["bash_heads"][" ".join(cmd[:2]) if cmd[0] in ("git", "gh", "npm", "uv", "claude", "openspec") else cmd[0]] += 1
            elif t == "user":
                c = (r.get("message") or {}).get("content")
                if r.get("toolDenialKind"):
                    d["denials"][r["toolDenialKind"]] += 1
                pd = r.get("permissionDecision") or {}
                if pd.get("decision") == "reject" or (pd.get("source") or "").startswith("user"):
                    d["denials"]["pd:%s/%s" % (pd.get("decision"), pd.get("source"))] += 1
                if isinstance(c, list):
                    for x in c:
                        if isinstance(x, dict) and x.get("type") == "tool_result" and x.get("is_error"):
                            cc = x.get("content")
                            d["tool_errors"].append((cc if isinstance(cc, str) else json.dumps(cc))[:80])
                s = text_of(c) if c else ""
                if s.startswith("[Request interrupted"):
                    d["interrupts"] += 1
                    if cur:
                        cur["interrupted"] = True
                    continue
                if (r.get("isMeta") or r.get("toolUseResult") is not None or r.get("isCompactSummary")
                        or (r.get("origin") or {}).get("kind", "human") != "human"
                        or r.get("promptSource") == "system"):
                    continue
                mm = re.search(r"<command-name>/?(.*?)</command-name>", s)
                if mm:
                    if mm.group(1) == "retro":
                        cut = ts
                        break
                    d["slash"][mm.group(1)] += 1
                    continue
                if not s or s.startswith("<"):
                    continue
                cur = {"ts": ts, "len": len(s), "prompt": s[:PROMPT_MAX], "tools": collections.Counter()}
                d["turns"].append(cur)
            elif t == "system":
                st = r.get("subtype")
                if st == "turn_duration" and cur:
                    cur["ms"] = r.get("durationMs")
                elif st == "compact_boundary":
                    cm = r.get("compactMetadata") or {}
                    d["compactions"].append({k: cm.get(k) for k in ("trigger", "preTokens", "postTokens")})
                elif st == "informational":
                    d["informational"].append((r.get("content") or "")[:80])
            elif t == "attachment":
                a = r.get("attachment") or {}
                if a.get("type") == "skill_listing" and a.get("isInitial"):
                    listing = a.get("names")
        except Exception:
            drift += 1
    for model, u, sk in reqs.values():
        d["models"][model] += 1
        tok = {"in": u.get("input_tokens", 0), "cache_read": u.get("cache_read_input_tokens", 0),
               "cache_write": u.get("cache_creation_input_tokens", 0), "out": u.get("output_tokens", 0),
               "thinking": (u.get("output_tokens_details") or {}).get("thinking_tokens", 0)}
        d["tokens"].update(tok)
        d["peak_ctx"] = max(d["peak_ctx"], tok["in"] + tok["cache_read"] + tok["cache_write"])
        if sk:
            d["attrib_skill_out"][sk] += tok["out"]
    d["start"], d["end"], d["requests"] = first, last, len(reqs)
    d["versions"] = sorted(d["versions"])
    d["tool_errors"] = collections.Counter(d["tool_errors"]).most_common(10)
    d["bash_heads"] = dict(d["bash_heads"].most_common(15))
    d["listing"] = listing
    return (d if first else None), cut, drift


def build_digest(start):
    """Digest every Session in the Window [start-30d, start). Returns the digest dict."""
    lo, hi = iso(start - timedelta(days=GATE_DAYS)), iso(start)
    files = [Path(f) for f in glob.glob(str(PROJECTS / "**" / "*.jsonl"), recursive=True)]
    mains = [f for f in files if f.parent.name != "subagents"]
    subs = [f for f in files if f.parent.name == "subagents"]
    sessions, cuts, drift = [], {}, 0
    for f in mains:
        d, cut, n = digest_session(f, lo, hi)
        drift += n
        if cut:
            cuts[f.stem] = cut
        if d:
            sessions.append(d)
    for f in subs:
        d, _, n = digest_session(f, lo, hi, cuts.get(f.parent.parent.name))
        drift += n
        if d:
            try:
                d["agent"] = json.loads(f.with_suffix(".meta.json").read_text())
            except (OSError, ValueError):
                pass
            sessions.append(d)
    sessions.sort(key=lambda d: d["start"])
    listings = {}
    for d in sessions:
        for name in d.pop("listing") or []:
            e = listings.setdefault(name, {"first": d["file"], "last": d["file"]})
            e["last"] = d["file"]
    history = []
    try:
        for line in HISTORY.open(errors="replace"):
            try:
                h = json.loads(line)
                ts = datetime.fromtimestamp(h["timestamp"] / 1000, timezone.utc)
                if not (lo <= iso(ts) < hi):
                    continue
                sid = h.get("sessionId")
                if (sid in cuts and iso(ts) >= cuts[sid]) or (h.get("display") or "").startswith("/retro"):
                    continue
                history.append({"ts": iso(ts), "project": h.get("project"), "sessionId": sid,
                                "display": (h.get("display") or "")[:PROMPT_MAX]})
            except (ValueError, KeyError, TypeError, OSError):
                drift += 1
    except OSError:
        pass
    mains_in = [d for d in sessions if "agentId" not in d]
    return {"window": {"start": lo, "end": hi}, "drift": drift, "sessions": sessions,
            "skill_listings": listings, "history": history,
            "n_sessions": len(mains_in), "n_projects": len({d.get("cwd") for d in mains_in})}


def _json_default(o):
    return dict(o) if isinstance(o, collections.Counter) else list(o)


def usage_line():
    try:
        out = subprocess.run(["claude", "-p", "/usage"], capture_output=True, text=True, timeout=60).stdout
        lines = [l.strip() for l in out.splitlines() if l.startswith("Current") and "%" in l]
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
    dg = build_digest(start)
    tmp = Path(tempfile.mkdtemp(prefix="retro-"))
    (tmp / "state.json").write_text(json.dumps({"redo": redo, "timestamp": start.isoformat()}))
    (tmp / "digest.json").write_text(json.dumps(dg, default=_json_default, separators=(",", ":")))
    (tmp / "draft.md").write_text(SKELETON.format(sessions=dg["n_sessions"], projects=dg["n_projects"]))
    print(f"format drift: {dg['drift']} records skipped")
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
