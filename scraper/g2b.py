"""
나라장터(g2b.go.kr) 입찰공고 수집.

나라장터는 직접 HTML 크롤링이 까다롭고(동적 렌더링, 캡차 등) 약관상으로도
권장되지 않는다. 대신 공공데이터포털에서 제공하는
"조달청_나라장터 입찰공고정보서비스" Open API를 사용하는 방식을 권장한다.

사전 준비:
1. https://www.data.go.kr 에서 "나라장터 입찰공고정보서비스" 검색 후
   활용신청을 하면 서비스키(인증키)를 발급받을 수 있다.
2. 발급받은 키를 환경변수 G2B_API_KEY 로 등록한다.
   (GitHub Actions를 쓴다면 Repository Settings > Secrets 에 등록)

여기서는 "용역" 분류 중 정보처리/소프트웨어 관련 입찰을 검색하는 예시이며,
실제 서비스명/엔드포인트/파라미터는 공공데이터포털 문서를 기준으로
한 번 더 확인이 필요하다 (오픈API 스펙은 갱신될 수 있음).
"""

import os
import xml.etree.ElementTree as ET
import datetime

import requests

API_KEY = os.environ.get("G2B_API_KEY", "")

# 예시 엔드포인트 (서비스용역 입찰공고 목록 조회) - 실제 사용 전 data.go.kr 문서에서
# 정확한 URL과 파라미터명을 다시 확인할 것.
BASE_URL = "http://apis.data.go.kr/1230000/ad/BidPublicInfoService/getBidPblancListInfoServcPPSSrch"

KEYWORDS = ["소프트웨어", "정보시스템", "홈페이지", "앱 개발", "데이터"]


def fetch():
    items = []

    if not API_KEY:
        print("[g2b] G2B_API_KEY 환경변수가 없어 나라장터 수집을 건너뜁니다.")
        return items

    today = datetime.date.today()
    start = (today - datetime.timedelta(days=14)).strftime("%Y%m%d")
    end = today.strftime("%Y%m%d")

    params = {
        "serviceKey": API_KEY,
        "pageNo": 1,
        "numOfRows": 100,
        "inqryDiv": 1,
        "inqryBgnDt": f"{start}0000",
        "inqryEndDt": f"{end}2359",
        "type": "xml",
    }

    try:
        res = requests.get(BASE_URL, params=params, timeout=20)
        res.raise_for_status()
    except Exception as e:
        print(f"[g2b] fetch failed: {e}")
        return items

    try:
        root = ET.fromstring(res.text)
    except ET.ParseError as e:
        print(f"[g2b] xml parse failed: {e}")
        return items

    for item in root.iter("item"):
        try:
            title = (item.findtext("bidNtceNm") or "").strip()
            if not title:
                continue
            # IT/소프트웨어 관련 키워드 필터링 (필요 없으면 제거)
            if KEYWORDS and not any(k in title for k in KEYWORDS):
                continue

            bid_no = item.findtext("bidNtceNo") or ""
            org = item.findtext("ntceInsttNm") or ""
            posted = item.findtext("bidNtceDt") or ""

            url = (
                f"https://www.g2b.go.kr/co/cnts/co/cnts2View.do?bidNo={bid_no}"
                if bid_no
                else "https://www.g2b.go.kr"
            )

            items.append(
                {
                    "source": "나라장터",
                    "title": f"[{org}] {title}" if org else title,
                    "url": url,
                    "budget": "",
                    "posted_at": _to_iso(posted),
                    "tags": ["공공입찰"],
                }
            )
        except Exception as e:
            print(f"[g2b] parse item error: {e}")
            continue

    return items


def _to_iso(raw):
    raw = (raw or "").strip()
    if len(raw) >= 8 and raw[:8].isdigit():
        return f"{raw[:4]}-{raw[4:6]}-{raw[6:8]}"
    return ""


if __name__ == "__main__":
    result = fetch()
    print(f"[g2b] {len(result)} items")
    for r in result[:5]:
        print(r)
