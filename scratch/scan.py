import json, re, sys, collections

fn = sys.argv[1] if len(sys.argv) > 1 else "perplexity_stream.txt"
txt = open(fn, encoding="utf-8").read().replace("\r\n", "\n")

events = []
for b in [x for x in txt.split("\n\n") if x.strip()]:
    name, data = None, None
    for line in b.splitlines():
        if line.startswith("event:"):
            name = line[6:].strip()
        elif line.startswith("data:"):
            raw = line[5:].strip()
            try:
                data = json.loads(raw)
            except Exception:
                data = raw
    events.append((name, data))

print("events:", len(events), collections.Counter(n for n, _ in events))
print("\n=== TOP-LEVEL KEYS PER EVENT ===")
for i, (n, d) in enumerate(events):
    if isinstance(d, dict):
        print(i, n, "| chars:", len(json.dumps(d)), "|", list(d.keys())[:30])

pat = re.compile(r"query|queries|step|source|web_result|citation|snippet|url|reason|think|plan|block|usage|goal|search", re.I)
seen = set()
def walk(o, path=""):
    if isinstance(o, dict):
        for k, v in o.items():
            p = f"{path}/{k}"
            key = re.sub(r"\[\d+\]", "[]", p)
            if pat.search(k) and key not in seen:
                seen.add(key)
                print(key, "->", json.dumps(v)[:130])
            walk(v, p)
    elif isinstance(o, list):
        for i, v in enumerate(o[:3]):
            walk(v, f"{path}[{i}]")

print("\n=== KEY PATHS (first occurrence, last event with data) ===")
last = [d for n, d in events if isinstance(d, dict)]
if last:
    walk(last[-2] if len(last) > 1 else last[-1])