# Chat Log

- 채팅/작업 로그 누적 기록. 최신 항목이 위에 오도록 유지.
- 파일명은 `Chat-Log.md`로 고정.

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
