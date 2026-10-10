import json, re, sys
from urllib.parse import urlsplit

tag = sys.argv[1] if len(sys.argv) > 1 else "run"
data = json.load(open("reconstructed.json", encoding="utf-8"))

def text_of(m):
    return "".join(x for x in m["content"].get("parts", []) if isinstance(x, str))

# retrieved: key by (ref_type, ref_index); keep the entry with a snippet if there is one
retrieved = {}
for w in data:
    for g in w["message"].get("metadata", {}).get("search_result_groups", []):
        for en in g.get("entries", []):
            r = en.get("ref_id") or {}
            key = (r.get("ref_type"), r.get("ref_index"))
            old = retrieved.get(key)
            if old is None or (en.get("snippet") and not old.get("snippet")):
                retrieved[key] = {
                    "ref_type": key[0], "ref_index": key[1],
                    "url": en["url"].split("?utm_source")[0].replace("&utm_source=chatgpt.com", ""),
                    "host": urlsplit(en["url"]).netloc, "title": en.get("title"),
                    "snippet": en.get("snippet", ""), "pub_date": en.get("pub_date"),
                }

# cited: every ref inside <Cite refs={[...]}/> tags in the answer text
cites = []
for w in data:
    m = w["message"]
    if m.get("channel") != "final":
        continue
    for tagtxt in re.findall(r'<Cite refs=\{\[(.*?)\]\}', text_of(m)):
        for ref in re.findall(r'"turn(\d+)([A-Za-z_]+?)(\d+)"', tagtxt):
            cites.append((ref[1], int(ref[2])))
cited = set(cites)

for key, d in retrieved.items():
    d["cited"] = (key[0], key[1]) in cited

print("retrieved:", len(retrieved), "| cite tags refs:", len(cites), "| unique cited:", len(cited))
print("cited and found in retrieved:", sum(1 for d in retrieved.values() if d["cited"]))
print("cited refs NOT found in retrieved:", sorted(cited - set(retrieved)))

print("\n=== CITED ===")
for d in retrieved.values():
    if d["cited"]:
        print(f'{d["ref_type"]}{d["ref_index"]} | {d["host"]} | {d["title"][:60]} | {d["url"][:80]}')

print("\n=== RETRIEVED BUT NOT CITED (first 15) ===")
n = 0
for d in retrieved.values():
    if not d["cited"]:
        n += 1
        if n <= 15:
            print(f'{d["ref_type"]}{d["ref_index"]} | {d["host"]} | {d["title"][:60]}')
print("not cited total:", n)

json.dump(list(retrieved.values()), open(f"sources_final_{tag}.json", "w", encoding="utf-8"), indent=1)
print(f"\nSaved sources_final_{tag}.json")