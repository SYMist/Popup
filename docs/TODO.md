# TODO

## 초기 설정
- [x] GitHub 레포 생성
- [x] 현재 프로젝트 파일 푸시
- [x] Actions 권한 확인(`contents: write`, `pull-requests: write`) — 워크플로 파일에 명시 확인
- [x] 워크플로 수동 실행으로 첫 크롤 수행
- [x] 생성된 PR/JSON 변경사항 확인 및 머지 → 단순화: PR 제거, `main`에 직접 커밋으로 전환
- [x] 자동 머지 설정 → 불필요로 제거(단일 운영: 직접 커밋)

## 분류/규칙 개선
- [x] 팝업 Allowlist 카테고리 보정
- [x] 제목 키워드/기간 휴리스틱 튜닝(오탐/누락 샘플 반영)
- [x] 규칙/제한값을 설정 파일로 외부화(`config/`)

## 수집/성능 개선
- [x] ETag/Last-Modified 캐싱으로 증분 수집 강화
- [x] 레이트리밋/재시도 파라미터 하드닝(지수 백오프, 지터)
- [x] 오류/실패 URL 재시도 큐 정리 및 리포트

## 데이터/출력 고도화
- [x] PR 요약 메트릭(신규/변경/삭제 개수) 본문에 추가
- [x] 이미지 선택 로직 로그/메타 추가(대표/갤러리 근거)
- [x] 가격 문구 정규화(금액/통화 추출, 후순위)

## 품질보증
- [x] 기본 파서 단위 테스트(Next 데이터/아폴로 캐시 샘플)
- [x] JSON 스키마 검증(필수 필드 누락 감지)
- [x] 좌표/기간/링크 유효성 검사 강화

## 정적 웹페이지(뷰어) 구성
- [x] 인덱스 빌더 추가(`scripts/build_index.py`) — `data/popups/*.json`에서 요약 `data/index.json` 생성
  - [x] 필드 구성: `id,title,start,end,city,lat,lon,category,isPopup,thumb,sourceUrl`
  - [x] 타이틀 로케일 우선순위(fallback): `ko → en → ja → zh-cn`
  - [x] 썸네일(대표) 선택: `meta.images.selectionRule`/첫 이미지 기반
  - [x] 용량 관리: 필요 필드만 포함, 5MB 이하 목표(필요 시 월별 샤딩)
- [x] 정적 뷰어 스캐폴드(`web/`) — `index.html`, `app.js`, `styles.css`
  - [x] 리스트 카드 UI(대표 이미지/제목/기간/도시/카테고리)
  - [x] 상세 모달(갤러리/링크/가격 정규화/감지 근거 표시)
  - [x] 카드 클릭 시 상세 페이지로 이동(SEO)
  - [x] 정적 상세 페이지 생성 스크립트(`scripts/build_pages.py`) 및 `web/p/*.html` 출력
  - [x] 필터: `isPopup` 기본 on, 도시/카테고리, 진행상태(진행중/예정/종료)
  - [x] 정렬: 종료일 오름차순 기본, 옵션 제공
  - [x] 검색: 제목 텍스트 포함 검색
- [x] 퍼포먼스
  - [x] 인덱스 분할(연-월 단위 `index-YYYY-MM.json`) 및 지연 로딩
  - [x] 캐시 버스팅(쿼리스트링에 `?v=timestamp`)
- [ ] 배포( GitHub Pages )
  - [x] Actions 단계 추가: 크롤 후 인덱스/상세 페이지 빌드 → `web/` 아티팩트 업로드 + `deploy-pages`로 배포
  - [x] 배포 성공 및 페이지 동작 확인(리스트/상세)
  - [x] 사용자 도메인/CNAME(선택)
- [ ] 품질/접근성
  - [x] 스키마/인덱스 필드 검증 스크립트(누락/형식)
  - [x] 반응형 레이아웃/키보드 내비게이션/대체텍스트

## 도메인/수익화
- [x] 커스텀 도메인 연결(`popup.deluxo.co.kr`) 및 `web/CNAME` 고정
- [x] AdSense `ads.txt` 공개(`web/ads.txt` → `/ads.txt`)
- [x] AdSense Auto ads 스니펫 주입(`web/index.html`, `scripts/build_pages.py`)
- [x] Privacy Policy 페이지 추가(`web/privacy.html`) 및 푸터 링크
- [ ] robots.txt/sitemap 생성 및 Pages 배포 포함

