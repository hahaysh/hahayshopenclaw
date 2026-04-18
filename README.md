# 🦞 OpenClaw 개인 투자 비서

Claude Code로 작성한 투자 브리핑 자동화 시스템을 **OpenClaw + Azure Linux VM**으로 마이그레이션한 실전 가이드입니다.

매일 아침 Telegram으로 투자 브리핑을 자동으로 받을 수 있습니다.

---

## ✨ 완성된 기능

| 기능 | 설명 |
|------|------|
| 📊 일일 브리핑 | 매일 09:00 KST 자동 생성 + Telegram 전송 |
| 📋 주간 리포트 | 매주 월요일 09:10 KST 자동 생성 |
| 💹 실시간 시장 데이터 | yfinance 기반 (KOSPI, S&P500, USDKRW, VIX 등 10개 지표) |
| 📁 마크다운 리포트 | `reports/daily/`, `reports/weekly/` 에 날짜별 누적 저장 |
| 🤖 AI 시나리오 분석 | OpenClaw agent가 Bullish/Base/Bear 시나리오 자동 작성 |
| 💬 Telegram 연동 | 요약 5~8줄 자동 전송 |

---

## 🏗️ 시스템 구조

```
investment-assistant/
├── data/
│   ├── investor_profile.md     # 투자자 프로필 (스타일, 선호 섹터 등)
│   ├── portfolio.csv           # 보유 종목
│   └── watchlist.csv           # 관심 종목
├── reports/
│   ├── daily/                  # 일일 브리핑 (YYYY-MM-DD.md)
│   └── weekly/                 # 주간 리포트 (YYYY-Wxx.md)
├── logs/
│   ├── daily.log
│   └── weekly.log
└── generate_briefing.py        # 브리핑 생성 핵심 스크립트

~/.openclaw/skills/
├── daily-investment-briefing/SKILL.md
└── weekly-portfolio-report/SKILL.md
```

---

## ✅ 사전 요구사항

- Azure Linux VM (Ubuntu 24.04 LTS) — SSH 접속 완료 상태
- Telegram 계정 (봇 생성 필요 → Step 0에서 안내)
- Anthropic API 키 또는 Microsoft Azure OpenAI / GitHub Copilot 구독 중 하나

---

## 🚀 설치 순서

| 단계 | 내용 |
|------|------|
| [Step 0](./docs/step0-openclaw-install.md) | OpenClaw 설치 및 초기 설정 |
| [Step 1](./docs/step1-project-setup.md) | 프로젝트 폴더 및 데이터 파일 생성 |
| [Step 2](./docs/step2-skills.md) | OpenClaw 스킬 등록 |
| [Step 3](./docs/step3-briefing-script.md) | 브리핑 생성 Python 스크립트 |
| [Step 4](./docs/step4-cron.md) | cron 자동 스케줄 등록 |
| [Step 5](./docs/step5-test.md) | 테스트 및 검증 |

---

## ⚠️ 트러블슈팅

실제 세팅 과정에서 겪은 문제 7가지와 해결법 → [troubleshooting.md](./docs/troubleshooting.md)

---

## 📱 수동 실행 명령어

```bash
# 일일 브리핑 즉시 실행
python3 ~/investment-assistant/generate_briefing.py

# 주간 리포트 즉시 실행
openclaw agent \
  --to telegram:YOUR_CHAT_ID \
  --deliver \
  --message "주간 포트폴리오 리포트 생성해줘. ~/investment-assistant/data 참조해서 weekly-portfolio-report 스킬 실행하고 ~/investment-assistant/reports/weekly/$(date +%Y-W%V).md 로 저장해줘."
```

---

## 📂 데이터 파일 업데이트

```bash
# 포트폴리오 수정 (매수/매도 후)
nano ~/investment-assistant/data/portfolio.csv

# 관심 종목 수정
nano ~/investment-assistant/data/watchlist.csv
```

---

## 🔗 관련 링크

- [OpenClaw 공식 사이트](https://openclaw.ai)
- [OpenClaw 문서](https://docs.openclaw.ai)
- [ClawHub 스킬 마켓](https://clawhub.ai)
