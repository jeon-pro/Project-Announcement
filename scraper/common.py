"""
공통 데이터 모델 및 유틸.
각 사이트 스크래퍼는 list[dict]를 반환하며, 아래 키를 따른다.

{
  "source": "위시켓",
  "title": "공고 제목",
  "url": "https://...",
  "budget": "300~500만원" 또는 "",
  "posted_at": "2026-06-28" (ISO 형식 문자열, 모르면 빈 문자열),
  "tags": ["React", "백엔드"]   # 선택
}
"""

import datetime
import json
import os

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )
}


def now_iso():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def save_merged(all_items, out_path):
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    payload = {
        "generated_at": now_iso(),
        "count": len(all_items),
        "items": all_items,
    }
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    print(f"Saved {len(all_items)} items to {out_path}")
