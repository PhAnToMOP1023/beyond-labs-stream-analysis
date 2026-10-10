import json, datetime

SRC = "chatgpt_stream_full.txt"
errors = []

def events(path):
    out = []
    for line in open(path, encoding="utf-8"):
        if line.startswith("data: "):
            b = line[6:].strip()
            if b and b != "[DONE]":
                try:
                    out.append(json.loads(b))
                except Exception:
                    pass
    return out

def walk_to(root, parts):
    cur = root
    for p in parts:
        cur = cur[int(p)] if isinstance(cur, list) else cur[p]
    return cur

def apply(root, p, o, v):
    parts = [x for x in p.split("/") if x]
    if not parts:
        return
    try:
        parent = walk_to(root, parts[:-1])
        key = parts[-1]
        if isinstance(parent, list):
            idx = len(parent) if key == "-" else int(key)
            if o == "append" and idx < len(parent):
                cur = parent[idx]
                if isinstance(cur, str):
                    parent[idx] = cur + v
                elif isinstance(cur, list):
                    cur.extend(v if isinstance(v, list) else [v])
                else:
                    parent[idx] = v
            elif o == "replace" and idx < len(parent):
                parent[idx] = v
            else:
                parent.insert(idx, v)
        else:
            if o == "append":
                cur = parent.get(key)
                if isinstance(cur, str):
                    parent[key] = cur + v
                elif isinstance(cur, list):
                    cur.extend(v if isinstance(v, list) else [v])
                else:
                    parent[key] = v
            else:
                parent[key] = v
    except Exception as e:
        errors.append((p, o, str(e)))

wraps, order = {}, []
cur, last = None, ("", "append")
for e in events(SRC):
    if not isinstance(e, dict) or "v" not in e:
        continue
    v, p, o = e["v"], e.get("p"), e.get("o")
    if isinstance(v, dict) and "message" in v and not p and o in (None, "add"):
        cur = v
        mid = v["message"]["id"]
        if mid not in wraps:
            order.append(mid)
        wraps[mid] = cur
        continue
    if cur is None:
        continue
    if p is None and o is None:
        p, o = last
    elif p is None:
        p = last[0]
    elif o is None:
        o = last[1]
    if o == "patch" and isinstance(v, list):
        sl = ("", "append")
        for s in v:
            sp, so = s.get("p", sl[0]), s.get("o", sl[1])
            sl = (sp, so)
            apply(cur, sp, so, s.get("v"))
    else:
        last = (p, o)
        apply(cur, p, o, v)

def msg(i):
    return wraps[i]["message"]

def text_of(m):
    return "".join(x for x in m["content"].get("parts", []) if isinstance(x, str))

print("messages rebuilt:", len(order), "| patch errors:", len(errors))
for mid in order:
    m = msg(mid)
    md = m.get("metadata", {})
    print(mid[:8], m["author"]["role"], m["author"].get("name"), "->", m.get("recipient"),
          "| ch:", m.get("channel"), "| text:", len(text_of(m)),
          "| groups:", len(md.get("search_result_groups", [])),
          "| refs:", len(md.get("content_references", [])),
          "| safe_urls:", len(md.get("safe_urls", [])))

queries = []
for mid in order:
    for k, val in msg(mid).get("metadata", {}).items():
        if "quer" in k.lower():
            queries.append({"msg": mid[:8], "key": k, "value": val})
print("\n=== FAN-OUT QUERIES ===")
print(json.dumps(queries, indent=1)[:2500])

retrieved = {}
for mid in order:
    for g in msg(mid).get("metadata", {}).get("search_result_groups", []):
        for en in g.get("entries", []):
            u = en.get("url")
            if u and u not in retrieved:
                d = dict(en)
                d["domain"] = g.get("domain")
                d["msg"] = mid[:8]
                if isinstance(d.get("pub_date"), (int, float)):
                    d["pub_date_iso"] = datetime.datetime.fromtimestamp(
                        d["pub_date"], datetime.timezone.utc).strftime("%Y-%m-%d")
                retrieved[u] = d
print("\n=== RETRIEVED SOURCES:", len(retrieved), "| with snippet:",
      sum(1 for d in retrieved.values() if d.get("snippet")))
for d in list(retrieved.values())[:3]:
    print(json.dumps(d)[:500])

final = max(order, key=lambda i: len(text_of(msg(i))))
fm = msg(final)
print("\n=== FINAL ANSWER message", final[:8], "| text chars:", len(text_of(fm)))
print(text_of(fm)[:300].replace("\n", " "))
refs = fm.get("metadata", {}).get("content_references", [])
print("content_references:", len(refs))
for r in refs[:3]:
    print(json.dumps(r)[:600])

json.dump([wraps[i] for i in order], open("reconstructed.json", "w", encoding="utf-8"), indent=1)
json.dump(list(retrieved.values()), open("sources_retrieved.json", "w", encoding="utf-8"), indent=1)
json.dump(queries, open("queries.json", "w", encoding="utf-8"), indent=1)
print("\nSaved reconstructed.json, sources_retrieved.json, queries.json")