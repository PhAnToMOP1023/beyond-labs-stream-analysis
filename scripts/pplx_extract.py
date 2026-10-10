import json, re, sys

fn = sys.argv[1] if len(sys.argv) > 1 else "perplexity_stream.txt"
txt = open(fn, encoding="utf-8").read().replace("\r\n", "\n")

msgs = []
for b in [x for x in txt.split("\n\n") if x.strip()]:
    ev, data = None, None
    for line in b.splitlines():
        if line.startswith("event:"):
            ev = line[6:].strip()
        elif line.startswith("data:"):
            try:
                data = json.loads(line[5:].strip())
            except Exception:
                pass
    if ev == "message" and isinstance(data, dict):
        msgs.append(data)

print("message events:", len(msgs))
print("\n=== BLOCK TYPES PER EVENT ===")
for i, m in enumerate(msgs):
    types = [[k for k in b if k != "intended_usage"] + [b.get("intended_usage")] for b in m.get("blocks", [])]
    print(i, "| text_completed:", m.get("text_completed"), "| status:", m.get("status"), "| blocks:", types)

final = msgs[-1]
queries, sources, steps = [], [], []
for b in final.get("blocks", []):
    wb = b.get("workflow_block")
    if wb:
        for s in wb.get("steps", []):
            steps.append(s.get("title"))
            for it in s.get("items", []):
                p = it.get("payload", {})
                queries += p.get("queries_payload", {}).get("queries", [])
                sources += p.get("sources_payload", {}).get("sources", [])

web = []
for b in final.get("blocks", []):
    web += b.get("web_result_block", {}).get("web_results", [])

print("\nSTEPS:", steps)
print("QUERIES:", json.dumps(queries, indent=1))
print("sources_payload:", len(sources), "| web_results:", len(web))
for w in web[:12]:
    print(" -", (w.get("name") or "")[:60], "|", w.get("url", "")[:70], "| snippet chars:", len(w.get("snippet") or ""))
print("web_result meta_data keys:", sorted({k for w in web for k in (w.get("meta_data") or {})}))
print("web_result keys:", sorted({k for w in web for k in w}))

print("\n=== ANSWER TEXT / CITATION HUNT ===")
for b in final.get("blocks", []):
    for k, v in b.items():
        if k in ("workflow_block", "web_result_block", "answer_tabs_block", "intended_usage"):
            continue
        print("block key:", k, "->", json.dumps(v)[:700])
blob = json.dumps(final)
print("citation-like markers [n]:", len(re.findall(r"\[\d+\]", blob)))
for w in ("answer", "citations", "citation", "chunks", "markdown"):
    print(w, "->", blob.count(w))

json.dump(queries, open("perplexity_queries.json", "w"), indent=1)
json.dump(web, open("perplexity_sources.json", "w"), indent=1)
print("\nSaved perplexity_queries.json, perplexity_sources.json")
