"""
원티드긱스(wanted.co.kr/gigs) 프로젝트 의뢰 목록 크롤러.

공식 JSON API를 직접 호출하는 방식으로 구현.
페이지네이션을 자동으로 처리해 전체 공고를 수집한다.

API 응답 주요 필드:
  id            - 공고 ID (상세 URL 조합에 사용)
  title         - 공고 제목
  salary        - {salary_type, start, end}  단위: 만원
  text_salary_type - "월급" / "프로젝트 전체" 등
  text_term_type   - "개월" / "주" 등
  term          - {start, end}  기간
  work_place_txt   - "상주" / "원격" / "원격/상주"
  skills        - 스킬 콤마 문자열
  startAt       - 시작 예정일 (YYYY-MM-DD)
  jobs          - 직군 문자열
"""

import time
import requests
from common import HEADERS

BASE_API = "https://www.wanted.co.kr/gigs/api-v2/projects"
DETAIL_BASE = "https://www.wanted.co.kr/gigs/projects"

PARAMS = {
    "work_type_office": "true",
    "work_type_remote": "true",
    "sort": "createdAt",
    "is_recruiting": "true",
}

MAX_PAGES = 5  # 한 번에 최대 수집할 페이지 수 (전체는 count.pages로 확인)


def _format_budget(item):
    """salary 필드를 '300~500만원/월' 형식 문자열로 변환."""
    salary = item.get("salary") or {}
    s = salary.get("start")
    e = salary.get("end")
    salary_type = item.get("text_salary_type", "")

    if s and e:
        budget = f"{s}~{e}만원"
    elif s:
        budget = f"{s}만원~"
    else:
        return ""

    if salary_type:
        budget += f" / {salary_type}"
    return budget


def _format_term(item):
    """기간을 '6개월', '4주' 같은 문자열로 변환."""
    term = item.get("term") or {}
    start = term.get("start")
    unit = item.get("text_term_type", "")
    if start and unit:
        return f"{start}{unit}"
    return ""


def _parse_tags(item):
    """skills 문자열과 직군 정보를 합쳐 태그 목록 반환."""
    skills_raw = item.get("skills", "") or ""
    tags = [s.strip() for s in skills_raw.split(",") if s.strip()]

    # 직군(jobs) 정보를 jobsV2에서 가져오기
    for job in item.get("jobsV2") or []:
        cat = job.get("jobCategoryTitle", "")
        if cat and cat not in tags:
            tags.append(cat)

    return tags[:8]  # 최대 8개만


def fetch():
    items = []
    page = 1

    while page <= MAX_PAGES:
        params = {**PARAMS, "page": page}
        try:
            res = requests.get(
                BASE_API,
                params=params,
                headers={
                    **HEADERS,
                    "Referer": "https://www.wanted.co.kr/gigs",
                    "Accept": "application/json",
                },
                timeout=15,
            )
            res.raise_for_status()
            data = res.json()
        except Exception as e:
            print(f"[wanted_gigs] page {page} fetch failed: {e}")
            break

        if data.get("status") != "success":
            print(f"[wanted_gigs] API returned non-success: {data.get('status')}")
            break

        rows = data.get("rows") or []
        if not rows:
            break

        for row in rows:
            try:
                pid = row.get("id")
                title = (row.get("title") or "").strip()
                work_place = row.get("work_place_txt", "")
                term = _format_term(row)
                budget = _format_budget(row)
                tags = _parse_tags(row)
                start_at = row.get("startAt", "") or ""

                # 제목 앞에 근무형태 표시 (원래 titleDisplay에도 포함되어 있으나
                # 여기서는 깔끔하게 직접 조합)
                display_title = f"[{work_place}] {title}" if work_place else title
                if term:
                    display_title += f" ({term})"

                url = f"{DETAIL_BASE}/{pid}" if pid else "https://www.wanted.co.kr/gigs"

                items.append(
                    {
                        "source": "원티드긱스",
                        "title": display_title,
                        "url": url,
                        "budget": budget,
                        "posted_at": start_at,
                        "tags": tags,
                    }
                )
            except Exception as e:
                print(f"[wanted_gigs] parse error on item: {e}")
                continue

        # 마지막 페이지 확인
        count_info = data.get("count") or {}
        total_pages = count_info.get("pages", 1)
        print(f"[wanted_gigs] page {page}/{total_pages} → {len(rows)}건")

        if page >= total_pages:
            break

        page += 1
        time.sleep(0.5)  # 과도한 요청 방지

    return items


if __name__ == "__main__":
    result = fetch()
    print(f"\n[wanted_gigs] 총 {len(result)}건 수집")
    for r in result[:5]:
        print(r)
