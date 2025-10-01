# Vibe‑Kanban 자동화 가이드

이 문서는 POPUP 레포에서 카드(티켓) 단위로 작업할 때 필요한 최소 절차와 자동화 동작을 간단히 설명합니다. 비개발자도 그대로 따라 할 수 있게 구성했습니다.

## 무엇이 자동으로 되나요
- `vk/*` 브랜치를 푸시하면 PR이 자동 생성되고 `vk` 라벨이 붙습니다.
- PR 본문에 브랜치/카드 정보와 TODO 체크리스트가 자동으로 들어갑니다.
- PR을 머지하면 `docs/Chat-Log.md`에 기록이 추가되고, PR 본문에서 체크한 TODO 항목이 `docs/TODO.md`에 자동 반영됩니다.
- PR 프리뷰 배포는 기본 비활성화이며, 로컬 확인을 기본으로 합니다(원할 때만 `VK_PREVIEW=1`로 활성화).

## 사전 준비(중요)
- GitHub/Vibe‑kanban 로그인 계정: 작업용 계정으로 로그인하세요. 현재는 `mmist0226@gmail.com` 사용 권장.
- GitHub Actions 권한: 레포 Settings → Actions → Workflow permissions = “Read and write”.
- PR/브랜치 생성은 “로컬에서 푸시” 방식 권장(일부 환경에서 OAuth ‘Create PR’ 버튼은 권한 문제로 실패할 수 있음).
- 선택(카드 링크 자동화): 레포 Actions Variables에 `VK_CARD_URL_FORMAT` = `https://your-vk.app/cards/{id}` 추가 시 PR 본문에 카드 링크 자동 생성.

## 빠른 시작(요약)
1) 터미널에서 브랜치 생성/푸시
   - `git checkout -b vk/{cardId}-{slug}`
   - `git push -u origin HEAD`
2) vibe‑kanban에서 티켓 열기 → “Link/Change branch”로 지금 브랜치 연결
3) 로컬에서 결과 확인(아래 절차 참고)
4) PR 본문 TODO 체크 표시 → 머지
5) 프로덕션 배포 확인(필요 시 Actions → “Crawl Triple Popups” 실행) → 카드 Done

## 전체 플로우(사용자/자동화 구분)
1 (사용자) vibe‑kanban에서 POPUP 저장소 선택
2 (사용자) 카드 생성: 제목/설명/완료 기준 작성
3 (사용자) 브랜치 생성: `vk/{cardId}-{slug}`
4 (사용자) 로컬 업데이트 후 작업 브랜치 체크아웃
5 (사용자) 구현/수정 진행, PR의 TODO 체크만 표시(문서 수기 체크 불필요)
6 (사용자) 커밋 생성(메시지 자유, 권장: 카드 ID 포함)
7 (사용자) 푸시: `git push -u origin HEAD`
8 (자동화) PR 자동 생성 및 ‘vk’ 라벨 부착
9 (자동화) PR 본문에 VK Context/TODO 체크리스트 자동 주입
10 (생략) PR 프리뷰는 기본 사용하지 않음(로컬 확인으로 대체)
11 (사용자) 로컬 확인 결과에 따라 커밋/푸시 반복
12 (사용자) PR 머지
13 (자동화) Chat-Log에 기록 추가 + `docs/TODO.md` 체크 동기화
14 (사용자) 프로덕션 배포 확인(필요 시 Actions → “Crawl Triple Popups” 수동 실행)
15 (사용자) 카드 상태 Done으로 이동

## 티켓 작성 가이드(간단)
- 제목: “feat(web): robots/sitemap + Pages deploy”처럼 짧고 명확하게 작성
- 본문(짧은 예시):
  - Goal: sitemap.xml/robots.txt 생성·배포
  - Verify: Pages에서 /sitemap.xml, /robots.txt 200 OK
  - Steps: 브랜치 푸시 → 로컬 확인 → 머지 → 배포 확인 → Done

## 브랜치/PR 다루기
- 브랜치 생성: `git checkout -b vk/{cardId}-{slug}`
- 브랜치 푸시: `git push -u origin HEAD` (→ 자동으로 PR 생성/라벨)
- 브랜치 연결: 티켓에서 “Link/Change branch”로 방금 푸시한 브랜치 선택

## 로컬 검증(기본)
- 데이터/페이지 생성:
  - `python3 scripts/build_index.py --output web/data/index.json --shard monthly`
  - `python3 scripts/build_pages.py --out-dir web/p --site-origin https://popup.deluxo.co.kr --sitemap-out web/sitemap.xml --robots-out web/robots.txt`
- 로컬 미리보기: `python3 -m http.server -d web 8080` → 브라우저 `http://localhost:8080`
  - 예: `http://localhost:8080/sitemap.xml`, `http://localhost:8080/robots.txt`, `http://localhost:8080/p/{id}.html`
- 프로덕션 확인(머지 후): `https://popup.deluxo.co.kr/sitemap.xml`, `/robots.txt`가 200 OK

## 문제 해결(FAQ)
- PR이 안 보임: 브랜치를 ‘푸시’해야 자동 생성됩니다(이름은 반드시 `vk/`로 시작).
- OAuth 오류(“workflow scope”): 버튼으로 PR 만들기 대신 로컬에서 푸시로 진행하세요.
- 잘못된 계정으로 PR이 열림: PR 닫기 → 올바른 계정으로 로그인 → 브랜치 푸시 후 PR 수동 생성 또는 자동 생성 확인.
- 브랜치 삭제가 안 됨(다른 worktree에 체크아웃):
  - `git worktree list` 확인 → `git worktree remove --force <경로>` → `git worktree prune` → `git branch -D <브랜치>`

## 참고(옵션)
- PR 프리뷰 잡은 기본 비활성화입니다. 필요 시 레포 Settings → Actions → Variables에 `VK_PREVIEW=1`을 추가하면, PR에 web 미리보기 아티팩트를 첨부하도록 동작합니다.

