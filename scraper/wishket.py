"""
위시켓(wishket.com) 프로젝트 의뢰 목록 크롤러.

위시켓은 필터 상태를 `d` 파라미터(base64 인코딩)로 전달한다.
외주/상주를 각각 별도 URL로 요청해서 work_type을 확정하고,
모집마감제외도 URL 단에서 처리된다.

외주 + 모집마감제외: ?d=A4FwvCCGDODWD6AjGBTAJgMhQYzWAKgE4CuKQA%3D%3D
상주 + 모집마감제외: ?d=A4FwvCCmBOC2D6AjAhgZ0gEwGSQMYbABVoBXSIA%3D

카드 구조:
  div.project-info-box
    a.project-link              ← href + 제목(p태그)
    p.budget span.body-1-medium ← 예산
    p.start-recruitment-data    ← "· 등록일자 2026.07.01."
    span.skill-chip             ← 스킬 태그 (여러 개)
    div.project-type-mark       ← "외주" or "기간제"
"""

import re
import time
import requests
from bs4 import BeautifulSoup

from common import HEADERS

BASE_URL = "https://www.wishket.com/project/"

# 외주/상주 각각 모집마감제외 필터 적용된 URL 파라미터
FILTER_URLS = [
    ("원격", "A4FwvCCGDODWD6AjGBTAJgMhQYzWAKgE4CuKQA=="),  # 외주 + 모집마감제외
    ("상주", "A4FwvCCmBOC2D6AjAhgZ0gEwGSQMYbABVoBXSIA="),  # 상주 + 모집마감제외
]


def _parse_date(raw: str) -> str:
    """'· 등록일자 2026.07.01.' → '2026-07-01'"""
    m = re.search(r"(\d{4})\.(\d{2})\.(\d{2})", raw)
    if m:
        return f"{m.group(1)}-{m.group(2)}-{m.group(3)}"
    return ""


def _parse_cards(soup, work_type: str) -> list:
    items = []
    cards = soup.select("div.project-info-box")

    for card in cards:
        try:
            # 제목 + URL
            link_tag = card.select_one("a.project-link")
            if not link_tag:
                continue
            title_tag = link_tag.select_one("p")
            if not title_tag:
                continue

            title = title_tag.get_text(strip=True)
            href = link_tag.get("href", "")
            url = href if href.startswith("http") else f"https://www.wishket.com{href}"

            # 예산
            budget_el = card.select_one("p.budget span.body-1-medium")
            budget = budget_el.get_text(strip=True) if budget_el else ""

            # 등록일
            date_el = card.select_one("p.start-recruitment-data")
            posted_at = _parse_date(date_el.get_text()) if date_el else ""

            # 스킬 태그
            skill_els = card.select("span.skill-chip")
            tags = [s.get_text(strip=True) for s in skill_els if s.get_text(strip=True)]

            # 프로젝트 유형 (외주 / 기간제)
            type_el = card.select_one("div.project-type-mark")
            if type_el:
                type_text = type_el.get_text(strip=True)
                if type_text and type_text not in tags:
                    tags.insert(0, type_text)

            items.append({
                "source":    "위시켓",
                "title":     title,
                "url":       url,
                "budget":    budget,
                "posted_at": posted_at,
                "work_type": work_type,  # URL 기준으로 확정
                "tags":      tags[:8],
            })
        except Exception as e:
            print(f"[wishket] parse error: {e}")
            continue

    return items


def fetch() -> list:
    all_items = []

    for work_type, d_param in FILTER_URLS:
        try:
            res = requests.get(
                BASE_URL,
                params={"d": d_param},
                headers={
                    **HEADERS,
                    "Referer": "https://www.wishket.com/",
                    "Accept":  "text/html,application/xhtml+xml",
                },
                timeout=15,
            )
            res.raise_for_status()
        except Exception as e:
            print(f"[wishket] {work_type} fetch failed: {e}")
            continue

        soup = BeautifulSoup(res.text, "html.parser")
        items = _parse_cards(soup, work_type)
        print(f"[wishket] {work_type} → {len(items)}건")
        all_items.extend(items)
        time.sleep(0.8)

    return all_items


if __name__ == "__main__":
    result = fetch()
    print(f"\n[wishket] 총 {len(result)}건 수집")
    for r in result[:5]:
        print(r)
