---
name: weekly-portfolio-report
description: 매주 월요일 09:10 KST 주간 포트폴리오 리포트 생성. 수익률 vs 벤치마크, thesis 점검, 리밸런싱 후보를 ~/investment-assistant/reports/weekly/YYYY-Wxx.md 로 저장 후 Telegram 6~10줄 요약 전송.
metadata: {"openclaw":{"emoji":"📋","os":["linux","darwin"]}}
---

## 트리거
"주간 리포트", "이번 주 포트폴리오 점검"

## 참조 파일
- 투자자 프로필: ~/investment-assistant/data/investor_profile.md
- 포트폴리오: ~/investment-assistant/data/portfolio.csv
- Watchlist: ~/investment-assistant/data/watchlist.csv

## 실행 순서
1. 주간 날짜 범위 확인 (직전 월~금)
2. 출력 파일명: ~/investment-assistant/reports/weekly/YYYY-Wxx.md
3. 위 참조 파일 3개 읽기
4. yfinance로 주간 시장 데이터 수집
5. 리포트 마크다운 생성 후 저장
6. Telegram으로 6~10줄 요약 전송

## 리포트 필수 섹션
1. 주간 수익률 vs KOSPI/S&P500 벤치마크
2. 기여 분석: 수익/손실 상위 종목
3. 비중 변화: 목표 대비 괴리
4. Thesis 점검: 유지/변경/훼손 분류
5. 밸류에이션 변화 (PER/PBR)
6. 리스크 맵
7. 리밸런싱 후보
8. 다음 주 촉매 (실적/지표/정책)
9. Watchlist 승격 후보
10. 다음 주 액션 플랜

## Telegram 요약 형식
📋 [주간] 포트폴리오 리포트
• 주간 수익률: [수치] vs 벤치마크 [수치]
• 최고 기여: [종목]
• 최저 기여: [종목]
• Thesis 변화: [종목]
• 리밸런싱 후보: [종목]
• 다음 주 촉매: [이벤트]
• 액션: [1순위]

## 원칙
- Telegram은 핵심 수치만, 본문은 markdown 파일로
- thesis 훼손 종목 반드시 명시
- 실행 가능한 리밸런싱 제안 포함
