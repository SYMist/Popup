# Chat Log

- 채팅/작업 로그 누적 기록. 최신 항목이 위에 오도록 유지.
- 파일명은 `Chat-Log.md`로 고정.

## 2025-09-22

- 정적 웹페이지(뷰어) 1차 구현 및 상세 페이지 전환(SEO)
  - 인덱스 빌더 추가: `scripts/build_index.py` → `data/index.json` 또는 자동 월별 샤딩(`index-YYYY-MM.json`), `index-manifest.json` 생성.
  - 웹 뷰어 스캐폴드: `web/index.html`, `web/app.js`, `web/styles.css` — 리스트/필터(팝업/도시/카테고리/상태)/정렬/검색 동작.
  - 카드 클릭 시 모달 대신 정적 상세 페이지로 이동: `web/p/{id}.html`.
  - 정적 상세 페이지 생성기: `scripts/build_pages.py` — 제목/기간/주소/갤러리/원문/지도/가격정규화/판정근거/JSON-LD/OG 태그 포함.
  - 데이터 경로 호환성: `app.js`가 `web/data` → 실패 시 `../data` 순서로 로드, 캐시 버스팅 쿼리(`?v=timestamp`) 적용.
- 크롤링 변경 요약 수치 개선
  - 매 실행마다 변하던 `meta.fetchedAt`로 인해 전체 파일이 Modified로 잡히던 문제 완화.
  - `scripts/storage.py`가 저장 전 기존 파일과 신규 레코드를 비교할 때 `meta.fetchedAt`을 무시하여 의미 변화 없으면 쓰기 생략.
- 워크플로/배포
  - GitHub Actions 워크플로에 웹 빌드/배포 통합: `web/data/index.json` 생성 및 `web/p/*.html` 출력 후 Pages 아티팩트 업로드, 별도 `deploy` 잡에서 `configure-pages` + `deploy-pages`로 Pages 배포.
  - 저장소 Settings → Pages의 Source “GitHub Actions” 설정 완료. 수동 실행으로 배포 성공.
  - Live: https://symist.github.io/Popup/
  - 커스텀 도메인 연결: `popup.deluxo.co.kr` 적용, Cloudflare DNS only(CNAME → symist.github.io), `web/CNAME` 고정.
  - ads.txt 배포: `/ads.txt` 200 확인(워크플로 재배포).
  - 운영 이슈: 커스텀 도메인 환경에서 뷰어가 인덱스(JSON) 로딩 실패 사례 확인 → 원인 분류(경로/배포 누락/샤딩/필터). TODO에 진단 체크리스트 추가.
- 로컬 검증
  - `python -m http.server`로 루트 서빙 시 `web/`에서 리스트/상세 정상 표시 확인.
  - `web/`만 서빙 시에도 `web/data`에 인덱스 생성하면 정상 로드.

## 2025-09-20

- 분류/규칙 보정 및 휴리스틱 강화
  - 카테고리 Allowlist 정규화: `POP-UP/POP UP/POPUP_EVENT/POPUP_STORE` 등을 토큰화해 매칭(`PopupRules._normalize_category`).
  - 크롤 결과에 `isPopup` 태깅과 `meta.detection` 기록(원본 category 포함).
  - 키워드 확장(ko/en/ja) + 기간 휴리스틱 결합: `classify()`로 `category` 또는 `(keyword AND duration≤90일)`일 때 팝업 판정. `keywordHits`, `durationDays`, `rule` 저장.
  - 규칙/임계값 외부화: `config/rules.json` 도입, `load_rules()`로 런타임 로드.
- 수집/성능 개선
  - HTTP 캐시(ETag/Last-Modified): `scripts/http_cache.py` 추가, 상세 요청에 조건부 헤더 적용, 304 시 파싱 스킵. 캐시 DB: `data/http_cache.sqlite`.
  - 재시도 하드닝: 백오프+풀 지터, 429/503 `Retry-After` 존중. 설정 `config/crawl.json`(attempts/initial/max/multiplier/jitter/timeout).
  - 실패 수집/재시도/리포트: 1차 실패를 모아 2차 재시도 및 `data/crawl_report.json` 생성.
  - 버그픽스: `crawl_popups.py`의 `__main__` 블록을 헬퍼 정의 아래로 이동해 `_parse_date` `NameError` 해결.
- 데이터/출력 고도화
  - 이미지 메타: `meta.images = { selectionRule, representativeRole, total, gallery }` 기록.
  - 가격 정규화: `pricing.normalized = { currency, amountMin, amountMax }` 추출.
  - README 동기화: 인터파크 경로/로케일 우선순위/CLI 옵션/직접 커밋/메타 예시 반영.
  - TODO의 데이터/출력 항목 체크 완료.
- 품질보증
  - JSON 스키마(`config/record.schema.json`)와 검증기(`scripts/validators.py`) 추가, 결과를 `meta.validation.errors/warnings`에 첨부(차단하지 않음).
  - 파서/검증 단위 테스트(pytest): `tests/test_triple_parser.py`, `tests/test_validators.py` 추가. `requirements.txt`에 `jsonschema`, `pytest` 추가.
- 실행/결과
  - 로컬(Python 3.11) 실행: `--limit 100 --fast --workers 8 --qps 2.0`으로 테스트.
  - 결과: `Saved: 100, Skipped: 0, Failures: 2` → 재시도 `Retry saved additionally: 1` 확인.
  - 데이터 커밋: `data/**/*.json` + `data/crawl_report.json` 반영.
