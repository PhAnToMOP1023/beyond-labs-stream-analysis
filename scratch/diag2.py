import json, re

data = json.load(open("reconstructed.json", encoding="utf-8"))

entries = []
for w in data:
    for g in w["message"].get("metadata", {}).get("search_result_groups", []):
        for en in g.get("entries", []):
            entries.append((g.get("domain"), en))

print("total raw entries (with duplicates):", len(entries))

print("\n=== RAW YOUTUBE ENTRIES (all keys, first 3) ===")
n = 0
for dom, en in entries:
    if "youtube.com/watch" in en.get("url", ""):
        n += 1
        if n <= 3:
            print("group domain:", dom)
            print(json.dumps(en, indent=1)[:1800])
print("youtube watch entries:", n)

print("\n=== RAW ENTRIES FOR THE n8n.io-LABELLED TITLES (first 2) ===")
m = 0
for dom, en in entries:
    if dom == "n8n.io" and "How to Build AI Agents" in en.get("title", ""):
        m += 1
        if m <= 2:
            print("group domain:", dom)
            print(json.dumps(en, indent=1)[:1500])

print("\n=== KEYS THAT MIGHT HOLD VIDEO/CHANNEL DATA ===")
pat = re.compile(r"channel|view|like|verified|subscriber|follower|description|video|duration|author|upload", re.I)
seen = set()

def walk(o, path=""):
    if isinstance(o, dict):
        for k, v in o.items():
            p = f"{path}/{k}"
            if pat.search(k):
                key = re.sub(r"\[\d+\]", "[]", p)
                if key not in seen:
                    seen.add(key)
                    print(key, "->", json.dumps(v)[:160])
            walk(v, p)
    elif isinstance(o, list):
        for i, v in enumerate(o):
            walk(v, f"{path}[{i}]")

for w in data:
    md = w["message"].get("metadata", {})
    md = {k: v for k, v in md.items() if k not in ("model_dil_v2",)}
    walk(md)