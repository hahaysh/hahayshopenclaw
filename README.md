# OpenClaw 개인 투자 비서

Claude Code로 설계한 투자 브리핑 자동화 시스템을 **OpenClaw + Azure Linux VM**으로 마이그레이션한 실전 가이드입니다.

매일 아침 Telegram으로 투자 브리핑을 자동으로 받을 수 있습니다.

---

## 완성된 기능

| 기능 | 설명 |
|------|------|
| 일일 브리핑 | 매일 09:00 KST 자동 생성 + Telegram 전송 |
| 주간 리포트 | 매주 월요일 09:10 KST 자동 생성 |
| 실시간 시장 데이터 | yfinance 기반 (KOSPI, S&P500, USDKRW, VIX 등 10개 지표) |
| 마크다운 리포트 | `reports/daily/`, `reports/weekly/` 에 날짜별 누적 저장 |
| AI 시나리오 분석 | OpenClaw agent가 Bullish/Base/Bear 시나리오 자동 작성 |
| Telegram 연동 | 요약 5~8줄 자동 전송 |

---

## 시스템 아키텍처

### 전체 구성도

```
┌─────────────────────────────────────────────────────────────────┐
│                      Azure Linux VM (Ubuntu 24.04)              │
│                                                                 │
│  ┌──────────┐    ┌─────────────────────────────────────────┐   │
│  │   cron   │───▶│         generate_briefing.py            │   │
│  │ 09:00 KST│    │                                         │   │
│  └──────────┘    │  1. yfinance → Yahoo Finance API        │   │
│                  │     (KOSPI, S&P500, VIX 등 10개 지표)   │   │
│  ┌──────────┐    │                                         │   │
│  │   cron   │    │  2. portfolio.csv + watchlist.csv 로드  │   │
│  │ 09:10 KST│    │                                         │   │
│  └────┬─────┘    │  3. 마크다운 브리핑 파일 생성           │   │
│       │          │     reports/daily/YYYY-MM-DD.md         │   │
│       │          └───────────────┬─────────────────────────┘   │
│       │                          │                              │
│       │          ┌───────────────▼─────────────────────────┐   │
│       │          │           OpenClaw Agent                 │   │
│       │          │  (Node.js 기반 AI 에이전트 프레임워크)   │   │
│       │          │                                         │   │
│       └─────────▶│  Skills:                                │   │
│                  │  - daily-investment-briefing             │   │
│                  │  - weekly-portfolio-report               │   │
│                  │                                         │   │
│                  │  AI 모델 (택 1):                        │   │
│                  │  - Anthropic Claude API                  │   │
│                  │  - Azure OpenAI (GPT-4o)                 │   │
│                  │  - GitHub Copilot                        │   │
│                  └───────────────┬─────────────────────────┘   │
│                                  │                              │
└──────────────────────────────────┼──────────────────────────────┘
                                   │
                    ┌──────────────▼──────────────┐
                    │         Telegram Bot         │
                    │   요약 메시지 5~8줄 전송     │
                    └─────────────────────────────┘
```

### 데이터 흐름

```
[cron 09:00]
     │
     ▼
generate_briefing.py
     │
     ├─① yfinance ──────▶ Yahoo Finance (시장 데이터 수집)
     │                        KOSPI / KOSDAQ / S&P500 / NASDAQ
     │                        USDKRW / 미국10년물 / DXY
     │                        WTI / 금 / VIX
     │
     ├─② 파일 읽기 ─────▶ ~/investment-assistant/data/
     │                        portfolio.csv   (보유 종목)
     │                        watchlist.csv   (관심 종목)
     │                        investor_profile.md (투자 스타일)
     │
     ├─③ 브리핑 생성 ──▶ ~/investment-assistant/reports/daily/YYYY-MM-DD.md
     │                        1. 시장 요약
     │                        2. 매크로 지표
     │                        3. 보유 종목 현황
     │                        4. Watchlist 점검
     │                        5. 시나리오 (Bullish/Base/Bear)
     │                        6. 액션 아이디어
     │
     ├─④ Telegram 전송 ▶ openclaw message send
     │                        → 요약 5~8줄 즉시 전송
     │
     └─⑤ AI 분석 ──────▶ openclaw agent
                              → 시나리오/액션 아이디어 AI 자동 생성
                              → 브리핑 파일 업데이트
```

### 컴포넌트별 역할

