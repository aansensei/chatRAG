"""Retrieval regression check — a small golden Q&A set grounded in the real
AanJSC_Documents KB content, run against the live /chat endpoint.

Checks retrieval quality specifically (does the right document surface in
"sources"), not answer-generation quality — the LLM's phrasing is nondeterministic
and provider-dependent, but which document gets retrieved for a given question
should be stable, so that's the signal worth catching regressions on.

Usage (server must be running on localhost:8000):
  python scripts/eval_retrieval.py

Exit code is non-zero if any case fails, so this can be wired into CI once a
DB connection is available there.
"""
import json
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from dotenv import load_dotenv
load_dotenv(str(Path(__file__).resolve().parents[1] / ".env"))

import httpx
from jose import jwt

from app.infrastructure.storage.local.auth_store import list_users, get_user_by_id

BASE = os.environ.get("EVAL_BASE_URL", "http://localhost:8000")

# Each case: a question an employee might realistically ask, and a filename
# substring that MUST appear among the retrieved sources for the case to pass.
# Grounded in real documents already in the KB — update this list if those
# documents are renamed/removed.
GOLDEN_SET = [
    {"question": "Công ty đã ký hợp đồng hợp tác gì với NASA?", "expect_filename": "NASA_PhaseII"},
    {"question": "Ngân sách R&D giai đoạn 2024-2029 là bao nhiêu?", "expect_filename": "NganSach_RnD"},
    {"question": "Chính sách phúc lợi nhân viên năm 2026 gồm những gì?", "expect_filename": "ChinhSach_PhucLoi_NhanVien"},
    {"question": "Báo cáo tài chính quý 4 năm 2025 của công ty thế nào?", "expect_filename": "BaoCao_TaiChinh_QuyIV"},
    {"question": "Kế hoạch marketing năm 2026 có những mục tiêu gì?", "expect_filename": "KeHoach_Marketing_2026"},
    {"question": "KPI theo quý năm 2025 của phòng kinh doanh là gì?", "expect_filename": "KPI_TheoQuy"},
    {"question": "Chính sách bảo mật thông tin của công ty quy định gì?", "expect_filename": "ChinhSach_BaoMat_ThongTin"},
    {"question": "Sơ đồ tổ chức công ty năm 2026 ra sao?", "expect_filename": "SoDoToChuc_CongTy"},
    {"question": "Quy trình tuyển dụng nhân sự của công ty diễn ra thế nào?", "expect_filename": "QuyTrinh_TuyenDung"},
    {"question": "Công ty có kế hoạch mở rộng thị trường quốc tế không?", "expect_filename": "MoRong_ThiTruongQuocTe"},
]


def _get_token() -> str:
    users = list_users()
    admin = next((u for u in users if u.get("role") == "admin"), None)
    if not admin:
        print("No admin user found — cannot run eval.")
        sys.exit(1)
    u = get_user_by_id(admin["id"])
    secret = os.environ["JWT_SECRET_KEY"]
    alg = os.environ.get("JWT_ALGORITHM", "HS256")
    return jwt.encode({"sub": u["id"], "email": u["email"], "role": u["role"], "exp": int(time.time()) + 3600}, secret, algorithm=alg)


def run_case(token: str, case: dict) -> tuple[bool, list[str]]:
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    filenames: list[str] = []
    # Only care about retrieval, not the LLM's final phrasing — stop reading as
    # soon as a "sources" event arrives instead of waiting for the full answer
    # to finish streaming (which can be slow/blocked independently of retrieval,
    # e.g. by an exhausted LLM provider quota).
    with httpx.stream("POST", f"{BASE}/chat", headers=headers, json={"question": case["question"]}, timeout=60) as r:
        for line in r.iter_lines():
            if not line.startswith("data: "):
                continue
            try:
                ev = json.loads(line[6:])
            except json.JSONDecodeError:
                continue
            if ev.get("type") == "sources" and ev.get("sources"):
                for s in ev["sources"]:
                    fn = s.get("filename", "")
                    if fn and fn not in filenames:
                        filenames.append(fn)
                break
            if ev.get("type") == "done":
                if ev.get("sources"):
                    for s in ev["sources"]:
                        fn = s.get("filename", "")
                        if fn and fn not in filenames:
                            filenames.append(fn)
                break
    passed = any(case["expect_filename"] in fn for fn in filenames)
    return passed, filenames


def main() -> None:
    token = _get_token()
    results = []
    for case in GOLDEN_SET:
        passed, filenames = run_case(token, case)
        results.append((passed, case, filenames))
        status = "PASS" if passed else "FAIL"
        print(f"[{status}] {case['question']}")
        if not passed:
            print(f"       expected filename containing: {case['expect_filename']}")
            print(f"       got sources: {filenames}")

    total = len(results)
    passed_count = sum(1 for p, _, _ in results if p)
    print(f"\n{passed_count}/{total} passed")
    sys.exit(0 if passed_count == total else 1)


if __name__ == "__main__":
    main()
