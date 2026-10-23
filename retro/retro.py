#!/usr/bin/env python3
"""Helper for the /retro skill. Claude runs these subcommands; the user never does."""
import collections, email.utils, urllib.parse, urllib.request, xml.etree.ElementTree as ET, glob, html, hashlib, json, math, os, re, shutil, subprocess, sys, tempfile, time
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
PATCH_MAX = 1500  # chars of one upstream file diff kept for the port-this judgment
PATCH_FILES = 8  # changed files per tracked source that carry a diff
SPLIT_TOKENS = 100_000  # an agent input over this (bytes / 4) is split into whole-Session pieces
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
                    "resume", "review", "usage", "config", "memory", "permissions", "plan", "btw", "rename",
                    "status", "mcp", "agents", "hooks", "login", "logout", "export", "vim", "add-dir", "terminal-setup",
                    "bug", "output-style", "statusline", "ide", "pr-comments", "release-notes", "theme", "fast", "color",
                    "effort", "new", "plugin", "reload-plugins", "skills", "rc", "diff", "skill-doctor", "opusplan"]

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
    """The Retro Timestamp in a findings file. Raises ValueError when it is missing or malformed."""
    try:
        m = re.search(r"^retro_timestamp: (\S+)$", path.read_text().split("---")[1], re.M)
        return datetime.fromisoformat(m.group(1))
    except (IndexError, AttributeError) as e:
        raise ValueError("no retro_timestamp") from e


def last_retro_start():
    """Start of the gate period: the Retro Timestamp, else the oldest history entry."""
    try:
        return findings_timestamp(FINDINGS)
    except (OSError, ValueError):
        pass  # no findings file, or a corrupt one: fall back to history
    try:
        with HISTORY.open() as f:
            first = json.loads(f.readline())
        return datetime.fromtimestamp(first["timestamp"] / 1000, timezone.utc)
    except (OSError, ValueError, KeyError):
        return None


def status():
    try:
        days = (now() - findings_timestamp(FINDINGS)).days
    except (OSError, ValueError):  # none yet, or unreadable
        print("retro due")
        return
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


def is_main(d):
    """A digest of a main Session, not a subagent's."""
    return "agentId" not in d


def iso(dt):
    return dt.strftime("%Y-%m-%dT%H:%M:%S.000Z")


def command_words(cmd):
    """First word of each command in a Bash string: past `cd x &&`, pipes, `;` and `FOO=1` prefixes."""
    words = []
    for seg in re.split(r"&&|\|\||[;|\n]", cmd):
        toks = [t for t in seg.split() if not re.fullmatch(r"\w+=\S*", t)]
        if toks:
            words.append(toks[0])
    return words


def text_of(c):
    if isinstance(c, str):
        return c
    return " ".join(x.get("text", "") for x in c if isinstance(x, dict) and x.get("type") == "text")


def tally_requests(d, reqs):
    """Fold each deduped request's tokens into the Session totals, per model and effort, and into its turn's cache writes."""
    for i, q in enumerate(reqs.values()):
        u, model, effort, turn = q["usage"], q["model"], q["effort"], q["turn"]
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
        if q["skill"]:
            d["attrib_skill_out"][q["skill"]] += tok["out"]


def flag_turns(d, full):
    """Flag interrupted, steered, churning and error-looping turns; drop the detail from the rest unless `full`."""
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


def digest_session(path, lo, hi, parent_cut=None, full=False):
    """Digest one transcript, keeping only records in [lo, hi). Returns (digest, own_cut, drift).

    A typed `/retro` cuts the Session from that prompt onward; a subagent is cut at its parent's cut.
    Returns digest None for a headless Session the Retro itself started.
    `full` keeps whole prompts, longer tails and error texts on every turn, for `context`.
    """
    d = {"file": str(path.relative_to(PROJECTS)), "versions": set(), "models": collections.Counter(),
         "effort": collections.Counter(), "tokens": collections.Counter(), "peak_ctx": 0,
         "tools": collections.Counter(), "bash_heads": collections.Counter(), "bash_words": set(),
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
                reqs[r.get("requestId") or r.get("uuid")] = {"model": m.get("model"), "usage": m.get("usage") or {}, "skill": r.get("attributionSkill"),
                                                             "effort": str(r.get("effort")), "turn": cur}
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
                                d["bash_words"].update(command_words(" ".join(cmd)))
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
    tally_requests(d, reqs)
    flag_turns(d, full)
    d["start"], d["end"], d["requests"] = first, last, len(reqs)
    d["versions"] = sorted(d["versions"])
    d["tool_errors"] = collections.Counter(d["tool_errors"]).most_common(10)
    d["bash_heads"] = dict(d["bash_heads"].most_common(15))
    d["bash_words"] = sorted(d["bash_words"])
    d["listing"] = listing
    return (d if first else None), cut, drift


def instruction_files(dg):
    """CLAUDE.md files over the line limit, or changed or grown during the Window."""
    lo = dg["window"]["start"]
    lo_epoch = datetime.fromisoformat(lo.replace("Z", "+00:00")).timestamp()
    dirs = {Path(d["cwd"]) for d in dg["sessions"] if d.get("cwd") and is_main(d)}
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
    mains = [d for d in ss if is_main(d)]
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
    by_project, by_model, by_effort = (collections.defaultdict(collections.Counter) for _ in range(3))
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
                                for d in sorted([d for d in ss if not is_main(d)], key=lambda d: -tok_total(d["tokens"]))[:5]],
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
    mains_in = [d for d in sessions if is_main(d)]
    return {"window": {"start": lo, "end": hi}, "drift": drift, "sessions": sessions,
            "skill_listings": listings, "history": history,
            "n_sessions": len(mains_in), "n_projects": len({d.get("cwd") for d in mains_in})}


