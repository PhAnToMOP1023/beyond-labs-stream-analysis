import json, re

rows = []
for line in open("chatgpt_stream_full.txt", encoding="utf-8"):
    if line.startswith("data: "):
        rows.append(line[6:].strip())

# 1) Where does non-empty snippet text appear?
print("=== NON-EMPTY SNIPPETS ===")
n = 0
for i, r in enumerate(rows):
    for m in re.finditer(r'"snippet":"([^"]{5,})', r):
        n += 1
        if n <= 4:
            print(f"event {i}: ...{r[max(0, m.start()-150):m.start()+350]}")
print("total non-empty snippet hits:", n)

# 2) Context around content_references / citations in each event that has them
print("\n=== content_references CONTEXT ===")
for i, r in enumerate(rows):
    k = r.find("content_references")
    if k != -1 and i in (13, 34, 81, 93, 110):
        print(f"\n--- event {i} (len {len(r)}) ---")
        print(r[max(0, k-100):k+1300])

# 3) Patch shapes that appear around the reference events
print("\n=== SHAPE OF EVENTS 30-34, 92-93 (first 350 chars each) ===")
for i in list(range(30, 35)) + [92, 93]:
    print(f"[{i}]", rows[i][:350])