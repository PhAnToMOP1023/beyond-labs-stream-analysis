import json

har = json.load(open("chatgpt_session.har", encoding="utf-8"))
found = False
for e in har["log"]["entries"]:
    url = e["request"]["url"]
    mime = e["response"]["content"].get("mimeType", "")
    text = e["response"]["content"].get("text", "")
    if url.split("?")[0].endswith("/conversation") or "event-stream" in mime:
        print("URL:", url[:90], "| mime:", mime, "| chars:", len(text))
        if len(text) > 1000:
            open("chatgpt_stream_full.txt", "w", encoding="utf-8").write(text)
            found = True
print("Saved chatgpt_stream_full.txt" if found else "No stream body found in HAR")