def agent_a_input(dg):
    """Agent A's slice: every main Session's turns, indexed for `retro.py context`."""
    keep = ("ts", "prompt", "len", "ms", "flags", "steering", "churn", "errors", "prev_tail")
    return {"sessions": [{"session": d["file"], "project": d.get("cwd"), "title": d.get("title"),
                          "interrupts": d["interrupts"], "slash": d["slash"],
                          "turns": [{"i": i, **{k: t[k] for k in keep if k in t}} for i, t in enumerate(d["turns"])]}
                         for d in dg["sessions"] if is_main(d) and d["turns"]]}


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
    mains = [d for d in dg["sessions"] if is_main(d) and d["turns"]]
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


def skill_lock():
    """The skills CLI lock file's entries by lock key."""
    return load_json(HOME.parent / ".agents" / ".skill-lock.json").get("skills", {})


def installed_plugins():
    """(plugin id, its first install record) for each installed plugin."""
    for pid, installs in (load_json(HOME / "plugins" / "installed_plugins.json").get("plugins") or {}).items():
        yield pid, installs[0] if isinstance(installs, list) and installs and isinstance(installs[0], dict) else {}


def build_toolkit(dg):
    """One row per invocable item, plus the plugin list. Tolerates missing or changed layouts."""
    claude_json = load_json(HOME.parent / ".claude.json")
    lifetime = lambda n: (claude_json.get("skillUsage", {}).get(n) or {}).get("usageCount")
    lock = skill_lock()
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
    cwds = {d["cwd"] for d in dg["sessions"] if d.get("cwd") and is_main(d)}
    for cwd in sorted(cwds | {h["project"] for h in dg["history"] if h.get("project")}):
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
    for pid, inst in installed_plugins():
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


def dead_slash(dg, items):
    """Slash names typed in the Window that match no Toolkit item (a plugin item matches by its bare name too)."""
    known = {r["name"] for r in items}
    known |= {n.split(":", 1)[1] for n in known if ":" in n and not n.startswith("agent:")}
    typed = collections.Counter()
    for h in dg["history"]:
        m = re.match(r"/([\w:.-]*\w)(?=\s|$)", h["display"])  # not a path or "/foo."
        if m:
            typed[m.group(1)] += 1
    for d in dg["sessions"]:
        if is_main(d):
            for n in d["slash"]:
                typed.setdefault(n, 1)
    return {n: c for n, c in sorted(typed.items()) if n not in known}


def agent_c_input(dg):
    """Agent C's slice: the Toolkit table and the prompts to match against it. Never split."""
    prompts = [{"session": d["file"], "project": d.get("cwd"), "prompts": [t["prompt"] for t in d["turns"]]}
               for d in dg["sessions"] if is_main(d) and d["turns"]]
    tk = build_toolkit(dg)
    return {**tk, "dead_slash": dead_slash(dg, tk["items"]), "sessions": prompts}


AGENT_INPUTS = {"a": agent_a_input, "b": agent_b_input, "c": agent_c_input}
AGENT_CATEGORIES = {"a": {"prompting", "rework"}, "b": {"repeats", "workflows"}, "c": {"skills", "overlap"}}


def previous_findings(redo):
    """The baseline Findings by owner (agent a/b/c, else main), plus its Toolkit updates and Meta text.
    Baseline: the current findings file, or the previous-findings file on a Redo. None: no previous Retro."""
    path = PREV if redo else FINDINGS
    if not path.exists():
        return None
    body = re.sub(r"\A---\n.*?\n---\n", "", path.read_text(), flags=re.S)
    sections = {m.group(1): m.group(2) for m in re.finditer(r"^## (.+?)\n(.*?)(?=^## |\Z)", body, re.M | re.S)}
    out = {o: [] for o in ("a", "b", "c", "main")}
    for m in re.finditer(r"^(### \d+\. ([^\n·]+?)(?: ·[^\n]*)?)\n(.*?)(?=^### |\Z)", sections.get("Findings", ""), re.M | re.S):
        owner = next((a for a, cats in AGENT_CATEGORIES.items() if m.group(2).strip().lower() in cats), "main")
        out[owner].append(m.group(1) + "\n" + m.group(3).strip())
    out["toolkit_updates"] = sections.get("Toolkit updates", "").strip()
    out["meta"] = sections.get("Meta", "").strip()
    return out


