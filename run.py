#!/usr/bin/env python3
"""
run.py — One-click runner for Observathon
Team: Đàm Mạnh Dũng

Usage:
  python3 run.py              → chạy public test
  python3 run.py private      → chạy private test
  python3 run.py public       → chạy public test
"""
import os
import sys
import glob
import json
import subprocess
import shutil
import tempfile

# ──────────────────────────────────────────────
# CẤU HÌNH — chỉnh ở đây nếu cần
# ──────────────────────────────────────────────
TEAM = "Đàm Mạnh Dũng"
API_KEY = "sk-ws-H.IILDPE.1SG4.MEQCIEVQxPm_BhPbBE9Vo7pwhYUmMnnwdlLng-DZZI9-_j4lAiAWDsSpGbAeO2eTXWjKxVamGuDQDKHbvlDTJtaOZHXnXg"
BASE_URL = "https://dashscope-intl.aliyuncs.com/compatible-mode/v1"
CONCURRENCY = 8

# Danh sách model theo thứ tự ưu tiên (model đầu = tốt nhất)
# Script sẽ tự động thử từng model nếu model trước bị lỗi quota
MODEL_FALLBACK_LIST = [
    "qwen3-max",
    "qwen-max",
    "qwen3.5-122b-a10b",
    "qwen3.7-plus",
    "qwen3.6-plus",
    "qwen3-vl-flash",
]

ROOT = os.path.dirname(os.path.abspath(__file__))

# ──────────────────────────────────────────────
# AUTO-DETECT binary names (không cần biết tên cố định)
# ──────────────────────────────────────────────
def find_binary(pattern):
    matches = glob.glob(os.path.join(ROOT, pattern))
    if not matches:
        print(f"\033[1;31m[ERROR]\033[0m Không tìm thấy binary khớp với '{pattern}'")
        print(f"        Hãy đảm bảo file tồn tại trong: {ROOT}")
        sys.exit(1)
    # Auto chmod +x nếu chưa có quyền execute
    for m in matches:
        if not os.access(m, os.X_OK):
            os.chmod(m, 0o755)
            print(f"\033[1;33m[INFO]\033[0m Auto chmod +x: {os.path.basename(m)}")
    # Ưu tiên file executable
    for m in matches:
        if os.access(m, os.X_OK):
            return m
    return matches[0]


def banner(msg, color="\033[1;36m"):
    width = 60
    print(f"\n{color}{'='*width}\033[0m")
    print(f"{color}  {msg}\033[0m")
    print(f"{color}{'='*width}\033[0m")


def run(cmd, env=None):
    """Chạy lệnh shell, in output realtime ra terminal."""
    result = subprocess.run(
        cmd,
        env=env,
        cwd=ROOT,
        stdout=sys.stdout,   # stream thẳng ra terminal
        stderr=sys.stderr,   # stream stderr ra terminal
    )

    if result.returncode != 0:
        print(f"\033[1;31m[ERROR]\033[0m Lệnh thất bại: {' '.join(cmd)}")
        sys.exit(result.returncode)


def parse_results(run_file):
    """In báo cáo đẹp từ file kết quả."""
    try:
        with open(run_file, encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        print(f"\033[1;31m[WARN]\033[0m Không đọc được {run_file}: {e}")
        return

    phase = data.get("phase", "UNKNOWN").upper()
    results = data.get("results", [])
    success = [r for r in results if r.get("status") == "ok"]
    fails   = [r for r in results if r.get("status") != "ok"]

    banner(f"📊 RUN REPORT — Phase: {phase}", "\033[1;32m")
    print(f"  \033[1;37mTotal  :\033[0m {len(results)}")
    print(f"  \033[1;32mOK     :\033[0m {len(success)}")
    print(f"  \033[1;31mFailed :\033[0m {len(fails)}")

    if fails:
        print(f"\n\033[1;31m  {'─'*50}\033[0m")
        print(f"\033[1;31m  FAILED REQUESTS (top {min(10, len(fails))})\033[0m")
        print(f"\033[1;31m  {'─'*50}\033[0m")
        for i, r in enumerate(fails[:10]):
            print(f"\n  \033[1;33m[Q{i+1}]\033[0m {r.get('question', '')[:90]}")
            print(f"  \033[1;31m[{r.get('status')}]\033[0m {str(r.get('answer', ''))[:80]}")
        if len(fails) > 10:
            print(f"\n  \033[35m... và {len(fails)-10} lỗi khác\033[0m")
    else:
        print(f"\n  \033[1;32m✨ TẤT CẢ REQUEST ĐỀU THÀNH CÔNG! ✨\033[0m")


def main():
    # Xác định testset từ argument
    testset = "public"
    if len(sys.argv) > 1:
        arg = sys.argv[1].lower()
        if arg in ("private", "public"):
            testset = arg
        else:
            print(f"\033[1;31m[ERROR]\033[0m Argument không hợp lệ: '{sys.argv[1]}'")
            print("        Dùng: python3 run.py [public|private]")
            sys.exit(1)

    out_file     = os.path.join(ROOT, f"run_{testset}.json")
    score_file   = os.path.join(ROOT, f"score_{testset}.json")
    findings     = os.path.join(ROOT, "solution", "findings.json")

    # Auto-detect binaries
    sim_bin   = find_binary("observathon-sim*")
    score_bin = find_binary("observathon-score*")

    banner(f"🚀 OBSERVATHON RUNNER — {testset.upper()} TEST", "\033[1;36m")
    print(f"  Team      : \033[1;32m{TEAM}\033[0m")
    print(f"  Testset   : \033[1;33m{testset}\033[0m")
    print(f"  Simulator : {os.path.basename(sim_bin)}")
    print(f"  Scorer    : {os.path.basename(score_bin)}")
    print(f"  Output    : {os.path.basename(out_file)}")

    # Thiết lập env
    env = os.environ.copy()
    env["OPENAI_API_KEY"]  = API_KEY
    env["OPENAI_BASE_URL"] = BASE_URL

    # ── BƯỚC 1: Chạy Simulator ──────────────────────
    banner("BƯỚC 1 / 3 — Chạy Simulator", "\033[1;35m")
    run([
        sim_bin,
        f"--testset={testset}",
        f"--concurrency", str(CONCURRENCY),
        "--out", out_file,
    ], env=env)

    # ── BƯỚC 2: In báo cáo ──────────────────────────
    banner("BƯỚC 2 / 3 — Phân tích kết quả", "\033[1;35m")
    parse_results(out_file)

    # ── BƯỚC 3: Chạy Scorer ─────────────────────────
    banner("BƯỚC 3 / 3 — Chạm điểm", "\033[1;35m")
    run([
        score_bin,
        "--run", out_file,
        "--findings", findings,
        "--team", TEAM,
        "--out", score_file,
    ], env=env)

    banner("✅ HOÀN THÀNH!", "\033[1;32m")
    print(f"  Kết quả lưu tại: \033[1;33m{os.path.basename(score_file)}\033[0m\n")


if __name__ == "__main__":
    main()
