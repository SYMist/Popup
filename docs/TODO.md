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
- [ ] 정적 뷰어 스캐폴드(`web/`) — `index.html`, `app.js`, `styles.css`
  - [x] 리스트 카드 UI(대표 이미지/제목/기간/도시/카테고리)
  - [ ] 상세 모달(갤러리/링크/가격 정규화/감지 근거 표시)
  - [x] 카드 클릭 시 상세 페이지로 이동(SEO)
  - [x] 정적 상세 페이지 생성 스크립트(`scripts/build_pages.py`) 및 `web/p/*.html` 출력
  - [x] 필터: `isPopup` 기본 on, 도시/카테고리, 진행상태(진행중/예정/종료)
  - [x] 정렬: 종료일 오름차순 기본, 옵션 제공
  - [x] 검색: 제목 텍스트 포함 검색
- [ ] 퍼포먼스
  - [ ] 인덱스 분할(연-월 단위 `index-YYYY-MM.json`) 및 지연 로딩
  - [x] 캐시 버스팅(쿼리스트링에 `?v=timestamp`)
- [ ] 배포( GitHub Pages )
  - [x] Actions 단계 추가: 크롤 후 인덱스/상세 페이지 빌드 → `web/` 아티팩트 업로드 + `deploy-pages`로 배포
  - [ ] 사용자 도메인/CNAME(선택)
- [ ] 품질/접근성
  - [ ] 스키마/인덱스 필드 검증 스크립트(누락/형식)
  - [ ] 반응형 레이아웃/키보드 내비게이션/대체텍스트

## 운영 메모
- 요약 수치(Modified 과다) 완화: `scripts/storage.py` 저장 시 `meta.fetchedAt` 무시 비교 도입 → 의미 없는 파일 재저장 방지.
- 배포 실행은 내일 수동 트리거 예정.