def cursor(redo, start):
    """Start of the changelog scope: the previous Retro's Timestamp (a Redo: the one in the previous file), else 30 days back."""
    path = PREV if redo else FINDINGS
    try:
        return iso(findings_timestamp(path))
    except (OSError, ValueError):
        return iso(start - timedelta(days=GATE_DAYS))


def run_json(cmd):
    out = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    if out.returncode:
        raise RuntimeError((out.stderr or "failed").strip()[:200])
    return json.loads(out.stdout)


def gh(path):
    return run_json(["gh", "api", path])


def gh_raw(path):
    """A GitHub contents file as JSON."""
    return run_json(["gh", "api", path, "-H", "Accept: application/vnd.github.raw"])


def vkey(v):
    return tuple(int(x) if x.isdigit() else 0 for x in re.split(r"[.+-]", v.lstrip("v")))


def cli_package(word):
    """The brew formula or npm-global package a Bash command word resolves to, else None."""
    exe = shutil.which(word)
    if not exe:
        return None
    real = Path(exe).resolve().parts
    for marker in ("Cellar", "node_modules"):
        if marker in real:
            i = len(real) - 1 - real[::-1].index(marker)  # the innermost marker
            if i + 1 < len(real):
                name = real[i + 1]
                return name + "/" + real[i + 2] if name.startswith("@") and i + 2 < len(real) else name
    return None


def run_outdated(cmd):
    """`npm outdated` exits 1 when something is outdated, so only unparseable output is a failure."""
    out = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    try:
        return json.loads(out.stdout or "{}")
    except ValueError:
        raise RuntimeError((out.stderr or "no JSON").strip()[:200])


def build_clis(dg):
    """Installed CLIs, which the Window used, and which are outdated. Raises if the installed list can't be built."""
    installed = {n.rsplit("/", 1)[-1]: "brew" for n in subprocess.run(
        ["brew", "leaves", "--installed-on-request"], capture_output=True, text=True, timeout=60, check=True).stdout.split()}
    npm = json.loads(subprocess.run(["npm", "ls", "-g", "--depth=0", "--json"], capture_output=True, text=True, timeout=60).stdout or "{}")
    installed.update({n: "npm" for n in npm.get("dependencies", {})})
    installed["claude"] = "claude"
    used = {cli_package(w) or ("claude" if w == "claude" else None) for d in dg["sessions"] for w in d.get("bash_words", [])}
    used = sorted(n for n in used if n in installed)
    outdated = {}
    for n in (o for o in run_outdated(["brew", "outdated", "--json=v2"]).get("formulae", []) if o["name"] in installed):
        outdated[n["name"]] = {"installed": n["installed_versions"][-1], "latest": n["current_version"], "update": "brew upgrade " + n["name"]}
    for n, o in run_outdated(["npm", "outdated", "-g", "--json"]).items():
        if n in installed:
            o = o[-1] if isinstance(o, list) else o  # one entry per location
            outdated[n] = {"installed": o.get("current", "?"), "latest": o.get("latest", "?"), "update": "npm install -g " + n}
    return {"installed": sorted(installed), "used": used,
            "outdated_used": [{"name": n, **v} for n, v in sorted(outdated.items()) if n in used],
            "unused_outdated": [f"{n} {v['installed']} → {v['latest']} · not used this Window" for n, v in sorted(outdated.items()) if n not in used]}


def tree_sha(d):
    """Git tree SHA of a folder, as in the skills lock file's skillFolderHash; None for an empty folder."""
    ents = []
    for p in Path(d).iterdir():
        if p.name == ".DS_Store":
            continue
        if p.is_symlink():
            data, mode = os.readlink(p).encode(), "120000"
        elif p.is_dir():
            sha = tree_sha(p)
            if sha:
                ents.append((p.name + "/", "40000", p.name, sha))
            continue
        else:
            data, mode = p.read_bytes(), "100755" if os.access(p, os.X_OK) else "100644"
        ents.append((p.name, mode, p.name, hashlib.sha1(b"blob %d\0" % len(data) + data).hexdigest()))
    if not ents:
        return None
    body = b"".join(m.encode() + b" " + n.encode() + b"\0" + bytes.fromhex(sha) for _, m, n, sha in sorted(ents, key=lambda e: e[0].encode()))
    return hashlib.sha1(b"tree %d\0" % len(body) + body).hexdigest()