## 배포 이슈(데이터 로딩)
- [x] Pages에서 인덱스 확인: `https://popup.deluxo.co.kr/data/index.json` 200 응답/콘텐츠 확인
- [x] 매니페스트 확인(샤딩 시): `https://popup.deluxo.co.kr/data/index-manifest.json` 존재 및 months 목록 검증
- [x] 워크플로 점검: "Build web index and pages" 단계가 `web/data/index.json` 생성 및 Pages 아티팩트 포함하는지 확인
- [x] 뷰어 경로/에러 보강
  - [x] `web/app.js`에 절대 경로(`/data`) 추가
  - [x] 오류 메시지 강화(로딩 스피너/네트워크 에러 출력)
- [x] 임시 확인: `isPopup` 필터 off 상태에서 리스트가 보이는지 점검(데이터 측면 문제 배제)
- [x] 네트워크 검사: DevTools Network에서 `/data/*.json` 응답 코드/크기/콘텐츠타입 확인
- [ ] 필요 시 수동 빌드: `python scripts/build_index.py --output web/data/index.json` 후 커밋/재배포

- [ ] 워크플로 실행 후 확인(월별 샤딩/지연 로딩)
  - [x] Actions 실행: GitHub → Actions → "Crawl Triple Popups" → Run workflow(main) → `crawl`/`deploy` 두 잡 모두 성공
  - [x] Logs 확인: "Build web index and pages" 단계에 `Index build complete: mode=monthly` 출력, Deploy 단계에서 Pages URL 표시
  - [x] 매니페스트: `https://popup.deluxo.co.kr/data/index-manifest.json` 200 OK, JSON에 `{ mode: "monthly", months: [...] }` 포함(길이>0)
  - [x] 단일 인덱스(플레이스홀더): `https://popup.deluxo.co.kr/data/index.json`가 `[]` (monthly 모드일 때)
  - [x] 뷰어 초기 로딩: 스피너 → 리스트 표시, 상단 메타에 `· 로드된개월/전체개월` 표기
  - [x] 네트워크(초기): DevTools Network에 `index-YYYY-MM.json` 요청이 최신 3개월만 발생(INITIAL=3)
  - [x] 더 보기: "이전 월 더 보기" 클릭 시 3개월씩 추가 로드(BATCH=3), 버튼 문구/표시 상태가 남은 개월 수에 맞게 갱신, 모두 로드되면 버튼 숨김
  - [x] 필터/검색: `isPopup` off로 전환 시 리스트 표시, 도시/카테고리/상태/정렬/검색 동작 정상
  - [x] 상세 페이지: 카드 클릭 → `web/p/{id}.html` 렌더 정상
  - [x] unknown 처리: 매니페스트에 `unknown` 있으면 마지막에 로드됨 확인(`index-unknown.json` 요청)
  - [x] 에러 UI: 정상이면 에러 배너 노출 없음, 콘솔 에러 없음

## 운영 메모
- 요약 수치(Modified 과다) 완화: `scripts/storage.py` 저장 시 `meta.fetchedAt` 무시 비교 도입 → 의미 없는 파일 재저장 방지.
- 배포/도메인: Pages 배포 성공, 커스텀 도메인 연결 완료. HTTPS 인증서는 발급 진행 중(접속은 정상).
- 수익화: `/ads.txt` 노출 및 Auto ads 삽입 완료.

## 내일 작업(자동화: vibe-kanban)
- [x] 인덱스페이지에 '테스트' 버튼 추가
- [x] 인덱스페이지에 추가된 '테스트' 버튼 제거
- [x] 카드 → 브랜치/PR 자동화 설계(네이밍 규칙 `vk/{cardId}-{slug}`)
- [x] PR 템플릿/체크리스트: TODO 반영 항목 자동 포함
- [x] 워크플로: 카드 상태 Done 시 `docs/TODO.md` 체크 및 `docs/Chat-Log.md` 업데이트 자동 커밋
- [x] 인덱스페이지에 '테스트' 버튼 제거
- [ ] 워크플로: PR 머지 후 Pages 배포 완료 여부 확인하고 결과 코멘트/서머리 남기기
- [ ] 권한/보안: GitHub App/PAT 최소 권한 구성, 보호 브랜치 정책 점검
- [ ] 로그/리포트: 실행 결과를 Actions Summary와 PR 코멘트로 보고
