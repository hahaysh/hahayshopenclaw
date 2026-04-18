---
name: daily-investment-briefing
description: 매일 09:00 KST 투자 일일 브리핑 생성. 시장 요약, 보유 종목 영향, watchlist 점검, 액션 아이디어를 ~/investment-assistant/reports/daily/YYYY-MM-DD.md 로 저장 후 Telegram 5~8줄 요약 전송.
metadata: {"openclaw":{"emoji":"📈","os":["linux","darwin"]}}
---

## 트리거
"오늘 투자 브리핑", "일일 브리핑 실행"

## 참조 파일
- 투자자 프로필: ~/investment-assistant/data/investor_profile.md
- 포트폴리오: ~/investment-assistant/data/portfolio.csv
- Watchlist: ~/investment-assistant/data/watchlist.csv

## 실행 순서
1. 오늘 날짜 확인: date +%Y-%m-%d
2. 위 참조 파일 3개 읽기
3. yfinance로 당일 시장 데이터 수집
4. 브리핑 마크다운 생성 후 ~/investment-assistant/reports/daily/YYYY-MM-DD.md 저장
5. Telegram으로 5~8줄 요약 전송

## 브리핑 필수 섹션
1. 시장 요약 및 원인 분석 (미국→한국 연결 해석)
2. 매크로: 금리/달러/USDKRW/WTI/금/VIX (실제 수치 포함)
3. 섹터 로테이션: 강세/약세
4. 보유 종목 영향 (thesis 변화 여부)
5. Watchlist 진입 트리거 충족 여부
6. 오늘 주요 일정 (지표/실적/연준)
7. Bullish / Base / Bear 시나리오
8. 액션 아이디어
9. Thesis 변화 종목 명시

## Telegram 요약 형식
📊 [날짜] 일일 투자 브리핑
• 시장: [한줄 요약]
• 매크로: [핵심 변화 1~2개]
• 포트폴리오: [중요 변화]
• Watchlist: [트리거 여부]
• 오늘 일정: [주요 이벤트]
• 액션: [즉시 확인 사항]

## 원칙
- 종목 수량/평단 장황 반복 금지
- value/quality/cashflow 스타일 기준 해석
- 실행 가능한 인사이트 중심으로 간결하게