def upstream_entries(skill_md):
    """The `metadata.upstream` entries ({repo, path, base}) of a SKILL.md, in flow or block YAML."""
    try:
        head = re.match(r"\s*---\n(.*?)\n---", skill_md.read_text(errors="replace"), re.S).group(1)
    except (OSError, AttributeError):
        return []
    entries = []
    for k, v in re.findall(r"\b(repo|path|base)\s*:\s*[\"']?([^\s,\"'}\]]+)", head[head.find("upstream:"):] if "upstream:" in head else ""):
        if k == "repo":
            entries.append({})
        if entries:
            entries[-1][k] = v
    return [e for e in entries if len(e) == 3]


def build_owned(names, uses, attempt, out, first):
    """Owned Skills' upstream changes, edited installs to own, and (in the first Retro only) skills with no provenance. Fills out["owned"]."""
    owned = out["owned"] = {"tracked": [], "edited_installs": [], "no_provenance": []}
    for f in sorted((HOME / "skills").glob("*/SKILL.md")):
        if f.parent.is_symlink():
            continue
        name = frontmatter(f).get("name") or f.parent.name
        entries = upstream_entries(f)
        if not entries and first:
            owned["no_provenance"].append(name)
        for e in entries:
            def check(name=name, e=e):
                path = e["path"].rstrip("/")
                try:
                    gh(f"repos/{e['repo']}/contents/{path}")
                except RuntimeError as err:
                    if "404" not in str(err):
                        raise
                    owned["tracked"].append({"skill": name, **e, "state": "removed upstream"})
                    return
                cmp = gh(f"repos/{e['repo']}/compare/{e['base']}...HEAD")
                files = [x for x in cmp["files"] if x["filename"] == path or x["filename"].startswith(path + "/")]
                if files:
                    owned["tracked"].append({"skill": name, **e, "state": "changed", "uses": uses.get(name, 0),
                                             "commits": [c["commit"]["message"].split("\n")[0] for c in cmp["commits"]][-20:],
                                             "files": [{"file": x["filename"], "status": x["status"], "patch": (x.get("patch") or "")[:PATCH_MAX] if i < PATCH_FILES else ""}
                                                       for i, x in enumerate(files)]})
            attempt(f"owned {name}", check)
    lock = skill_lock()
    for key, sk in lock.items():
        d = HOME.parent / ".agents" / "skills" / key
        if sk.get("sourceType") != "github" or "/" not in (sk.get("skillPath") or "") or not d.is_dir():
            continue
        def check(key=key, sk=sk, d=d):
            if tree_sha(d) == sk["skillFolderHash"]:
                return
            base = gh(f"repos/{sk['source']}/commits?until={sk['installedAt']}&per_page=1")[0]["sha"]
            owned["edited_installs"].append({"skill": names.get(key, key), "lock_key": key, "repo": sk["source"],
                                             "path": sk["skillPath"].rsplit("/", 1)[0], "base": base, "uses": uses.get(names.get(key, key), 0)})
        attempt(f"edited install {key}", check)


def skills_behind(out, attempt, names, uses, since):
    """Lock-file skills whose upstream folder changed or vanished, with their repos' commit headlines."""
    repos = collections.defaultdict(dict)
    for key, sk in skill_lock().items():
        if sk.get("sourceType") == "github" and "/" in (sk.get("skillPath") or ""):  # a repo-root skill has no tree entry
            repos[sk["source"]][key] = sk
    for repo, group in repos.items():
        def check(repo=repo, group=group):
            full = gh(f"repos/{repo}/git/trees/HEAD?recursive=1")
            if full.get("truncated"):
                raise RuntimeError("tree too large, skipped")
            tree = {t["path"]: t["sha"] for t in full["tree"] if t["type"] == "tree"}
            commits = None
            for key, sk in group.items():
                d = sk["skillPath"].rsplit("/", 1)[0]
                state = "removed upstream" if d not in tree else ("behind" if tree[d] != sk["skillFolderHash"] else None)
                if state:
                    if commits is None:
                        commits = [c["commit"]["message"].split("\n")[0] for c in gh(f"repos/{repo}/commits?since={since}&per_page=100")]
                    out["skills"].append({"name": names.get(key, key), "lock_key": key, "repo": repo, "path": d, "state": state,
                                          "uses": uses.get(names.get(key, key), 0), "update": "npx skills update " + key})
            if commits is not None:
                out["commits"][repo] = commits
        attempt(f"skills {repo}", check)


def synced_updated(out, uses, since):
    for m in (HOME / "skills" / "synced").glob("*/manifest.json"):
        for sk in load_json(m).get("skills", []):
            n = "anthropic-skills:" + sk.get("name", "?")
            if isinstance(sk.get("updatedAt"), str) and sk["updatedAt"] > since:
                out["synced"].append({"name": n, "updated": sk["updatedAt"], "uses": uses.get(n, 0)})


