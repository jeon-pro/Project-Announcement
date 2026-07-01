"""
원티드긱스(wanted.co.kr/gigs 또는 별도 도메인) 프로젝트 의뢰 목록 크롤러.

주의:
- 원티드긱스는 SPA(React 등) 기반으로 동작할 가능성이 높아 단순 requests로는
  빈 페이지만 받아질 수 있다. 이 경우 내부 API(JSON)를 호출하거나
  Playwright/Selenium 같은 헤드리스 브라우저 사용을 고려해야 한다.
- 아래는 1차로 정적 파싱을 시도하고, 실패 시 사용할 수 있는 골격만 제공한다.
"""

import requests
from bs4 import BeautifulSoup

from common import HEADERS

LIST_URL = "https://www.wanted.co.kr/gigs"


def fetch():
    items = []
    try:
        res = requests.get(LIST_URL, headers=HEADERS, timeout=15)
        res.raise_for_status()
    except Exception as e:
        print(f"[wanted_gigs] fetch failed: {e}")
        return items

    soup = BeautifulSoup(res.text, "html.parser")

    # TODO: SPA라면 아래 셀렉터로는 비어 있을 수 있음.
    # 그 경우 브라우저 Network 탭에서 호출되는 JSON API 엔드포인트를 찾아
    # requests.get(api_url, headers=HEADERS).json() 형태로 교체할 것.
    cards = soup.select("a.gig-card, li.gig-item")

    for card in cards:
        try:
            title_el = card.select_one(".title")
            budget_el = card.select_one(".budget, .price")

            href = card.get("href", "")
            if not title_el or not href:
                continue

            url = href if href.startswith("http") else f"https://www.wanted.co.kr{href}"

            items.append(
                {
                    "source": "원티드긱스",
                    "title": title_el.get_text(strip=True),
                    "url": url,
                    "budget": budget_el.get_text(strip=True) if budget_el else "",
                    "posted_at": "",
                    "tags": [],
                }
            )
        except Exception as e:
            print(f"[wanted_gigs] parse error: {e}")
            continue

    return items


if __name__ == "__main__":
    result = fetch()
    print(f"[wanted_gigs] {len(result)} items")
    for r in result[:5]:
        print(r)
