"""
크몽 엔터프라이즈(kmong.com/enterprise/requests) 프로젝트 의뢰 목록 크롤러.

API 응답 구조:
  total         - 전체 공고 수
  last_page     - 마지막 페이지
  next_page_link
  requests[]
    id            - 공고 ID → 상세 URL 조합에 사용
    title         - 공고 제목
    breadcrumb    - "IT·프로그래밍 / 웹사이트 개발"
    amount        - 금액 (원, 정수)
    project_type  - "OUTSOURCING"(외주) | "RESIDENT"(상주/기간제)
    days          - 진행 기간 (일)
    deadline      - 모집 마감까지 남은 일수
    proposal_count
    category
      cat1_name   - 대분류
      cat2_name   - 소분류
"""

import time
import requests

from common import HEADERS

API_URL     = "https://kmong.com/api/custom-project/v1/requests"
DETAIL_BASE = "https://kmong.com/enterprise/requests"
MAX_PAGES   = 5   # 한 번에 최대 수집 페이지 (1페이지 = 10건)


def _format_budget(item: dict) -> str:
    amount = item.get("amount")
    if not amount:
        return ""
    formatted = f"{amount:,}원"
    # 상주(기간제)는 월 단가, 외주는 총액
    if item.get("project_type") == "RESIDENT":
        formatted += "/월"
    return formatted


def _format_tags(item: dict) -> list:
    tags = []
    ptype = item.get("project_type", "")
    if ptype == "OUTSOURCING":
        tags.append("외주")
    elif ptype == "RESIDENT":
        tags.append("상주")

    cat = item.get("category") or {}
    cat1 = cat.get("cat1_name", "")
    cat2 = cat.get("cat2_name", "")
    if cat1:
        tags.append(cat1)
    if cat2 and cat2 != cat1:
        tags.append(cat2)

    days = item.get("days")
    if days:
        tags.append(f"{days}일")

    return tags[:6]


def fetch() -> list:
    items = []

    for page in range(1, MAX_PAGES + 1):
        params = {
            "q":                "",
            "sort":             "CREATED_AT",
            "category_list":    "",
            "sub_category_list":"",
            "project_type":     "",
            "page":             page,
            "per_page":         10,
        }
        try:
            res = requests.get(
                API_URL,
                params=params,
                headers={
                    **HEADERS,
                    "Referer": "https://kmong.com/enterprise/requests",
                    "Accept":  "application/json",
                },
                timeout=15,
            )
            res.raise_for_status()
            data = res.json()
        except Exception as e:
            print(f"[kmong] page {page} fetch failed: {e}")
            break

        rows = data.get("requests") or []
        if not rows:
            break

        last_page = data.get("last_page", 1)
        print(f"[kmong] page {page}/{last_page} → {len(rows)}건  (총 {data.get('total', '?')}건)")

        for row in rows:
            try:
                pid   = row.get("id", "")
                title = (row.get("title") or "").strip()
                url   = f"{DETAIL_BASE}/{pid}" if pid else "https://kmong.com/enterprise/requests"

                items.append({
                    "source":    "크몽엔터프라이즈",
                    "title":     title,
                    "url":       url,
                    "budget":    _format_budget(row),
                    "posted_at": "",
                    "tags":      _format_tags(row),
                })
            except Exception as e:
                print(f"[kmong] parse error: {e}")
                continue

        if page >= last_page:
            break

        time.sleep(0.5)

    return items


if __name__ == "__main__":
    result = fetch()
    print(f"\n[kmong] 총 {len(result)}건 수집")
    for r in result[:5]:
        print(r)