# Step 2. OpenClaw 스킬 등록

## 개요
OpenClaw에 투자 브리핑용 스킬 2개를 등록합니다.
스킬은 `~/.openclaw/skills/` 폴더에 `SKILL.md` 파일로 저장됩니다.

> **OpenClaw 스킬이란?**
> AI 에이전트에게 특정 작업 방법을 알려주는 지침서입니다.
> `SKILL.md` 파일에 언제, 어떻게 실행할지를 정의하면 에이전트가 이를 참고합니다.

---

## 2-1. 일일 브리핑 스킬 생성

```bash
mkdir -p ~/.openclaw/skills/daily-investment-briefing

cat > ~/.openclaw/skills/daily-investment-briefing/SKILL.md << 'EOF'
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

## Telegram 요약 형식 (파일 저장 완료 후 전송)
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
EOF
```

---

## 2-2. 주간 리포트 스킬 생성

```bash
mkdir -p ~/.openclaw/skills/weekly-portfolio-report

cat > ~/.openclaw/skills/weekly-portfolio-report/SKILL.md << 'EOF'
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

## Telegram 요약 형식 (파일 저장 완료 후 전송)
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
EOF
```

---

## 2-3. 스킬 등록 확인

```bash
openclaw skills list 2>/dev/null | grep -E "daily-investment|weekly-portfolio"
```

정상 출력:
```
│ ✓ ready │ 📈 daily-investment-briefing │ ... │ openclaw-managed │
│ ✓ ready │ 📋 weekly-portfolio-report   │ ... │ openclaw-managed │
```

> ⚠️ `needs setup` 이 뜨면 SKILL.md의 첫 줄 `---` 구분자와 `metadata` JSON 형식을 확인하세요.

✅ Step 2 완료 → [Step 3으로 이동](./step3-briefing-script.md)
