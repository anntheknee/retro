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
TAIL_MAX = 300  # tail of the previous reply kept on a flagged turn
CHURN_EDITS = 3  # edits to one file in one turn that count as churn
ERROR_LOOP = 3  # tool errors in one turn that count as an error-and-retry loop
LONG_TURNS = 30  # a Session with this many typed prompts counts as long
CACHE_WRITE_HEAVY = 50_000  # cache-write tokens in one turn
CLAUDE_MD_LINES = 200
LONG_PROMPT = 200  # chars: a typed prompt this long may be a pasted playbook
SIMILAR = 0.6  # word-trigram Jaccard at or above this counts as near-identical
RECUR_SESSIONS = 3  # Bash heads and tool sequences must recur across this many Sessions
SEQ_LEN = 3  # tools in a recurring sequence
DESC_MAX = 300  # chars of a Toolkit description kept for agent C
SEQ_MAX = 2000  # tool calls kept per Session for sequence counting
# Record types the digest knows about or deliberately drops; anything else counts as format drift.
KNOWN_TYPES = {
    "assistant", "attachment", "user", "api-request-blob", "mode", "atis-latch", "last-prompt",
    "api-request", "ai-title", "system", "file-history-snapshot", "bridge-session", "permission-mode",
    "queue-operation", "file-history-delta", "cost-state", "api-request-shape", "agent-color",
    "pr-link", "custom-title",
}

# Built-in slash commands users type; not on disk, so listed here. Bundled skills come from the skill listing.
BUILTIN_COMMANDS = ["clear", "compact", "context", "cost", "doctor", "help", "init", "insights", "model", "rewind",
                    "resume", "review", "usage", "config", "memory", "permissions", "plan", "btw", "rename"]

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