- 저장소/운영
  - `.gitignore`에 `data/http_cache.sqlite` 및 `data/*.sqlite` 무시 규칙 추가.
  - 정적 웹페이지(뷰어) TODO 섹션 추가(인덱스 빌더/웹 UI/배포 체크리스트).

## 2025-09-18

- Actions push 실패 원인 해결 및 워크플로 안정화
  - `actions/checkout`에 `fetch-depth: 0` 추가로 전체 히스토리 확보
  - 크롤 이후 `git pull --rebase --autostash origin main` 단계 추가로 분기 정리
  - `git-auto-commit-action`에 `push_options: --force-with-lease` 설정(안전 강제 푸시)
  - 동시 실행 방지: `concurrency.cancel-in-progress: true`로 변경
- 크롤 성능 개선(1h30m → 단축 목표)
  - `scripts/crawl_popups.py`에 병렬 처리 도입(ThreadPoolExecutor)
  - 전역 QPS 기반 RateLimiter 추가, 사이트맵/상세요청에 적용
  - 빠른 모드(`--fast`): 최초 성공한 로케일에서 멈춰 불필요 요청 축소
  - CLI 옵션 추가: `--limit`, `--fast`, `--workers`, `--qps`, `--langs`
  - 워크플로 크롤 명령을 `--fast --workers 8 --qps 2.0`로 변경
- 파서/클라이언트 조정
  - `fetch_festa_by_lang(session, festa_id, lang, limiter=None)` 형태로 변경 및 내부 슬립 제거
  - 크롤러에서 limiter 전달로 예의있는 레이트 제어 유지
 - 워크플로 결과 요약
   - Job Summary에 JSON 변경 개수(Added/Modified/Deleted) 출력 단계 추가

## 2025-09-17

- 어제 최초 크롤링 성공 확인. 전체 워크플로 수행에 1시간 37분 소요 — 수집 파이프라인 성능 개선 필요.
- 대응: TODO의 "수집/성능 개선" 항목에 반영(증분 수집 강화, 레이트리밋/재시도 하드닝, 실패 URL 재시도 리포트).
- 초기 설정 진행: Actions 권한 확인 완료(워크플로 `permissions: { contents: write, pull-requests: write }` 명시). 생성된 PR 여부 점검 결과, 최근 실행에서 변경 사항이 없어 PR 미생성.
- 운영 단순화: PR/자동 머지 제거하고 `stefanzweifel/git-auto-commit-action`으로 `data/**/*.json`을 `main`에 직접 커밋하도록 워크플로 수정.
- 크롤러 도메인/라우트 수정: 상세 페이지를 `triple.global` → `interparkglobal.com/{lang}/festas/{id}`로 전환.
- 데이터 파싱 보강: Next.js `pageProps.__APOLLO_CACHE__` 지원(기존 `apolloState` 대비 변경 대응).
- 언어 확장/우선순위: `zh-cn`, `en`, `ja`, `ko` 순으로 시도(ko는 다수 404).
- 필터 제거: 카테고리/키워드/기간 규칙 미적용 → 언어 중 하나라도 성공하면 저장.
- 이미지 추출 개선: `sizes.full/small_square` 등 중첩 구조 지원으로 대표/썸네일 이미지 확보.
- 주소 병합 개선: 비어있는 필드는 다음 로케일 값으로 보완해 최상위 `address` 채움.
- 로컬 테스트: 샘플 5건 저장 성공(`data/popups/*.json`, `data/popups.sqlite` 생성). 이미지/주소 필드 확인 완료.
- 전체 크롤 실행: GitHub Actions 수동 트리거로 전체 크롤 시작(RUN #17802191161). 완료 시 변경 사항이 있으면 `main`에 자동 커밋.

## 2025-09-16

### Session Summary
- 초기 git 저장소 생성, 원격(origin) 추가, `main` 푸시.
- README에서 "Triple" 명칭 제거 및 커밋/푸시.
- GitHub Actions 워크플로(`crawl-popups.yml`)의 `workflow_dispatch` 트리거 및 YAML 파싱 오류 수정.
- `scripts/crawl_popups.py`에서 `sys.path` 보정으로 모듈 임포트 오류 해결.
- Actions 워크플로 수동 실행과 결과(1h37m, 저장된 팝업 0개) 확인, TODO 체크리스트 갱신.
- 대화 저장 요청으로 이 로그 파일 생성, `.gitignore`에 제외 규칙 추가.

### 대화 메모
- 사용자가 새 GitHub 레포(`SYMist/Popup`) 생성, 프로젝트 전체 초기 커밋 및 푸시 요청.
- Actions 탭에서 `Run workflow` 버튼이 보이지 않는 문제 → 권한/버튼 위치 안내.
- `workflow_dispatch` 트리거 인식 422 오류 → YAML 수정(`workflow_dispatch: {}`) 및 문자열 따옴표 처리.
- `gh workflow run` 실행 후 `ModuleNotFoundError: No module named 'scripts'` → `sys.path` 보정으로 해결.
- 워크플로가 1시간 37분 소요, `Saved: 0` 로그 확인, 규칙 튜닝 필요성 공유 (추후 작업 예정).
- TODO 초기 설정 항목 중 수동 실행 완료 체크, Actions 권한/결과 검토는 보류.
- 대화 기록은 자동 저장되지 않아 수동으로 파일로 남김(현재 파일).
