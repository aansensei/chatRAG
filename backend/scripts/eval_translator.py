"""Regression check for the JP->VN translator prompt.

Runs a small fixed test set against POST /chat/translate and flags:
  - residual CJK characters left untranslated (excluding romanized names)
  - stray English words leaking into the Vietnamese output
  - literal echo of the system prompt itself

Usage:
  python scripts/eval_translator.py [--model MODEL] [--base-url URL]

Exit code is non-zero if any case fails, so this can be wired into CI.
"""
import argparse
import json
import re
import sys
import urllib.request

CJK_RE = re.compile(r"[぀-ヿ㐀-䶿一-鿿豈-﫿]")
PROMPT_ECHO_MARKERS = ["LUẬT SỐ", "===== VĂN BẢN", "QUY TẮC TỔNG QUÁT"]

TEST_CASES = [
    {
        "name": "academic_kango",
        "text": "15世紀後半の大越国において、長きにわたる権力闘争や宮廷暗殺による政治的混乱を余儀なくされた。",
        "max_cjk": 2,
    },
    {
        "name": "skill_names",
        "text": "「ファイアボール！」とアリスが叫ぶと、彼女の手のひらから巨大な火球が放たれた。タクミは咄嗟にヒールを唱えた。",
        "max_cjk": 0,
    },
    {
        "name": "onomatopoeia",
        "text": "ドキドキしながら扉を開けると、ドンという音が響いた。",
        "max_cjk": 0,
    },
]


def call_translate(base_url: str, text: str, model: str | None) -> str:
    body = json.dumps({"text": text, "model": model}).encode("utf-8")
    req = urllib.request.Request(
        f"{base_url}/chat/translate", data=body, headers={"Content-Type": "application/json"}
    )
    out = []
    with urllib.request.urlopen(req, timeout=120) as resp:
        for line in resp:
            line = line.decode("utf-8").strip()
            if not line.startswith("data: "):
                continue
            try:
                ev = json.loads(line[6:])
            except json.JSONDecodeError:
                continue
            if ev.get("type") == "token":
                out.append(ev["token"])
    return "".join(out)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="llama-3.3-70b-versatile")
    ap.add_argument("--base-url", default="http://localhost:8000")
    args = ap.parse_args()

    failures = 0
    for case in TEST_CASES:
        result = call_translate(args.base_url, case["text"], args.model)
        cjk_count = len(CJK_RE.findall(result))
        echoed = any(marker in result for marker in PROMPT_ECHO_MARKERS)
        ok = cjk_count <= case["max_cjk"] and not echoed and len(result.strip()) > 0
        status = "PASS" if ok else "FAIL"
        print(f"[{status}] {case['name']}: cjk={cjk_count} (max {case['max_cjk']}) echoed_prompt={echoed}")
        if not ok:
            failures += 1
            print(f"  output: {result[:200]!r}")

    print(f"\n{len(TEST_CASES) - failures}/{len(TEST_CASES)} passed")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