def digest_session(path, lo, hi, parent_cut=None, full=False):
    """Digest one transcript, keeping only records in [lo, hi). Returns (digest, own_cut, drift).

    A typed `/retro` cuts the Session from that prompt onward; a subagent is cut at its parent's cut.
    Returns digest None for a headless Session the Retro itself started.
    `full` keeps whole prompts, longer tails and error texts on every turn, for `context`.
    """
    d = {"file": str(path.relative_to(PROJECTS)), "versions": set(), "models": collections.Counter(),
         "effort": collections.Counter(), "tokens": collections.Counter(), "peak_ctx": 0,
         "tools": collections.Counter(), "bash_heads": collections.Counter(),
         "skills_invoked": collections.Counter(), "slash": collections.Counter(),
         "attrib_skill_out": collections.Counter(), "tool_errors": [], "denials": collections.Counter(),
         "interrupts": 0, "compactions": [], "api_errors": 0, "informational": [], "turns": [],
         "perm_modes": collections.Counter(), "denied": collections.Counter(),
         "prompted_by": collections.Counter(), "tokens_by_model": collections.defaultdict(collections.Counter),
         "tokens_by_effort": collections.defaultdict(collections.Counter), "cache_heavy": [],
         "ctx_sum": 0, "first_ctx": 0, "tool_seq": [], "agent_prompts": []}
    tool_by_uuid = {}
    listing = None
    reqs, cur, first, last, cut, drift, seen_user = {}, None, None, None, None, 0, False
    reply = ""  # tail of the latest assistant text
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
            elif t == "queue-operation":
                if r.get("reason") == "absorbed_mid_turn" and cur:
                    cur["steered"] = cur.get("steered", 0) + 1
                    cur.setdefault("steering", []).append((r.get("content") or "")[:PROMPT_MAX])
            elif t == "assistant":
                m = r.get("message") or {}
                txt = text_of(m.get("content") or []).strip()
                if txt:
                    reply = txt[-(10 * TAIL_MAX if full else TAIL_MAX):]
                reqs[r.get("requestId") or r.get("uuid")] = (m.get("model"), m.get("usage") or {}, r.get("attributionSkill"), str(r.get("effort")), cur)
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
                        if cur and n in ("Edit", "Write", "MultiEdit", "NotebookEdit") and inp.get("file_path"):
                            cur["edits"][inp["file_path"]] += 1
                        head = ""
                        if n == "Skill":
                            d["skills_invoked"][inp.get("skill")] += 1
                        if n == "Bash":
                            cmd = (inp.get("command") or "").strip().split()
                            if cmd:
                                head = " ".join(cmd[:2]) if cmd[0] in ("git", "gh", "npm", "uv", "claude", "openspec") else cmd[0]
                                d["bash_heads"][head] += 1
                        tool_by_uuid[r.get("uuid")] = tool_by_uuid[c.get("id")] = f"{n} {head}".strip()
                        if len(d["tool_seq"]) < SEQ_MAX:
                            d["tool_seq"].append(tool_by_uuid[c.get("id")])
                        if n in ("Agent", "Task") and inp.get("prompt"):
                            d["agent_prompts"].append(str(inp["prompt"])[:PROMPT_MAX])
            elif t == "user":
                c = (r.get("message") or {}).get("content")
                tids = [x.get("tool_use_id") for x in c if isinstance(x, dict)] if isinstance(c, list) else []
                src = next((tool_by_uuid[i] for i in tids if i in tool_by_uuid), tool_by_uuid.get(r.get("sourceToolAssistantUUID"), "?"))
                if r.get("toolDenialKind"):
                    d["denials"][r["toolDenialKind"]] += 1
                    d["denied"][f"{src} [{r['toolDenialKind']}]"] += 1
                pd = r.get("permissionDecision") or {}
                if pd.get("decision") == "reject" or (pd.get("source") or "").startswith("user"):
                    d["denials"]["pd:%s/%s" % (pd.get("decision"), pd.get("source"))] += 1
                    if pd.get("decision") == "reject" and not r.get("toolDenialKind"):
                        d["denied"][f"{src} [reject]"] += 1
                if (pd.get("source") or "").startswith("user") and pd.get("decision") == "accept":
                    d["prompted_by"][src] += 1
                if isinstance(c, list):
                    for x in c:
                        if isinstance(x, dict) and x.get("type") == "tool_result" and x.get("is_error"):
                            cc = x.get("content")
                            msg = cc if isinstance(cc, str) else json.dumps(cc)
                            d["tool_errors"].append(msg[:80])
                            if cur:
                                cur["errors"].append(msg[:500 if full else 80])
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
                cur = {"ts": ts, "len": len(s), "prompt": s if full else s[:PROMPT_MAX], "tools": collections.Counter(),
                       "edits": collections.Counter(), "errors": [], "prev_tail": reply}
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
    for i, (model, u, sk, effort, turn) in enumerate(reqs.values()):
        d["models"][model] += 1
        tok = {"in": u.get("input_tokens", 0), "cache_read": u.get("cache_read_input_tokens", 0),
               "cache_write": u.get("cache_creation_input_tokens", 0), "out": u.get("output_tokens", 0),
               "thinking": (u.get("output_tokens_details") or {}).get("thinking_tokens", 0)}
        d["tokens"].update(tok)
        d["tokens_by_model"][model].update(tok)
        d["tokens_by_effort"][effort].update(tok)
        ctx = tok["in"] + tok["cache_read"] + tok["cache_write"]
        d["peak_ctx"] = max(d["peak_ctx"], ctx)
        d["ctx_sum"] += ctx
        if i == 0:
            d["first_ctx"] = ctx
        if turn is not None:
            turn["_cw"] = turn.get("_cw", 0) + tok["cache_write"]
        if sk:
            d["attrib_skill_out"][sk] += tok["out"]
    for t in d["turns"]:
        edits, errors = t.pop("edits"), t.pop("errors")
        churn = {f: n for f, n in edits.items() if n >= CHURN_EDITS}
        flags = [k for k, on in (("interrupted", t.get("interrupted")), ("steered", t.get("steered")),
                                 ("edit_churn", churn), ("error_loop", len(errors) >= ERROR_LOOP)) if on]
        if flags:
            t["flags"] = flags
            if churn:
                t["churn"] = churn
            if errors:
                t["errors"] = errors[:5]
        if full:
            t["edits"], t["errors"] = edits, errors
        elif not flags:
            t.pop("prev_tail")
        if not t.get("prev_tail"):
            t.pop("prev_tail", None)
        cw = t.pop("_cw", 0)
        if cw >= CACHE_WRITE_HEAVY:
            d["cache_heavy"].append({"ts": t["ts"], "cache_write": cw, "prompt": t["prompt"][:80]})
    d["start"], d["end"], d["requests"] = first, last, len(reqs)
    d["versions"] = sorted(d["versions"])
    d["tool_errors"] = collections.Counter(d["tool_errors"]).most_common(10)
    d["bash_heads"] = dict(d["bash_heads"].most_common(15))
    d["listing"] = listing
    return (d if first else None), cut, drift