def plugins_behind(out, attempt, tk, since):
    """Installed plugins behind their marketplace repo, with the releases since the cursor."""
    markets = load_json(HOME / "plugins" / "known_marketplaces.json")
    for pid, inst in installed_plugins():
        pname, _, market = pid.partition("@")
        repo = ((markets.get(market) or {}).get("source") or {}).get("repo") if isinstance(markets.get(market), dict) else None
        if not isinstance(repo, str):
            continue

        def check(pid=pid, pname=pname, repo=repo, inst=inst):
            row = {"plugin": pid, "installed": inst.get("version") or (inst.get("gitCommitSha") or "")[:12],
                   "uses": next((p["uses"] for p in tk["plugins"] if p["plugin"] == pid), 0), "update": f"claude plugin update {pid}"}
            latest = None
            try:  # a pinned version wins; else compare commits
                mk = gh_raw(f"repos/{repo}/contents/.claude-plugin/marketplace.json")
                latest = next((p.get("version") for p in mk.get("plugins", []) if p.get("name") == pname), None)
            except (ValueError, RuntimeError):
                pass
            if not latest:
                try:
                    latest = gh_raw(f"repos/{repo}/contents/.claude-plugin/plugin.json").get("version")
                except (ValueError, RuntimeError):
                    pass
            if latest and inst.get("version"):
                behind = vkey(latest) > vkey(inst["version"])
            else:
                latest = gh(f"repos/{repo}/commits/HEAD")["sha"][:12]
                behind = bool(inst.get("gitCommitSha")) and not latest.startswith(inst["gitCommitSha"][:12])
            if behind:
                row["latest"] = latest
                row["releases_since_cursor"] = [{"tag": r["tag_name"], "published": r["published_at"], "notes": (r.get("body") or "")[:500]}
                                                for r in gh(f"repos/{repo}/releases?per_page=30") if (r.get("published_at") or "") > since]
                out["plugins"].append(row)
        attempt(f"plugin {pid}", check)


def claude_code_behind(out, since):
    installed = subprocess.run(["claude", "--version"], capture_output=True, text=True, timeout=30).stdout.split()[0]
    times = run_json(["npm", "view", "@anthropic-ai/claude-code", "time", "--json"])
    vs = {v: t for v, t in times.items() if re.fullmatch(r"\d+\.\d+\.\d+", v)}
    latest = max(vs, key=vkey)
    if vkey(latest) > vkey(installed):
        out["claude_code"] = {"installed": installed, "latest": latest, "update": "claude update",
                              "releases_since_cursor": sorted((v for v, t in vs.items() if t > since), key=vkey)[-60:],
                              "upstream_of": "built-in commands, bundled skills and agents"}


def build_upstream(dg, since, first=False, tk=None):
    """What is behind upstream, as plain data for the main session. Each part tolerates a failed call."""
    tk = tk or build_toolkit(dg)
    uses = {r["name"]: r["uses"] for r in tk["items"]}
    out = {"since": since, "skills": [], "synced": [], "plugins": [], "commits": {}, "claude_code": None, "clis": None, "owned": None, "errors": []}

    def attempt(what, fn):
        try:
            return fn()
        except Exception as e:  # missing gh, no network, changed layout
            out["errors"].append(f"{what}: {e}")

    names = {}  # lock key -> the name the Toolkit table uses
    for f in (HOME / "skills").glob("*/SKILL.md"):
        if f.parent.is_symlink():
            names[f.parent.resolve().name] = frontmatter(f).get("name") or f.parent.name
    skills_behind(out, attempt, names, uses, since)
    attempt("synced skills", lambda: synced_updated(out, uses, since))
    plugins_behind(out, attempt, tk, since)
    attempt("claude code", lambda: claude_code_behind(out, since))
    out["clis"] = attempt("clis", lambda: build_clis(dg))
    build_owned(names, uses, attempt, out, first)
    return out


def _json_default(o):
    return dict(o) if isinstance(o, collections.Counter) else list(o)


def dumps(o):
    return json.dumps(o, default=_json_default, separators=(",", ":"))


def usage_line():
    try:
        out = subprocess.run(["claude", "-p", "/usage"], capture_output=True, text=True, timeout=60).stdout
        lines = [l.strip() for l in out.splitlines() if l.startswith("Current") and "%" in l]
        return "Plan usage: " + " | ".join(lines) if lines else "Plan usage: unavailable"
    except Exception:
        return "Plan usage: unavailable"


INSIGHTS_SECTIONS = ["section-friction", "section-features", "section-patterns", "section-horizon"]


def start_insights(tmp):
    # detached so it outlives prepare; `insights` waits for the done file
    subprocess.Popen(["sh", "-c", 'claude -p "/insights" --output-format json > insights_run.json 2> insights_err.txt; echo $? > insights_done.tmp; mv insights_done.tmp insights_done'],
                     cwd=tmp, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)


