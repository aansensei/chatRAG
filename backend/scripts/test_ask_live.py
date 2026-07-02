import sys, json, io, httpx

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

question = sys.argv[1]
model = sys.argv[2] if len(sys.argv) > 2 else "llama-3.3-70b-versatile"

answer = []
sources = []
with httpx.stream(
    "POST", "http://localhost:8000/chat",
    json={"question": question, "model": model}, timeout=90.0,
) as r:
    for line in r.iter_lines():
        if not line.startswith("data: "):
            continue
        try:
            ev = json.loads(line[6:])
        except json.JSONDecodeError:
            continue
        t = ev.get("type")
        if t == "token":
            answer.append(ev["token"])
        elif t == "sources":
            sources = ev.get("sources", [])
        elif t == "done" and not answer:
            answer.append(ev.get("answer", ""))

print("=== ANSWER ===")
print("".join(answer))
print("\n=== SOURCES ===")
for s in sources:
    print(" -", s.get("filename") or s.get("title"), "| similarity:", s.get("similarity"))
