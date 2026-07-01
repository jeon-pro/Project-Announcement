"""
위시켓(wishket.com) 프로젝트 의뢰 목록 크롤러.

주의:
- 위시켓은 목록을 JS로 렌더링하거나 내부 API를 호출할 수 있어, 실제 운영 전
  브라우저 개발자도구(Network 탭)로 실데이터를 호출하는 API 엔드포인트가
  있는지 먼저 확인하는 것을 권장한다. 있다면 requests로 그 API를 직접
  호출하는 편이 훨씬 안정적이다.
- 아래는 정적 HTML 파싱 기준의 예시 구현이며, 실제 클래스명/구조는
  사이트 개편에 따라 달라질 수 있으므로 셀렉터(CSS selector)를
  현재 사이트 구조에 맞게 점검/수정해야 한다.
"""

import requests
from bs4 import BeautifulSoup

from common import HEADERS

LIST_URL = "https://www.wishket.com/project/"


def fetch():
    items = []
    try:
        res = requests.get(LIST_URL, headers=HEADERS, timeout=15)
        res.raise_for_status()
    except Exception as e:
        print(f"[wishket] fetch failed: {e}")
        return items

    soup = BeautifulSoup(res.text, "html.parser")

    # TODO: 실제 카드 컨테이너 셀렉터로 교체 필요
    cards = soup.select("a.project-list-item, div.project-card")

    for card in cards:
        try:
            title_el = card.select_one(".title, .project-title")
            link_el = card if card.name == "a" else card.select_one("a")
            budget_el = card.select_one(".budget, .price")

            if not title_el or not link_el:
                continue

            href = link_el.get("href", "")
            url = href if href.startswith("http") else f"https://www.wishket.com{href}"

            items.append(
                {
                    "source": "위시켓",
                    "title": title_el.get_text(strip=True),
                    "url": url,
                    "budget": budget_el.get_text(strip=True) if budget_el else "",
                    "posted_at": "",
                    "tags": [],
                }
            )
        except Exception as e:
            print(f"[wishket] parse error: {e}")
            continue

    return items


if __name__ == "__main__":
    result = fetch()
    print(f"[wishket] {len(result)} items")
    for r in result[:5]:
        print(r)
