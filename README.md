# DSOLAR 태양광 공고 모니터

대성쏠라의 태양광·신재생에너지 사업 기회를 찾기 위한 자동 공고 모니터링 프로젝트입니다.

## 현재 구조

- `solar-notice-monitor.html` : 모니터링 대시보드
- `collector/solar_notice_collector.py` : 공개 RSS 수집 + 태양광 관련도 점수화
- `.github/workflows/solar-notice-monitor.yml` : 매시간 자동 실행
- `data/notices.json` : 누적 공고 데이터
- `monitor-status.json` : 마지막 실행 상태

## 동작 방식

GitHub Actions가 매시간 수집기를 실행하고, 공개 RSS에서 태양광·신재생·영농형태양광 관련 공고/뉴스를 수집합니다. 키워드별 가중치를 이용해 관련도 점수를 계산하고 `data/notices.json`에 누적 저장합니다.

대시보드는 GitHub Pages에서 `data/notices.json`을 읽어 최신 데이터를 표시합니다.

## 다음 확장

1. 나라장터/조달청 공식 데이터 소스
2. 기업마당·중기부 공고
3. 한국에너지공단 관련 공고
4. 경상남도·거제시 등 지자체 고시·공고
5. 네이버/구글 검색 결과 보조 수집
6. 신규 공고 이메일/메신저 알림
7. 대성쏠라 사업별 영업기회 점수
