"""Context and timing of one /retro run: python3 runstats.py <main Session .jsonl>"""
import collections, glob, json, sys
from datetime import datetime


def secs(a, b):
    p = lambda s: datetime.fromisoformat(s.replace("Z", "+00:00"))
    return (p(b) - p(a)).total_seconds()


def agent(path):
    reqs, ts = {}, []
    for line in open(path, errors="replace"):
        r = json.loads(line)
        if r.get("timestamp"):
            ts.append(r["timestamp"])
        if r.get("type") == "assistant":
            u = r["message"].get("usage") or {}
            reqs[r.get("requestId")] = (r["message"].get("model"), u.get("input_tokens", 0) + u.get("cache_read_input_tokens", 0)
                                        + u.get("cache_creation_input_tokens", 0), u.get("cache_read_input_tokens", 0))
    ctx = [c for _, c, _ in reqs.values()]
    return (f"{len(reqs)} requests, {secs(ts[0], ts[-1]):.0f}s, first {ctx[0]:,}, final {ctx[-1]:,}, "
            f"cache reads {sum(cr for *_, cr in reqs.values()):,}, {sorted({m for m, *_ in reqs.values() if m})}")


main = sys.argv[1]
for f in sorted(glob.glob(main[:-6] + "/subagents/*.jsonl")):
    print(json.load(open(f[:-6] + ".meta.json")).get("description"), "|", agent(f))
recs = [json.loads(l) for l in open(main, errors="replace")]
i = next(i for i, r in enumerate(recs) if r.get("type") == "user" and "<command-name>/retro</command-name>" in json.dumps(r.get("message")))
models = {}
for r in recs[i:]:
    if r.get("type") == "assistant":
        models[r.get("requestId")] = r["message"].get("model")
    if r.get("type") == "user" and "retro/findings.md" in json.dumps(r.get("message")):
        break  # commit printed the findings path
print(f"main | /retro to commit {secs(recs[i]['timestamp'], r['timestamp']):.0f}s, requests by model {dict(collections.Counter(models.values()))}")
