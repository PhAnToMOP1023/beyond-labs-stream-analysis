import re, json, collections

KEYWORDS = ["search_queries", "search_result_groups", "content_references",
            "citations", "snippet", "pub_date", "queries", "web.run", "safe_urls"]

rows = []
for line in open("chatgpt_stream_full.txt", encoding="utf-8"):
    line = line.rstrip("\n")
    m = re.match(r'^\s*(\w+)\t(.*?)\t\d\d:\d\d:\d\d\.\d+\s*$', line)
    if m:
        rows.append((m.group(1), m.group(2)))
    elif line.startswith("data: "):
        rows.append(("data", line[6:]))

print("Total events:", len(rows))
print("Event types:", dict(collections.Counter(t for t, _ in rows)))

print("\n--- Keyword hits (event number, type, keywords) ---")
for i, (t, d) in enumerate(rows):
    hits = [k for k in KEYWORDS if k in d]
    if hits:
        print(i, t, hits)

print("\n--- Patch paths and operations (count) ---")
ops = collections.Counter()
for t, d in rows:
    try:
        j = json.loads(d)
    except Exception:
        continue
    if not isinstance(j, dict):
        continue
    if "o" in j:
        ops[(j.get("p"), j.get("o"))] += 1
    if isinstance(j.get("v"), list):
        for sub in j["v"]:
            if isinstance(sub, dict) and "o" in sub:
                ops[(sub.get("p"), sub.get("o"))] += 1
for (p, o), n in ops.most_common(25):
    print(n, p, o)