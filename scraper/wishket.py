"""
위시켓(wishket.com) 프로젝트 의뢰 목록 크롤러.

HTML 파일 분석 결과 확인된 실제 셀렉터 기준으로 구현.
위시켓은 서버사이드 렌더링(SSR) 방식이라 requests로 직접 파싱 가능.

카드 구조:
  div.project-info-box          ← 공고 1건
    a.project-link              ← 링크 + href
      p.subtitle-1-half-medium  ← 공고 제목
    p.budget
      span.body-1-medium        ← 예산 (예: "협의 후 결정", "4,000,000원")
    p.start-recruitment-data    ← "· 등록일자 2026.07.01."
    span.skill-chip             ← 스킬 (여러 개)
    div.project-type-mark       ← "외주" or "기간제"
"""

import re
import time
import requests
from bs4 import BeautifulSoup

from common import HEADERS

BASE_URL = "https://www.wishket.com/project/"
MAX_PAGES = 5  # 최대 수집 페이지 수


def _parse_date(raw: str) -> str:
    """'· 등록일자 2026.07.01.' → '2026-07-01'"""
    m = re.search(r"(\d{4})\.(\d{2})\.(\d{2})", raw)
    if m:
        return f"{m.group(1)}-{m.group(2)}-{m.group(3)}"
    return ""


def _parse_cards(soup) -> list:
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

            # 스킬
            skill_els = card.select("span.skill-chip")
            tags = [s.get_text(strip=True) for s in skill_els if s.get_text(strip=True)]

            # 프로젝트 유형 (외주 / 기간제)
            type_el = card.select_one("div.project-type-mark")
            if type_el:
                type_text = type_el.get_text(strip=True)
                if type_text and type_text not in tags:
                    tags.insert(0, type_text)

            # 근무형태 판별
            type_text_lower = type_el.get_text(strip=True).lower() if type_el else ""
            if "상주" in type_text_lower:
                work_type = "상주"
            else:
                work_type = "원격"   # 위시켓 외주는 대부분 원격

            items.append({
                "source": "위시켓",
                "title": title,
                "url": url,
                "budget": budget,
                "posted_at": posted_at,
                "work_type": work_type,
                "tags": tags[:8],
            })
        except Exception as e:
            print(f"[wishket] parse error: {e}")
            continue

    return items


def fetch():
    all_items = []

    for page in range(1, MAX_PAGES + 1):
        params = {"page": page}
        try:
            res = requests.get(
                BASE_URL,
                params=params,
                headers={
                    **HEADERS,
                    "Referer": "https://www.wishket.com/",
                    "Accept": "text/html,application/xhtml+xml",
                },
                timeout=15,
            )
            res.raise_for_status()
        except Exception as e:
            print(f"[wishket] page {page} fetch failed: {e}")
            break

        soup = BeautifulSoup(res.text, "html.parser")
        items = _parse_cards(soup)
        print(f"[wishket] page {page} → {len(items)}건")

        if not items:
            # 더 이상 공고 없으면 종료
            break

        all_items.extend(items)
        time.sleep(0.8)  # 서버 부담 방지

    return all_items


if __name__ == "__main__":
    result = fetch()
    print(f"\n[wishket] 총 {len(result)}건 수집")
    for r in result[:5]:
        print(r)