def insights(tmp):
    """Wait for the background /insights run, then write insights.json: date range and the four sections as text, or an error."""
    tmp = Path(tmp)
    out = tmp / "insights.json"
    try:
        for _ in range(300):
            if (tmp / "insights_done").exists():
                break
            time.sleep(1)
        else:
            raise RuntimeError("timed out")
        if (tmp / "insights_done").read_text().strip() != "0":
            raise RuntimeError("claude exited with " + (tmp / "insights_done").read_text().strip() + ": " + (tmp / "insights_err.txt").read_text()[:200])
        res = json.loads((tmp / "insights_run.json").read_text())
        if res.get("is_error"):
            raise RuntimeError(str(res.get("result"))[:200])
        m = re.search(r"[^\s\"'`()]*report[^\s\"'`()]*\.html", str(res.get("result")))
        report = Path(m.group(0).replace("file://", "")).expanduser() if m else None
        if not (report and report.is_file()):  # the result didn't name it: take the newest report written since the run began
            started = (tmp / "insights_run.json").stat().st_birthtime
            fresh = [f for f in (HOME / "usage-data").glob("report*.html") if f.stat().st_mtime >= started]
            report = max(fresh, key=lambda f: f.stat().st_mtime) if fresh else None
        if report is None:
            raise RuntimeError("no new report found")
        page = report.read_text()
        r = re.search(r'class="subtitle">[^<]*?(\d{4}-\d\d-\d\d) to (\d{4}-\d\d-\d\d)', page)
        sections = {}
        for sid in INSIGHTS_SECTIONS:
            i = page.find(f'id="{sid}"')
            if i < 0:
                continue
            j = page.find("<h2", i + 10)
            body = re.sub(r"<(script|style|button)\b.*?</\1>", "", page[page.find('>', i) + 1:j if j > 0 else len(page)], flags=re.S)
            sections[sid] = re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", body))).strip()
        if not sections:
            raise RuntimeError("report has none of the four sections")
        data = {"report": str(report), "date_range": [r.group(1), r.group(2)] if r else None, "sections": sections}
    except Exception as e:
        data = {"error": str(e)}
    out.write_text(json.dumps(data, separators=(",", ":")))
    print(out)


FEEDS = [  # (name, url, official)
    ("changelog", "https://code.claude.com/docs/en/changelog/rss.xml", True),
    ("whats-new", "https://code.claude.com/docs/en/whats-new/rss.xml", True),
    ("claude.dev", "https://claude.dev/rss.xml", True),
    ("simonw", "https://simonwillison.net/tags/claude-code.atom", False),
]
HTML_SOURCES = [  # for the web agent: WebFetch with a narrow prompt
    ("claude.com/blog", "https://www.claude.com/blog", "list posts dated after {since}"),
    ("github trending", "https://github.com/trending?since=monthly", "list repos about AI coding agents, Claude Code, skills, plugins or MCP"),
]
PLATFORM_TERMS = ["claude code", "skill", "plugin", "hook", "subagent", "mcp", "marketplace"]
CATEGORY_TERMS = {
    "prompting": ["prompt", "plan mode", "claude.md", "agents.md", "instructions"],
    "context": ["context", "compaction", "/clear", "memory", "1m", "rewind", "fork"],
    "skills": ["skill", "trigger", "description", "/skill-doctor"],
    "repeats": ["memory", "claude.md", "docs", "llms.txt"],
    "cost": ["usage", "token", "cost", "effort", "/usage", "fast mode", "model"],
    "rework": ["review", "verify", "test", "/code-review", "goal"],
    "permissions": ["permission", "auto mode", "allow", "deny", "sandbox"],
    "workflows": ["workflow", "routine", "loop", "hook", "automation", "mod"],
    "overlap": ["duplicate", "merge", "plugin list", "marketplace"],
}
NEWS_KEEP = 40  # non-official items kept after scoring
NEWS_MIN = 3  # score a non-official item needs
BODY_MAX = 600


def http_get(url):
    req = urllib.request.Request(url, headers={"User-Agent": "retro-skill"})
    return urllib.request.urlopen(req, timeout=30).read().decode("utf-8", "replace")


def parse_date(text):
    text = (text or "").strip()
    try:
        d = email.utils.parsedate_to_datetime(text)
    except (TypeError, ValueError):
        d = datetime.fromisoformat(text.replace("Z", "+00:00"))
    return d if d.tzinfo else d.replace(tzinfo=timezone.utc)


