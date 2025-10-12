# Chat Log

- 채팅/작업 로그 누적 기록. 최신 항목이 위에 오도록 유지.
- 파일명은 `Chat-Log.md`로 고정.

## 2025-10-12

- VK Done: vk/4dc7-feat-web-add-tes merged via PR #9: VK: 4dc7-feat-web-add-tes
  - https://github.com/SYMist/Popup/pull/9

## 2025-10-10

- 자동화/워크플로
  - `vibe-kanban.yml` 보강: `vk/*` 브랜치 push/create/수동 실행(workflow_dispatch) 시 PR 자동 생성/갱신 보장.
  - PR 본문 보강 유지: VK Context + TODO 체크리스트 주입.
- 프리뷰/배포 안전장치
  - PR 프리뷰 Pages 배포 기본 비활성화. 레포 변수 `VK_PREVIEW=1`일 때만 프리뷰 배포 수행.
  - 비활성화 시 Summary와 PR 본문에 “Local Preview (artifact 다운로드 → 로컬 서버)” 안내 자동 삽입.
  - 이전 테스트에서 PR 프리뷰가 실서비스를 덮은 이슈 재발 방지.
- 자동 푸시(브랜치)
  - `.githooks/post-commit` 추가: `vk/*` 브랜치에서 커밋 시 자동 `git push`(upstream 없으면 `-u origin <branch>`).
  - `core.hooksPath`를 `.githooks`로 설정. 일부 툴이 post-commit을 우회할 수 있어, post-checkout 훅/로깅 보강은 추후 검토.
- 운영
  - 실서비스의 테스트 버튼 노출 건 해결: “Crawl Triple Popups” 워크플로(main) 수동 실행 → main 기준으로 Pages 재배포 완료.
  - 테스트용 `vk/*` 로컬/원격 브랜치 및 worktree 정리(현재 main만 유지).
- 다음 작업 제안
  - post-checkout 훅(브랜치 생성 직후 1회 push) 및 훅 로깅 강화.
  - (선택) main만 재배포하는 경량 워크플로 추가.

## 2025-09-30

- 동기화/검증
  - `git pull --rebase --autostash`로 원격과 동기화. 커밋 `93a7437 docs: check off privacy policy` 반영 확인.
  - Privacy Policy 페이지 추가 확인: `web/privacy.html` 존재, 인덱스 푸터(`web/index.html`)와 상세 페이지 템플릿(`scripts/build_pages.py`)에 링크 포함.
  - TODO 갱신 확인: `docs/TODO.md`에서 Privacy Policy 항목 체크 처리.
- 내일 작업(예정): vibe‑kanban 기반 자동화 프로세스 설계/구현
  - 카드 → 브랜치/PR 자동화(네이밍 `vk/{cardId}-{slug}`), PR 템플릿에 TODO 체크리스트 포함.
  - 카드 상태 Done 시 TODO 체크/Chat-Log 자동 갱신 커밋 워크플로.
  - PR 머지 후 Pages 배포 확인 및 결과 서머리/코멘트 남기기.
  - 권한 최소화 및 보호 브랜치 정책 점검, 실행 로그/리포트 정리.

## 2025-09-29

- 웹 뷰어 로딩/에러 UX 강화 및 성능 개선
  - 로딩 스피너/네트워크 에러 배너 추가: `web/index.html` 마크업, `web/styles.css` 스타일, `web/app.js` 토글/메시지 처리.
  - 월별 샤딩 + 지연 로딩: 매니페스트(`index-manifest.json`) 모드에서 초기 3개월만 로드, "이전 월 더 보기"로 3개월씩 추가.
  - `unknown` 샤드 마지막 로드, 상단 메타에 `로드된 개월/전체 개월` 표기.
  - 워크플로 인덱스 빌드에 `--shard monthly` 적용: `.github/workflows/crawl-popups.yml` 수정.
- 접근성/반응형 개선
  - 스킵 링크, 포커스 링, 리스트/아이템 역할(role), 대체텍스트/aria 라벨, 모바일 필터 토글(접힘/펼침) 도입.
  - 카드에 제목 링크 추가, 퀵뷰 버튼에 `aria-haspopup="dialog"` 지정.
- 상세 모달(퀵뷰) 추가
  - 카드의 “퀵뷰”로 `web/p/{id}.html`을 iframe으로 미리보기, ESC/배경/버튼으로 닫기, 포커스 복귀.
- 인덱스 검증 품질 스크립트 추가
  - `config/index.schema.json` 스키마와 `scripts/validate_index.py` 도입. monthly/single 모두 검증 지원.
- TODO 갱신 및 검증
  - 퍼포먼스(샤딩+지연 로딩), 에러 UI, 정적 뷰어 스캐폴드/상세 모달, 접근성/검증 스크립트 항목 체크 완료.
  - 사용자 검증: 워크플로 실행 결과 `mode=monthly`, manifest 200 OK, 초기 3개월만 네트워크 요청, 더 보기 동작, 필터/검색/상세 정상. 마지막 2개(unknown 처리/에러 UI)도 확인 완료.
- 커밋/푸시
  - viewer(web): loading spinner & error UI; monthly sharding + lazy loading
  - a11y+responsive: skip link, focus rings, title links, alt/aria labels, mobile filter toggle; role=list/listitem
  - quality: add index schema and validator script
  - workflow: force monthly shard in index build
  - docs: update TODO checklist / post-deploy checks

## 2025-09-27

- 뷰어 경로 보강/버그 수정 및 배포 확인
  - `web/app.js`에 절대 경로 `'/data'` 추가, 데이터 필터 옵션 초기화 시 `rows` → `DATA`로 참조 수정.
  - 커밋/푸시: "viewer: add /data base and fix filter option init" (5bc6562) 반영. 사용자가 워크플로 수동 실행하여 Pages 배포 완료.
  - 라이브 검증: `https://popup.deluxo.co.kr/app.js`에서 `const bases = ['/data', 'data', '../data'];`와 `uniqSorted(DATA.map(...))` 확인. `https://popup.deluxo.co.kr/data/index.json` 200 OK.
  - 결과: https://popup.deluxo.co.kr 접속 시 리스트/필터 정상 동작.
- TODO 갱신
  - "Pages에서 인덱스 확인" 및 "워크플로 점검(웹 데이터 포함 배포)" 완료 체크.
  - "뷰어 경로/에러 보강" 세분화: 절대 경로 추가 완료, 로딩 스피너/네트워크 에러 UI는 미완.
- 다음 작업 제안(우선순위)
  - 로딩 스피너 + 네트워크 에러 UI 추가.
  - 인덱스 월별 샤딩 + 지연 로딩.
  - Privacy Policy, robots.txt/sitemap 생성 및 배포.

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