def instruction_files(dg):
    """CLAUDE.md files over the line limit, or changed or grown during the Window."""
    lo = dg["window"]["start"]
    lo_epoch = datetime.fromisoformat(lo.replace("Z", "+00:00")).timestamp()
    dirs = {Path(d["cwd"]) for d in dg["sessions"] if d.get("cwd") and "agentId" not in d}
    paths = {HOME / "CLAUDE.md"} | {p / n for p in dirs for n in ("CLAUDE.md", ".claude/CLAUDE.md")}
    out = []
    for f in sorted(paths):
        try:
            lines = len(f.read_text(errors="replace").splitlines())
            changed = f.stat().st_mtime >= lo_epoch
        except OSError:
            continue
        grew = None
        try:
            log = subprocess.run(["git", "-C", str(f.parent), "log", f"--since={lo}", "--numstat", "--format=", "--", f.name],
                                 capture_output=True, text=True, timeout=10).stdout
            grew = sum(int(a) - int(b) for a, b, _ in (l.split("\t") for l in log.splitlines() if l.count("\t") == 2) if a.isdigit() and b.isdigit())
        except (OSError, subprocess.SubprocessError):
            pass
        if lines > CLAUDE_MD_LINES or changed or (grew or 0) > 0:
            out.append({"file": str(f), "lines": lines, "over_limit": lines > CLAUDE_MD_LINES,
                        "changed_in_window": changed, "net_lines_added_in_window": grew})
    return out


