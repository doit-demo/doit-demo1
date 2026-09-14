# DSOLAR 태양광 공고 모니터

대성쏠라의 태양광·신재생에너지 사업 기회를 찾기 위한 자동 공고 모니터링 프로젝트입니다.

## 바로 실행

### 1. GitHub에서 자동 실행

`Actions → Solar Notice Monitor → Run workflow`를 누르면 즉시 한 번 수집할 수 있습니다.

기본 스케줄은 매시간입니다.

### 2. Windows 로컬 실행

저장소를 내려받은 뒤 `run_local.bat`을 더블클릭하면 수집기를 실행하고 모니터 화면을 엽니다.

Python 3가 필요합니다.

## 현재 구조

- `solar-notice-monitor.html` : 모니터링 대시보드
- `collector/solar_notice_collector.py` : 실제 공개 RSS 수집 + 태양광 관련도 점수화 + 사업유형 분류
- `collector/sources.json` : 수집원 설정
- `collector/korea_public_sources.json` : 국내 공공데이터 수집원 레지스트리
- `.github/workflows/solar-notice-monitor.yml` : 매시간 자동 실행
- `data/notices.json` : 누적 공고 데이터
- `monitor-status.json` : 마지막 실행/수집원별 상태
- `run_local.bat` : Windows 원클릭 실행

## 현재 동작

GitHub Actions가 매시간 수집기를 실행하고, 공개 RSS에서 태양광·신재생·영농형태양광 등 관련 자료를 수집합니다. 키워드 가중치와 제외 키워드로 관련도를 계산하고, 발전사업·영농형/농촌·공공부지·지붕형·주민참여·수상태양광 등 사업유형을 분류합니다.

기업마당 지원사업 API는 `BIZINFO_API_KEY` GitHub Secret을 등록하면 활성화됩니다.

대시보드는 저장된 `data/notices.json`과 `monitor-status.json`을 읽어 현재 수집 결과와 소스 상태를 표시합니다.

## 실제 서비스로 확장하는 순서

1. 나라장터/조달청 공식 입찰공고 API 연결
2. 나라장터 발주계획 API 연결
3. 한국에너지공단 공고 adapter 연결
4. 경상남도·거제시 고시·공고 adapter 연결
5. 신규 공고 알림(이메일/메신저)
6. 대성쏠라 사업별 영업기회 점수 고도화