| 컴포넌트 | 기술 | 역할 |
| -------- | ---- | ---- |
| **cron** | Linux cron | 매일 09:00 / 09:10 KST 자동 실행 |
| **generate_briefing.py** | Python 3 + yfinance | 시장 데이터 수집 → 마크다운 브리핑 생성 → Telegram 전송 트리거 |
| **OpenClaw** | Node.js | AI 에이전트 런타임. Skills 실행 + Telegram 채널 관리 |
| **Skills** | SKILL.md | 브리핑/리포트 생성 지침 정의 (일일/주간) |
| **AI 모델** | Claude / GPT-4o | 시나리오 분석, 액션 아이디어 자동 작성 |
| **yfinance** | Python 라이브러리 | Yahoo Finance에서 실시간 시장 데이터 수집 |
| **Telegram Bot** | Telegram API | 브리핑 요약 수신 채널 |

### 왜 Python 스크립트를 별도로 두나요?

OpenClaw의 기본 AI 모델(GPT-4o 등)은 **실시간 웹 검색 도구가 없습니다.**  
`"오늘 KOSPI 알려줘"` 같은 요청은 403 오류가 발생합니다.  
이 문제를 `yfinance`로 해결합니다 — Yahoo Finance에서 직접 데이터를 가져와 브리핑 파일을 먼저 만든 뒤, OpenClaw AI가 그 데이터를 기반으로 분석/시나리오를 작성합니다.

```
[데이터 수집]    Python + yfinance  →  브리핑 파일(.md)
[AI 분석/작성]   OpenClaw Agent    →  시나리오 + 액션 아이디어
[전송]           OpenClaw + Telegram Bot  →  요약 메시지
```

---

## 파일 구조

```
이 저장소 (GitHub)
├── README.md
├── docs/
│   ├── step0-openclaw-install.md    # OpenClaw 설치 및 Telegram 연결
│   ├── step1-project-setup.md       # 프로젝트 폴더 및 데이터 파일 생성
│   ├── step2-skills.md              # OpenClaw 스킬 등록
│   ├── step3-briefing-script.md     # 브리핑 생성 Python 스크립트
│   ├── step4-cron.md                # cron 자동 스케줄 등록
│   ├── step5-test.md                # 테스트 및 검증
│   └── troubleshooting.md           # 실전 트러블슈팅 7가지
├── skills/
│   ├── daily-investment-briefing/SKILL.md   # 일일 브리핑 스킬 정의
│   └── weekly-portfolio-report/SKILL.md     # 주간 리포트 스킬 정의
├── scripts/
│   └── generate_briefing.py         # 브리핑 생성 핵심 스크립트
└── data-samples/
    ├── portfolio.csv                 # 포트폴리오 샘플
    └── watchlist.csv                 # 관심 종목 샘플

VM 실행 환경 (~/investment-assistant/)
├── data/
│   ├── investor_profile.md          # 투자자 프로필 (스타일, 선호 섹터)
│   ├── portfolio.csv                # 실제 보유 종목
│   └── watchlist.csv                # 실제 관심 종목
├── reports/
│   ├── daily/YYYY-MM-DD.md          # 일일 브리핑 (날짜별 누적)
│   └── weekly/YYYY-Wxx.md           # 주간 리포트 (주차별 누적)
├── logs/
│   ├── daily.log
│   └── weekly.log
└── generate_briefing.py             # 스크립트 (data-samples 기반 복사본)

~/.openclaw/skills/
├── daily-investment-briefing/SKILL.md
└── weekly-portfolio-report/SKILL.md
```

---

## 사전 요구사항

- Azure Linux VM (Ubuntu 24.04 LTS) — SSH 접속 완료 상태
- Telegram 계정 (봇 생성 필요 → Step 0에서 안내)
- Anthropic API 키 또는 Microsoft Azure OpenAI / GitHub Copilot 구독 중 하나

---

## 설치 순서

| 단계 | 내용 |
|------|------|
| [Step 0](./docs/step0-openclaw-install.md) | OpenClaw 설치 및 초기 설정 |
| [Step 1](./docs/step1-project-setup.md) | 프로젝트 폴더 및 데이터 파일 생성 |
| [Step 2](./docs/step2-skills.md) | OpenClaw 스킬 등록 |
| [Step 3](./docs/step3-briefing-script.md) | 브리핑 생성 Python 스크립트 |
| [Step 4](./docs/step4-cron.md) | cron 자동 스케줄 등록 |
| [Step 5](./docs/step5-test.md) | 테스트 및 검증 |

---

## 트러블슈팅

실제 세팅 과정에서 겪은 문제 7가지와 해결법 → [troubleshooting.md](./docs/troubleshooting.md)

---

## 수동 실행 명령어

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

## 데이터 파일 업데이트

```bash
# 포트폴리오 수정 (매수/매도 후)
nano ~/investment-assistant/data/portfolio.csv

# 관심 종목 수정
nano ~/investment-assistant/data/watchlist.csv
```

---

## 관련 링크

- [OpenClaw 공식 사이트](https://openclaw.ai)
- [OpenClaw 문서](https://docs.openclaw.ai)
- [ClawHub 스킬 마켓](https://clawhub.ai)