def compute_metrics(dg):
    """Numbers and rubric candidates for categories 2, 5 and 7. Writes no Finding."""
    ss = dg["sessions"]
    mains = [d for d in ss if "agentId" not in d]
    top = lambda c, n=15: dict(collections.Counter(c).most_common(n))
    tok_total = lambda c: c.get("in", 0) + c.get("cache_write", 0) + c.get("out", 0)

    def row(d):
        return {"file": d["file"], "project": d.get("cwd"), "turns": len(d["turns"]), "peak_ctx": d["peak_ctx"],
                "mean_ctx": d["ctx_sum"] // d["requests"] if d["requests"] else 0,
                "compactions": d["compactions"], "clear": d["slash"].get("clear", 0), "compact": d["slash"].get("compact", 0)}

    rows = [row(d) for d in mains if d["requests"]]
    no_clear = [d["file"] for d in mains if d["interrupts"] >= 2 and not d["slash"].get("clear")]
    context = {
        "sessions": len(rows),
        "mean_peak_ctx": sum(r["peak_ctx"] for r in rows) // max(len(rows), 1),
        "top_peak": sorted(rows, key=lambda r: -r["peak_ctx"])[:15],
        "compactions_total": sum(len(r["compactions"]) for r in rows),
        "clear_total": sum(r["clear"] for r in rows), "compact_total": sum(r["compact"] for r in rows),
        "long_sessions": sorted([r for r in rows if r["turns"] >= LONG_TURNS], key=lambda r: -r["turns"])[:15],
        "instruction_files": instruction_files(dg),
        "rubric_candidates": [f"{len(no_clear)} Sessions had 2+ interrupts and no /clear: {no_clear[:10]}"] if no_clear else [],
    }
    by = lambda key: collections.defaultdict(collections.Counter)
    by_project, by_model, by_effort = by(0), by(0), by(0)
    usd_project, skill_out = collections.Counter(), collections.Counter()
    allt = collections.Counter()
    for d in ss:
        proj = d.get("cwd")
        by_project[proj].update(d["tokens"])
        usd_project[proj] += d.get("cost_usd", 0)
        allt.update(d["tokens"])
        skill_out.update(d["attrib_skill_out"])
        for m, c in d["tokens_by_model"].items():
            by_model[m].update(c)
        for e, c in d["tokens_by_effort"].items():
            by_effort[e].update(c)
    ctx_in = allt["in"] + allt["cache_read"] + allt["cache_write"]
    firsts = sorted(d["first_ctx"] for d in mains if d["requests"])
    cost = {
        "tokens": dict(allt), "usd_total": round(sum(usd_project.values()), 2),
        "cache_hit_ratio": round(allt["cache_read"] / ctx_in, 3) if ctx_in else None,
        "by_project": {p: {**dict(c), "usd": round(usd_project[p], 2)} for p, c in sorted(by_project.items(), key=lambda x: -tok_total(x[1]))[:10]},
        "by_model": {m: dict(c) for m, c in by_model.items()},
        "by_effort": {e: dict(c) for e, c in by_effort.items()},
        "output_tokens_by_skill": top(skill_out, 10),
        "top_sessions": [{"file": d["file"], "usd": d.get("cost_usd"), **dict(d["tokens"])}
                         for d in sorted(mains, key=lambda d: -tok_total(d["tokens"]))[:10]],
        "cache_heavy_turns": sorted([{"file": d["file"], **t} for d in ss for t in d["cache_heavy"]], key=lambda t: -t["cache_write"])[:10],
        "expensive_subagents": [{"file": d["file"], "agent": d.get("agent"), **dict(d["tokens"])}
                                for d in sorted([d for d in ss if "agentId" in d], key=lambda d: -tok_total(d["tokens"]))[:5]],
        "fixed_overhead_ctx": {"median": firsts[len(firsts) // 2] if firsts else 0,
                               "mean": sum(firsts) // max(len(firsts), 1), "sessions": len(firsts)},
    }
    denied, prompted, kinds = collections.Counter(), collections.Counter(), collections.Counter()
    for d in ss:
        denied.update(d["denied"])
        prompted.update(d["prompted_by"])
        kinds.update(d["denials"])
    permissions = {"prompts_answered": sum(prompted.values()), "prompted_by_tool": top(prompted),
                   "denied_by_tool_and_kind": top(denied), "denial_kinds": dict(kinds)}
    return {"context": context, "cost": cost, "permissions": permissions}


def context(session, turn, tmp=None):
    """Print one turn in full. `session` is a digest `file` path or a session id; `turn` indexes its turns.

    Pass the Retro temp folder so turns are counted inside the same Window as `agent_a.json`.
    """
    stem = Path(session).stem
    hits = glob.glob(str(PROJECTS / "**" / f"{stem}.jsonl"), recursive=True)
    if not hits:
        sys.exit(f"no transcript for session {session}")
    win = json.loads((Path(tmp) / "digest.json").read_text())["window"] if tmp else {"start": "", "end": "￿"}
    d, _, _ = digest_session(Path(hits[0]), win["start"], win["end"], full=True)
    try:
        t = d["turns"][int(turn)]
    except (TypeError, IndexError, ValueError):
        sys.exit(f"turn {turn} not found ({len(d['turns']) if d else 0} turns)")
    print(f"session {d['file']} turn {turn} at {t['ts']}\nflags: {', '.join(t.get('flags', [])) or 'none'}")
    print(f"\n## Typed prompt\n{t['prompt']}\n\n## End of Claude's previous reply\n{t.get('prev_tail') or '(none)'}")
    print(f"\n## Tools\n{dict(t['tools']) or '(none)'}\nedits per file: {dict(t['edits']) or '(none)'}")
    print("\n## Mid-turn steering\n" + ("\n".join(f"- {x}" for x in t.get("steering", [])) or "(none)"))
    print("\n## Tool errors\n" + ("\n".join(f"- {x}" for x in t["errors"]) or "(none)"))


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


def agent_a_input(dg):
    """Agent A's slice: every main Session's turns, indexed for `retro.py context`."""
    keep = ("i", "ts", "prompt", "len", "ms", "flags", "steering", "churn", "errors", "prev_tail")
    return {"sessions": [{"session": d["file"], "project": d.get("cwd"), "title": d.get("title"),
                          "interrupts": d["interrupts"], "slash": d["slash"],
                          "turns": [{k: t[k] for k in keep if k in t} for t in (dict(t, i=i) for i, t in enumerate(d["turns"]))]}
                         for d in dg["sessions"] if "agentId" not in d and d["turns"]]}


def norm(s):
    return " ".join(re.findall(r"\w+", s.lower()))


def shingles(s):
    w = norm(s).split()
    return {" ".join(w[i:i + 3]) for i in range(max(len(w) - 2, 1))}


def clusters(items):
    """Group (where, text) items whose word trigrams overlap >= SIMILAR; keep groups spanning 2+ places."""
    groups = []  # ponytail: greedy single pass, O(n*groups); a different order can split a group
    for where, text in items:
        sh = shingles(text)
        if not norm(text):
            continue
        for g in groups:
            if len(sh & g["sh"]) / len(sh | g["sh"]) >= SIMILAR:
                g["where"].append(where)
                break
        else:
            groups.append({"sh": sh, "text": text, "where": [where]})
    out = [{"text": g["text"][:PROMPT_MAX], "count": len(set(g["where"])), "where": sorted(set(g["where"]))[:10]}
           for g in groups if len(set(g["where"])) >= 2]
    return sorted(out, key=lambda g: -g["count"])[:15]


def agent_b_input(dg):
    """Agent B's slice: typed prompts plus whole-Window repeat candidates for categories 4 and 8."""
    mains = [d for d in dg["sessions"] if "agentId" not in d and d["turns"]]
    prompts = [(d["file"], t["prompt"]) for d in mains for t in d["turns"]]
    exact = collections.defaultdict(set)
    for f, p in prompts:
        if len(norm(p)) >= 15:
            exact[norm(p)].add(f)
    heads = collections.defaultdict(set)
    seqs = collections.defaultdict(set)
    for d in mains:
        for h in d["bash_heads"]:
            heads[h].add(d["file"])
        q = d["tool_seq"]
        for i in range(len(q) - SEQ_LEN + 1):
            if len(set(q[i:i + SEQ_LEN])) > 1:
                seqs[" > ".join(q[i:i + SEQ_LEN])].add(d["file"])
    recur = lambda m: sorted(((k, len(v)) for k, v in m.items() if len(v) >= RECUR_SESSIONS), key=lambda x: -x[1])[:20]
    return {
        "repeated_prompts": sorted(({"prompt": k[:PROMPT_MAX], "sessions": len(v), "where": sorted(v)[:10]}
                                    for k, v in exact.items() if len(v) >= 2), key=lambda x: -x["sessions"])[:20],
        "long_prompt_duplicates": clusters([(f, p) for f, p in prompts if len(p) >= LONG_PROMPT]),
        "similar_openings": clusters([(d["file"], d["turns"][0]["prompt"]) for d in mains if len(d["turns"][0]["prompt"]) >= 15]),
        "similar_agent_prompts": clusters([(d["file"], p) for d in dg["sessions"] for p in d["agent_prompts"]]),
        "bash_heads_in_3plus_sessions": recur(heads),
        "tool_sequences_in_3plus_sessions": recur(seqs),
        "sessions": [{"session": d["file"], "project": d.get("cwd"), "prompts": [t["prompt"] for t in d["turns"]]} for d in mains],
    }


def frontmatter(path):
    """Top-level `key: value` pairs of a SKILL.md or agent file; folded `>`/`|` values are joined."""
    try:
        head = re.match(r"\s*---\n(.*?)\n---", path.read_text(errors="replace"), re.S).group(1).splitlines()
    except (OSError, AttributeError):
        return {}
    out, key, folded = {}, None, False
    for line in head:
        m = re.match(r"^([\w-]+):\s*(.*)$", line)
        if m:
            key = m.group(1)
            folded = m.group(2).strip() in (">", "|", ">-", "|-")
            out[key] = "" if folded else m.group(2).strip().strip("\"'")
        elif folded and line.startswith((" ", "\t")):
            out[key] = (out[key] + " " + line.strip()).strip()
    return out


def load_json(path):
    try:
        return json.loads(Path(path).read_text())
    except (OSError, ValueError):
        return {}


def build_toolkit(dg):
    """One row per invocable item, plus the plugin list. Tolerates missing or changed layouts."""
    claude_json = load_json(HOME.parent / ".claude.json")
    lifetime = lambda n: (claude_json.get("skillUsage", {}).get(n) or {}).get("usageCount")
    lock = load_json(HOME.parent / ".agents" / ".skill-lock.json").get("skills", {})
    uses, tool_uses = collections.Counter(), collections.Counter()
    for d in dg["sessions"]:
        uses.update(d["skills_invoked"])
        uses.update(d["slash"])
        tool_uses.update(d["tools"])
        if d.get("agent", {}).get("agentType"):
            uses["agent:" + d["agent"]["agentType"]] += 1
    rows = {}

    def add(name, origin, auto, desc):
        rows.setdefault(name, {"name": name, "origin": origin, "auto": auto, "description": (desc or "")[:DESC_MAX],
                               "uses": uses.get(name, 0), "lifetime": lifetime(name)})

    def add_skill(f, name, origin):
        fm = frontmatter(f)
        add(name or fm.get("name") or f.parent.name, origin, fm.get("disable-model-invocation") != "true", fm.get("description"))

    for f in sorted((HOME / "skills").glob("*/SKILL.md")):
        d = f.parent
        if d.name == "synced":
            continue
        if d.is_symlink():
            src = (lock.get(d.resolve().name) or {}).get("source")
            add_skill(f, frontmatter(f).get("name") or d.name, f"skills CLI ({src or 'unlocked symlink'})")
        else:
            add_skill(f, frontmatter(f).get("name") or d.name, "hand copy")
    for m in (HOME / "skills" / "synced").glob("*/manifest.json"):
        for sk in load_json(m).get("skills", []):
            if sk.get("name"):
                add("anthropic-skills:" + sk["name"], f"claude.ai synced ({sk.get('source')})", True, sk.get("description"))
    for cwd in sorted({d["cwd"] for d in dg["sessions"] if d.get("cwd") and "agentId" not in d}):
        proj = Path(cwd) / ".claude"
        if proj == HOME:
            continue
        for f in sorted(proj.glob("skills/*/SKILL.md")):
            add_skill(f, None, f"project {Path(cwd).name}")
        for f in sorted(proj.glob("commands/**/*.md")):
            add(":".join(f.relative_to(proj / "commands").with_suffix("").parts), f"project {Path(cwd).name}", False, frontmatter(f).get("description"))
        for f in sorted(proj.glob("agents/*.md")):
            add("agent:" + (frontmatter(f).get("name") or f.stem), f"project {Path(cwd).name}", True, frontmatter(f).get("description"))
    for f in sorted((HOME / "commands").glob("**/*.md")):
        add(":".join(f.relative_to(HOME / "commands").with_suffix("").parts), "user command", False, frontmatter(f).get("description"))
    for f in sorted((HOME / "agents").glob("*.md")):
        add("agent:" + (frontmatter(f).get("name") or f.stem), "user agent", True, frontmatter(f).get("description"))
    plugins = []
    for pid, installs in (load_json(HOME / "plugins" / "installed_plugins.json").get("plugins") or {}).items():
        inst = installs[0] if isinstance(installs, list) and installs and isinstance(installs[0], dict) else {}
        pname, root = pid.split("@")[0], Path(inst.get("installPath", "/nonexistent"))
        names = []
        for f in sorted(root.glob("skills/*/SKILL.md")):
            n = f"{pname}:{frontmatter(f).get('name') or f.parent.name}"
            add_skill(f, n, f"plugin {pid}")
            names.append(n)
        for f in sorted(root.glob("commands/**/*.md")):
            n = f"{pname}:{f.stem}"
            add(n, f"plugin {pid}", False, frontmatter(f).get("description"))
            names.append(n)
        for f in sorted(root.glob("agents/*.md")):
            n = f"agent:{pname}:" + (frontmatter(f).get("name") or f.stem)
            add(n, f"plugin {pid}", True, frontmatter(f).get("description"))
            names.append(n)
        mcp = sum(c for t, c in tool_uses.items() if t.startswith(f"mcp__plugin_{pname}_"))
        used = sum(uses.get(n, 0) for n in names) + mcp
        has_hooks = (root / "hooks").exists()
        status = "used" if used else (("hooks only, can't tell" if not names else "unused, but ships hooks") if has_hooks else "unused")
        plugins.append({"plugin": pid, "version": inst.get("version"), "items": names, "uses": used, "status": status})
    for n in dg["skill_listings"]:
        add(n, "bundled or built-in (skill listing)", True, None)
    for n in BUILTIN_COMMANDS:
        add(n, "built-in command", False, None)
    return {"items": sorted(rows.values(), key=lambda r: r["name"]), "plugins": plugins}


def agent_c_input(dg):
    """Agent C's slice: the Toolkit table and the prompts to match against it. Never split."""
    prompts = [{"session": d["file"], "project": d.get("cwd"), "prompts": [t["prompt"] for t in d["turns"]]}
               for d in dg["sessions"] if "agentId" not in d and d["turns"]]
    return {**build_toolkit(dg), "sessions": prompts}


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
    (tmp / "agent_a.json").write_text(json.dumps(agent_a_input(dg), default=_json_default, separators=(",", ":")))
    (tmp / "agent_b.json").write_text(json.dumps(agent_b_input(dg), default=_json_default, separators=(",", ":")))
    (tmp / "agent_c.json").write_text(json.dumps(agent_c_input(dg), default=_json_default, separators=(",", ":")))
    (tmp / "draft.md").write_text(SKELETON.format(sessions=dg["n_sessions"], projects=dg["n_projects"]))
    (tmp / "metrics.json").write_text(json.dumps(compute_metrics(dg), default=_json_default, separators=(",", ":")))
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
    body = draft.read_text()
    n = len(re.findall(r"^### \d+\.", body, re.M))
    body = re.sub(r"Findings: \d+", f"Findings: {n}", body, count=1)
    new.write_text(f"---\nretro_timestamp: {state['timestamp']}\n---\n\n{body}")
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
    elif cmd == "context" and len(args) in (2, 3):
        context(*args)
    elif cmd == "commit" and args:
        commit(args[0])
    else:
        sys.exit("usage: retro.py prepare [--redo] | context <session> <turn> [<temp folder>] | commit <draft.md> | status")
