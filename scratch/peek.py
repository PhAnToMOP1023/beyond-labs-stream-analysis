import json

rows = []
for line in open("chatgpt_stream_full.txt", encoding="utf-8"):
    if line.startswith("data: "):
        rows.append(line[6:].rstrip("\n"))

for i in (27, 28, 29):
    print(f"\n=== EVENT {i} ({len(rows[i])} chars) ===")
    print(rows[i][:1800])

def walk(o, path=""):
    if isinstance(o, dict):
        for k, v in o.items():
            if k in ("queries", "search_queries"):
                print("FOUND", k, "at", path or "/", "->", json.dumps(v)[:400])
            walk(v, path + "/" + k)
    elif isinstance(o, list):
        for n, v in enumerate(o):
            walk(v, f"{path}[{n}]")

print("\n=== ALL 'queries' FIELDS IN THE STREAM ===")
for i, r in enumerate(rows):
    try:
        j = json.loads(r)
    except Exception:
        continue
    print("-- event", i)
    walk(j)