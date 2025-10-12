# Automation Guide (Vibe‑Kanban, macOS)

본 문서는 macOS 환경에서 Vibe‑Kanban(이하 VK) 자동화 흐름과 PR 로컬 미리보기 방법을 간단히 정리합니다.

## VK 작업 흐름
1) 티켓 생성 후 main 브랜치에서 description 작성
2) 티켓을 In progress로 옮기고 ‘start’ 실행 → VK가 `vk/*` 브랜치를 만들고 작업 시작 (자동)
3) 완료되면 VK가 PR을 생성/갱신 (자동)
4) PR이 생성되면 워크플로우가 빌드 후 아티팩트를 업로드하고, PR 본문과 Step Summary에 로컬 미리보기 방법을 게시

## 사전 준비 (macOS)
- 터미널 사용: Terminal 또는 iTerm
- Python 3 설치 확인: `python3 --version`
- GitHub CLI 설치 및 로그인: `gh auth status` (필요시 `gh auth login`)

## PR 로컬 미리보기 (권장)
PR 페이지 본문에 “Local Preview (no Pages deploy)” 블록이 자동으로 추가됩니다. 해당 명령을 터미널에서 실행하세요.

1) 아티팩트 다운로드 및 폴더 준비
```
gh run download <run_id> -R <owner>/<repo> -n github-pages -D web-preview
```

2) 로컬 서빙 시작
```
python3 -m http.server -d web-preview 8080
# 또는 동일 동작:
# python3 -m http.server 8080 --directory web-preview
```

3) 브라우저 열기
```
open http://localhost:8080
```

참고
- `<run_id>`, `<owner>/<repo>`는 PR 본문 스니펫에 실제 값으로 채워져 제공됩니다. 그대로 복사‑붙여넣기하면 됩니다.
- GitHub CLI를 사용하지 않는 경우, PR → Checks → 해당 워크플로우 실행 → Artifacts에서 `github-pages`를 수동으로 다운로드한 뒤 압축을 풀고 폴더를 `web-preview`로 두면 2) 이후 단계만 실행하면 됩니다.

## 아티팩트 없이 직접 빌드해서 확인 (대안)
레포 루트에서 다음을 실행해 정적 리소스를 생성하고 바로 서빙할 수 있습니다.

1) 의존성 설치
```
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2) 데이터/페이지 빌드
```
python scripts/build_index.py --output web/data/index.json --shard monthly
python scripts/build_pages.py --out-dir web/p
```

3) 로컬 서빙
```
python3 -m http.server -d web 8080
open http://localhost:8080
```

## 선택: 소량 크롤링으로 최신 데이터 반영
빠른 스모크 테스트가 필요하면 일부만 크롤링한 후 위 빌드 과정을 반복하세요.
```
python scripts/crawl_popups.py --limit 30 --fast --workers 8 --qps 2.0
```

## 트러블슈팅
- 포트 사용 중: `8080` 대신 `8081` 등 다른 포트 사용 (명령의 포트 숫자만 변경)
- gh 인증 오류: `gh auth login`으로 GitHub 로그인 (권한 허용 필요)
- 아티팩트가 안 보임: 워크플로우 실행이 완료되었는지 확인하고, Run의 Artifacts에 `github-pages`가 있는지 점검
- 미리보기 초기화: `rm -rf web-preview`로 폴더 정리 후 다시 다운로드

