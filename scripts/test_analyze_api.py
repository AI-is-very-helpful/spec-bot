#!/usr/bin/env python3
"""
Azure Function API로 레포 분석 요청이 올바르게 처리되는지 테스트.
POST /api/messages 에 보낼 Teams 활동 형식으로 요청을 시뮬레이션.

사용법:
  # 로컬에서 함수 실행 후 (다른 터미널에서 func start)
  python scripts/test_analyze_api.py

  # 또는 함수 없이 핸들러 직접 호출 (분석 단계에서 Azure 설정 필요)
  python scripts/test_analyze_api.py --direct
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys

# 프로젝트 루트
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "src"))

# .env 로드
from pathlib import Path
env_path = Path(ROOT) / ".env"
if env_path.exists():
    from dotenv import load_dotenv
    load_dotenv(env_path)

REPO_URL = "https://github.com/AI-is-very-helpful/hae_shopping_mall"


def test_via_http():
    """실제 HTTP로 로컬 함수 호출 (func start 필요)"""
    try:
        import urllib.request
        req = urllib.request.Request(
            "http://localhost:7071/api/messages",
            data=json.dumps({
                "type": "message",
                "text": REPO_URL,
                "from": {"id": "test-user"},
                "conversation": {"id": "test-conv"},
                "channelData": {"channel": {"id": ""}, "tenant": {"id": ""}},
                "serviceUrl": "",
            }).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=120) as resp:
            body = resp.read().decode("utf-8")
            data = json.loads(body) if body.strip() else {}
            print("Status:", resp.status)
            print("Response (first 1500 chars):")
            print(json.dumps(data, ensure_ascii=False, indent=2)[:1500])
            if resp.status == 200 and (data.get("type") == "message" or "zip" in str(data).lower() or "download" in str(data).lower()):
                print("\n[OK] API responded successfully.")
            elif resp.status == 200 and "오류" in str(data) or "error" in str(data).lower():
                print("\n[INFO] API returned error message (check Azure/.env config).")
    except Exception as e:
        print("HTTP request failed:", e)
        print("Make sure 'func start' is running in another terminal.")


async def test_direct():
    """핸들러 직접 호출 (Azure 설정 없으면 분석 단계에서 실패)"""
    import azure.functions as func

    class MockRequest:
        method = "POST"

        def get_json(self):
            return {
                "type": "message",
                "text": REPO_URL,
                "from": {"id": "test"},
                "conversation": {"id": "c"},
                "channelData": {"channel": {"id": ""}, "tenant": {"id": ""}},
                "serviceUrl": "",
            }

    from presentation.handlers.http_handler import main as http_handler_main
    req = MockRequest()
    resp = await http_handler_main(req)
    body = resp.get_body().decode("utf-8") if resp.get_body() else ""
    data = json.loads(body) if body.strip() else {}
    print("Status:", resp.status_code)
    print("Response (first 2000 chars):")
    print(json.dumps(data, ensure_ascii=False, indent=2)[:2000])
    return resp.status_code, data


def main():
    ap = argparse.ArgumentParser(description="Test analyze API with hae_shopping_mall repo")
    ap.add_argument("--direct", action="store_true", help="Call handler directly (no func start)")
    args = ap.parse_args()
    if args.direct:
        status, _ = asyncio.run(test_direct())
        sys.exit(0 if status == 200 else 1)
    test_via_http()


if __name__ == "__main__":
    main()
