# 외주 프로젝트 모아보기

위시켓, 크몽엔터프라이즈, 원티드긱스, 나라장터의 프로젝트/입찰 공고를
크롤링해서 하나의 페이지에서 모아 볼 수 있게 하는 정적 사이트입니다.
GitHub Pages로 호스팅되고, GitHub Actions가 매일 자동으로 데이터를 갱신합니다.

## 구조

```
.
├── index.html              # 메인 페이지
├── assets/
│   ├── style.css
│   └── app.js               # data/projects.json을 읽어 카드로 렌더링
├── data/
│   └── projects.json        # 크롤링 결과 (Actions가 자동 갱신)
├── scraper/
│   ├── common.py
│   ├── wishket.py
│   ├── kmong.py
│   ├── wanted_gigs.py
│   ├── g2b.py                # 나라장터는 공공데이터포털 Open API 사용
│   └── main.py                # 전체 실행 + 결과 병합
├── requirements.txt
└── .github/workflows/crawl.yml
```

## 1. 로컬에서 먼저 확인하기

```bash
pip install -r requirements.txt
python scraper/main.py
```

`data/projects.json`이 갱신되면 `index.html`을 브라우저로 열어
(또는 `python -m http.server` 로 로컬 서버를 띄워) 확인합니다.

> 주의: 현재 셀렉터는 각 사이트의 대략적인 구조를 가정한 예시입니다.
> 실제 사이트를 브라우저 개발자도구로 열어 카드 목록의 class명을
> 확인한 뒤 `scraper/wishket.py`, `scraper/kmong.py`, `scraper/wanted_gigs.py`의
> `soup.select(...)` 부분을 실제 구조에 맞게 수정해야 정상적으로 데이터가 모입니다.
> 특히 원티드긱스처럼 React/SPA 기반 사이트는 단순 HTML 파싱으로는
> 데이터가 비어있을 수 있어, 브라우저 Network 탭에서 호출되는 내부 JSON API를
> 찾아 직접 호출하는 방식으로 바꾸는 것이 더 안정적입니다.

## 2. 나라장터 API 키 발급

1. https://www.data.go.kr 가입
2. "나라장터 입찰공고정보서비스" 검색 → 활용신청
3. 승인 후 발급되는 서비스키를 GitHub 저장소 Settings → Secrets and variables →
   Actions → New repository secret 에 이름 `G2B_API_KEY` 로 등록

## 3. GitHub Pages 배포

1. 이 폴더 전체를 GitHub 저장소에 push
2. 저장소 Settings → Pages → Source를 "GitHub Actions"로 설정
3. `.github/workflows/crawl.yml`이 main 브랜치 push / 매일 정해진 시간에
   자동으로 크롤링 → `data/projects.json` 커밋 → Pages 배포까지 수행

## 4. 주의사항

- 각 사이트(위시켓/크몽/원티드/나라장터)의 이용약관 및 robots.txt를
  확인하고, 과도한 요청으로 부담을 주지 않도록 요청 간 딜레이를 두거나
  허용된 범위 내에서만 수집하는 것을 권장합니다.
- 사이트 구조 변경 시 셀렉터가 깨질 수 있으므로, Actions 실행 로그를
  주기적으로 확인하는 것이 좋습니다.
- 가능하다면 각 사이트가 공식 API(개발자센터, 오픈API 등)를 제공하는지
  먼저 확인하고, 있다면 HTML 크롤링보다 API 사용을 우선하는 것이
  더 안정적이고 약관 위반 위험도 적습니다.
