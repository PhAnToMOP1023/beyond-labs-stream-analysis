import json, re, datetime
from urllib.parse import urlsplit, parse_qsl, urlencode

SRC = "chatgpt_stream_2.txt"
errors = []

def load(path):
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

def get(root, parts):
    cur = root
    for p in parts:
        cur = cur[int(p)] if isinstance(cur, list) else cur[p]
    return cur

def put(c, key, o, v):
    is_list = isinstance(c, list)
    idx = (len(c) if key == "-" else int(key)) if is_list else key
    exists = (idx < len(c)) if is_list else (key in c)
    cur = (c[idx] if exists else None)
    if o == "remove":
        if exists:
            del c[idx]
        return
    if o == "add" and is_list:
        c.insert(idx, v)
        return
    if o == "append" and exists:
        if isinstance(cur, str) and isinstance(v, str):
            v = cur + v
        elif isinstance(cur, list):
            v = cur + (v if isinstance(v, list) else [v])
        elif isinstance(cur, dict) and isinstance(v, dict):
            v = {**cur, **v}
    if is_list and not exists:
        c.append(v)
    else:
        c[idx] = v

def apply(root, p, o, v):
    parts = [x for x in p.split("/") if x]
    if not parts:
        return
    try:
        put(get(root, parts[:-1]), parts[-1], o, v)
    except Exception as e:
        errors.append((p, o, str(e)))

def is_ops(v):
    return isinstance(v, list) and v and all(isinstance(x, dict) and ("p" in x or "o" in x) for x in v)

wraps, order, cur, last = {}, [], None, ("", "append")
for e in load(SRC):
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
    if is_ops(v):
        sl = ("", "append")
        for s in v:
            sp, so = s.get("p", sl[0]), s.get("o", sl[1])
            sl = (sp, so)
            apply(cur, sp, so, s.get("v"))
        last = sl
        continue
    p = p if p is not None else last[0]
    o = o if o is not None else last[1]
    last = (p, o)
    apply(cur, p, o, v)

def M(i): return wraps[i]["message"]
def text_of(m): return "".join(x for x in m["content"].get("parts", []) if isinstance(x, str))

def norm(u):
    s = urlsplit(u)
    q = [(k, v) for k, v in parse_qsl(s.query) if k != "utm_source"]
    host = s.netloc.lower().removeprefix("www.")
    return host + s.path.rstrip("/") + (("?" + urlencode(q)) if q else "")

print("messages:", len(order), "| patch errors:", len(errors))
for er in errors[:5]:
    print("  err:", er)
for mid in order:
    m, md = M(mid), M(mid).get("metadata", {})
    if text_of(m) or md.get("search_result_groups") or md.get("safe_urls"):
        print(mid[:8], m["author"]["role"], "ch:", m.get("channel"), "| text:", len(text_of(m)),
              "| groups:", len(md.get("search_result_groups", [])), "| safe_urls:", len(md.get("safe_urls", [])))

# fan-out queries and reasoning titles
queries, reasoning = [], []
for mid in order:
    md = M(mid).get("metadata", {})
    sq = md.get("search_model_queries")
    if sq:
        queries += sq.get("queries", [])
    for t in md.get("reasoning_titles", []):
        if t not in reasoning:
            reasoning.append(t)
print("\n=== FAN-OUT QUERIES ===")
print(json.dumps(queries, indent=1))
print("=== REASONING TITLES ===")
print(json.dumps(reasoning, indent=1))

# retrieved sources: merge by normalized URL, prefer non-empty snippet
src = {}
for mid in order:
    for g in M(mid).get("metadata", {}).get("search_result_groups", []):
        for en in g.get("entries", []):
            k = norm(en["url"])
            d = src.setdefault(k, {"url": en["url"].split("?utm_source")[0], "domain": g.get("domain")})
            for f in ("title", "pub_date", "attribution"):
                if en.get(f):
                    d[f] = en[f]
            if en.get("snippet"):
                d["snippet"] = en["snippet"]
            d.setdefault("ref_ids", [])
            if en.get("ref_id") not in d["ref_ids"]:
                d["ref_ids"].append(en.get("ref_id"))
for d in src.values():
    if isinstance(d.get("pub_date"), (int, float)):
        d["pub_date_iso"] = datetime.datetime.fromtimestamp(d["pub_date"], datetime.timezone.utc).strftime("%Y-%m-%d")

# final answer text, safe_urls, citation signals
final_ids = [i for i in order if M(i).get("channel") == "final" and text_of(M(i))]
answer = "\n".join(text_of(M(i)) for i in final_ids)
text_urls = {norm(u) for u in re.findall(r'https?://[^\s)"\'>\]\\]+', answer)}
safe = {norm(u) for i in order for u in M(i).get("metadata", {}).get("safe_urls", []) if isinstance(u, str)}
for k, d in src.items():
    d["in_answer_text"] = k in text_urls
    d["in_safe_urls"] = k in safe

print("\n=== SOURCES:", len(src), "| with snippet:", sum(1 for d in src.values() if d.get("snippet")))
print("answer chars:", len(answer), "| urls in answer text:", len(text_urls), "| safe_urls:", len(safe))
for n, d in enumerate(src.values()):
    print(n, "| text:", int(d["in_answer_text"]), "| safe:", int(d["in_safe_urls"]),
          "| snip:", len(d.get("snippet", "")), "|", d.get("domain"), "|", d.get("title", "")[:55])

print("\n=== safe_urls sample ===")
for u in list(safe)[:30]:
    print(" ", u[:100])

raw = open(SRC, encoding="utf-8").read()
print("\n=== raw signals ===")
for sig in ['grouped_webpages', '"sources":[{', 'turn0search', 'turn0view', 'sources_footnote', 'youtube']:
    print(sig, raw.count(sig))
print("\nEntity values:", re.findall(r'<Entity value="([^"]+)"', answer)[:20])
print("\nANSWER TAIL:", answer[-500:].replace("\n", " "))

json.dump(list(src.values()), open("sources.json", "w", encoding="utf-8"), indent=1)
json.dump(queries, open("queries.json", "w", encoding="utf-8"), indent=1)
open("answer_text.md", "w", encoding="utf-8").write(answer)
json.dump([wraps[i] for i in order], open("reconstructed.json", "w", encoding="utf-8"), indent=1)
print("\nSaved sources.json, queries.json, answer_text.md, reconstructed.json")



from collections import Counter
print("ERROR GROUPS:", Counter(p.split("/")[3] if len(p.split("/")) > 3 else p for p, o, m in errors))