def parse_feed(xml):
    """RSS 2.0 or Atom -> [{title, url, date, body}]."""
    root = ET.fromstring(xml)
    out = []
    for e in root.iter():
        tag = e.tag.rsplit("}", 1)[-1]
        if tag not in ("item", "entry"):
            continue
        f = {}
        for c in e:
            t = c.tag.rsplit("}", 1)[-1]
            if t == "link" and c.get("rel") in ("self", "enclosure"):
                continue
            f.setdefault(t, c.get("href") or (c.text or ""))
            if t in ("encoded", "content"):
                f["body"] = c.text or ""
        body = f.get("body") or f.get("description") or f.get("summary") or ""
        out.append({"title": f.get("title", "").strip(), "url": f.get("link", ""), "body": re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", body))).strip(),
                    "date": f.get("pubDate") or f.get("published") or f.get("updated")})
    return out


MONTHS = "Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec".split()


def week_start(title):
    """'Week 37 (Sep 7-11, 2026)' -> that week's first day; the feed's pubDate is re-stamped, so it can't be trusted.
    The year is the end date's, so 'Dec 29 - Jan 2, 2027' starts in 2026."""
    days = re.findall("(%s)[a-z]* (\\d{1,2})\\b" % "|".join(MONTHS), title)
    year = re.search(r"\b(\d{4})\b", title)
    if not (days and year):
        return None
    y = int(year.group(1)) - (MONTHS.index(days[-1][0]) < MONTHS.index(days[0][0]))
    return datetime.strptime(f"{days[0][0]} {days[0][1]} {y}", "%b %d %Y").replace(tzinfo=timezone.utc)


def fetch_news(since):
    """Raw items from the script-readable shortlist, newer than `since`. Failures go in `errors`."""
    cut = parse_date(since)
    items, errors = [], []

    def attempt(what, fn):
        try:
            items.extend(fn())
        except Exception as e:
            errors.append(f"{what}: {e}")

    def releases():
        return [{"source": "claude-code releases", "official": True, "title": r["tag_name"], "url": r["html_url"], "date": r["published_at"],
                 "body": (r.get("body") or "")[:BODY_MAX]} for r in gh("repos/anthropics/claude-code/releases?per_page=100") if (r.get("published_at") or "") > since]

    def feed(name, url, official):
        out = []
        for i in parse_feed(http_get(url)):
            try:  # one undated item must not cost the feed
                d = (week_start(i["title"]) if name == "whats-new" else None) or parse_date(i["date"])
            except ValueError:
                continue
            if d > cut:
                out.append({"source": name, "official": official, "title": i["title"], "url": i["url"], "date": d.isoformat(), "body": i["body"][:BODY_MAX]})
        return out

    def hn():
        q = "https://hn.algolia.com/api/v1/search_by_date?" + urllib.parse.urlencode({
            "query": "claude code", "tags": "story", "restrictSearchableAttributes": "title",
            "numericFilters": f"created_at_i>{int(cut.timestamp())},points>50", "hitsPerPage": 50})
        return [{"source": "hacker news", "official": False, "title": h["title"], "url": h.get("url") or f"https://news.ycombinator.com/item?id={h['objectID']}",
                 "date": h["created_at"], "body": "", "points": h.get("points", 0)} for h in json.loads(http_get(q))["hits"] if h.get("title")]

    def awesome():
        cs = gh(f"repos/hesreallyhim/awesome-claude-code/commits?since={since}&per_page=100")
        return [{"source": "awesome-claude-code", "official": False, "title": c["commit"]["message"].splitlines()[0], "url": c["html_url"],
                 "date": c["commit"]["committer"]["date"], "body": ""} for c in cs if c["commit"]["message"].startswith("Add resource:")]

    def marketplace():
        repo = "repos/anthropics/claude-plugins-official"
        old = gh(f"{repo}/commits?until={since}&per_page=1")[0]["sha"]
        read = lambda ref: {p["name"]: p for p in gh_raw(f"{repo}/contents/.claude-plugin/marketplace.json?ref={ref}")["plugins"]}
        before, after = read(old), read("main")
        return [{"source": "official marketplace", "official": True, "title": "New official plugin: " + n, "url": "https://github.com/anthropics/claude-plugins-official",
                 "date": iso(now()), "body": (after[n].get("description") or "")[:BODY_MAX]} for n in sorted(set(after) - set(before))]

    attempt("claude-code releases", releases)
    for name, url, official in FEEDS:
        attempt(name, lambda: feed(name, url, official))
    attempt("hacker news", hn)
    attempt("awesome-claude-code", awesome)
    attempt("official marketplace", marketplace)
    return {"items": items, "errors": errors, "html_sources": [{"name": n, "url": u, "prompt": p.format(since=since)} for n, u, p in HTML_SOURCES]}


