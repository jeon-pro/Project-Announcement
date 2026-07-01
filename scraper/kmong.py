"""
크몽 엔터프라이즈(kmong.com biz/enterprise 영역) 프로젝트 의뢰 목록 크롤러.

주의:
- 크몽엔터프라이즈는 로그인 후에만 전체 공고가 보이는 경우가 있다.
  비로그인 상태에서 접근 가능한 목록 페이지 URL을 먼저 확인해야 한다.
- 아래는 정적 파싱 예시이며, 실제 페이지 구조 확인 후 셀렉터 수정이 필요하다.
"""

import requests
from bs4 import BeautifulSoup

from common import HEADERS

LIST_URL = "https://kmong.com/enterprise/projects"


def fetch():
    items = []
    try:
        res = requests.get(LIST_URL, headers=HEADERS, timeout=15)
        res.raise_for_status()
    except Exception as e:
        print(f"[kmong] fetch failed: {e}")
        return items

    soup = BeautifulSoup(res.text, "html.parser")

    # TODO: 실제 카드 컨테이너 셀렉터로 교체 필요
    cards = soup.select("li.css-x6apz0 e1wbh2vn0")

    for card in cards:
        try:
            title_el = card.select_one(".title")
            budget_el = card.select_one(".budget, .price")
            date_el = card.select_one(".date, .posted")

            href = card.get("href", "")
            if not href:
                a = card.select_one("a")
                href = a.get("href", "") if a else ""

            if not title_el or not href:
                continue

            url = href if href.startswith("http") else f"https://kmong.com{href}"

            items.append(
                {
                    "source": "크몽엔터프라이즈",
                    "title": title_el.get_text(strip=True),
                    "url": url,
                    "budget": budget_el.get_text(strip=True) if budget_el else "",
                    "posted_at": date_el.get_text(strip=True) if date_el else "",
                    "tags": [],
                }
            )
        except Exception as e:
            print(f"[kmong] parse error: {e}")
            continue

    return items


if __name__ == "__main__":
    result = fetch()
    print(f"[kmong] {len(result)} items")
    for r in result[:5]:
        print(r)
