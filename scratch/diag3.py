import re

rows = [l[6:].strip() for l in open("chatgpt_stream_2.txt", encoding="utf-8") if l.startswith("data: ")]
print("events:", len(rows))

print("\n=== EVENTS MENTIONING youtube (index, count, context) ===")
shown = 0
for i, r in enumerate(rows):
    c = r.lower().count("youtube")
    if c:
        shown += 1
        if shown <= 12:
            k = r.lower().find("youtube")
            print(i, c, "|", r[max(0, k - 120):k + 160].replace("\n", " "))
print("events with youtube:", shown)

print("\n=== VIDEO METADATA WORDS ===")
for w in ["channel", "subscriber", "view_count", "viewCount", "likes", "like_count", "verified", "duration", "uploader"]:
    hits = [(i, r) for i, r in enumerate(rows) if w in r]
    line = f"{w}: {len(hits)} events"
    if hits:
        i, r = hits[0]
        k = r.find(w)
        line += f" | first at {i}: " + r[max(0, k - 80):k + 140].replace("\n", " ")
    print(line)

print("\n=== PILL LABELS IN ANSWER TEXT ===")
ans = open("answer_text.md", encoding="utf-8").read()
for label in ["n8n Help Center", "freeCodeCamp", "Class Central", "YouTube"]:
    ks = [m.start() for m in re.finditer(re.escape(label), ans)]
    print(label, "->", len(ks))
    if ks:
        print("   ", ans[max(0, ks[0] - 100):ks[0] + 120].replace("\n", " "))