def score_news(items, terms):
    """Stage 1: title hits 3, body hits 1, official +5 (always kept), HN points >= 100 +3."""
    pats = [re.compile(r"(?<![\w-])" + re.escape(t.lower()) + r"(?![\w-])") for t in terms if len(t) > 1]
    for i in items:
        title, body = i["title"].lower(), i["body"].lower()
        i["score"] = sum(3 * bool(p.search(title)) + bool(p.search(body)) for p in pats) + 5 * i["official"] + 3 * (i.get("points", 0) >= 100)
    return [i for i in items if i["official"]] + sorted((i for i in items if not i["official"] and i["score"] >= NEWS_MIN), key=lambda i: -i["score"])[:NEWS_KEEP]


def news(tmp, categories=()):
    """Stage-1 filter of news_raw.json with Toolkit, CLI, platform and problem terms; writes news.json."""
    tmp = Path(tmp)
    raw = json.loads((tmp / "news_raw.json").read_text())
    c = load_json(tmp / "agent_c.json")
    unknown = [x for x in categories if x not in CATEGORY_TERMS]
    if unknown:
        print("unknown categories ignored: " + ", ".join(unknown), file=sys.stderr)
    terms = {i["name"] for i in c.get("items", []) if i["name"] not in BUILTIN_COMMANDS} | {p["plugin"].split("@")[0] for p in c.get("plugins", [])}
    terms |= set((load_json(tmp / "upstream.json").get("clis") or {}).get("installed", []))
    terms |= set(PLATFORM_TERMS) | {t for cat in categories for t in CATEGORY_TERMS.get(cat, [])}
    out = {"items": score_news(raw["items"], terms), "html_sources": raw["html_sources"], "errors": raw["errors"]}
    (tmp / "news.json").write_text(dumps(out))
    print(tmp / "news.json", len(out["items"]), "items")


def split_input(inp):
    """Cut an agent input into pieces of whole Sessions in time order, each about SPLIT_TOKENS.
    The rest of the input (B's whole-Window lists, `previous_findings`) rides along in every piece."""
    size = lambda o: len(dumps(o)) / 4
    ss = inp["sessions"]
    if not ss or size(inp) <= SPLIT_TOKENS:
        return [inp]
    rest = {k: v for k, v in inp.items() if k != "sessions"}
    sizes = [size(x) for x in ss]
    room = max(SPLIT_TOKENS - size(rest), SPLIT_TOKENS // 4)  # a big fixed part overshoots the cap rather than blocking the split
    n = math.ceil(sum(sizes) / room)
    per = sum(sizes) / n
    pieces, cur, acc = [], [], 0
    for x, sz in zip(ss, sizes):
        if cur and acc >= per and len(pieces) < n - 1:
            pieces.append(cur)
            cur, acc = [], 0
        cur.append(x)
        acc += sz
    pieces.append(cur)
    return [{**rest, "sessions": ps} for ps in pieces]


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
    start_insights(tmp)
    (tmp / "state.json").write_text(json.dumps({"redo": redo, "timestamp": start.isoformat()}))
    (tmp / "digest.json").write_text(dumps(dg))
    prev = previous_findings(redo)
    splits = {}
    for a, fn in AGENT_INPUTS.items():
        inp = fn(dg)
        if prev is not None:
            inp["previous_findings"] = prev[a]
        pieces = split_input(inp) if a != "c" else [inp]  # C is never split
        names = [f"agent_{a}_{i + 1}.json" for i in range(len(pieces))] if len(pieces) > 1 else [f"agent_{a}.json"]
        if len(pieces) > 1:
            splits[a] = names
        for nm, pc in zip(names, pieces):
            (tmp / nm).write_text(dumps(pc))
    (tmp / "splits.json").write_text(json.dumps(splits))
    (tmp / "previous.json").write_text(json.dumps(prev, separators=(",", ":")))
    up = build_upstream(dg, cursor(redo, start), first=prev is None)
    (tmp / "upstream.json").write_text(json.dumps(up, separators=(",", ":")))
    (tmp / "news_raw.json").write_text(json.dumps(fetch_news(cursor(redo, start)), separators=(",", ":")))
    (tmp / "draft.md").write_text(SKELETON.format(sessions=dg["n_sessions"], projects=dg["n_projects"]))
    (tmp / "metrics.json").write_text(dumps(compute_metrics(dg)))
    for a, names in splits.items():
        print(f"agent {a.upper()} input split into {len(names)} pieces: see splits.json")
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
    findings = re.search(r"^## Findings\n(.*?)(?=^## |\Z)", body, re.M | re.S)
    n = len(re.findall(r"^### \d+\.", findings.group(1) if findings else "", re.M))
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
    elif cmd == "insights" and args:
        insights(args[0])
    elif cmd == "news" and args:
        news(args[0], args[1:])
    elif cmd == "commit" and args:
        commit(args[0])
    else:
        sys.exit("usage: retro.py prepare [--redo] | context <session> <turn> [<temp folder>] | insights <temp folder> | news <temp folder> [<category>...] | commit <draft.md> | status")
