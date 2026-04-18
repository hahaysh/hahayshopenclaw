# CLAUDE.md — OpenClaw 투자 비서 프로젝트 컨텍스트

이 파일은 Claude Code가 새 세션에서도 프로젝트 전체 맥락을 즉시 파악할 수 있도록 작성된 문서입니다.

---

## 프로젝트 개요

매일 아침 09:00 KST에 Azure Linux VM에서 자동으로 투자 브리핑을 생성하고 Telegram으로 전송하는 시스템입니다. OpenClaw(AI 에이전트 런타임)와 yfinance(시장 데이터 수집)를 조합해 구현합니다.

---

## Azure VM 정보

| 항목 | 값 |
|------|-----|
| FQDN | `hahayshopenclaw.koreacentral.cloudapp.azure.com` |
| OS | Ubuntu 24.04.4 LTS |
| 사용자 | `hahaysh` |
| 홈 디렉토리 | `/home/hahaysh/` |
| 접속 방식 | SSH (키 기반) |

---

## 디렉토리 구조

```
/home/hahaysh/
├── hahayshopenclaw/          # GitHub 저장소 클론 (git pull 대상)
│   ├── scripts/
│   │   └── generate_briefing.py   # 소스 파일 (여기서 수정)
│   ├── skills/
│   ├── docs/
│   ├── data-samples/
│   └── .github/workflows/deploy.yml
│
├── investment-assistant/      # 운영 실행 환경 (cron이 직접 실행)
│   ├── generate_briefing.py   # rsync로 scripts/에서 자동 동기화됨
│   ├── data/
│   │   ├── portfolio.csv
│   │   ├── watchlist.csv
│   │   └── investor_profile.md
│   ├── reports/
│   │   ├── daily/YYYY-MM-DD.md
│   │   └── weekly/YYYY-Wxx.md
│   └── logs/
│       ├── daily.log
│       └── weekly.log
│
├── webapp1/                   # investment-assistant/ 경로를 참조하는 웹앱
├── webapp2/                   # investment-assistant/ 경로를 참조하는 웹앱
└── ~/.openclaw/
    └── agents/main/sessions/sessions.json   # Telegram Chat ID 확인 위치
```

---

## ⚠️ 절대 변경 금지 사항

**`/home/hahaysh/investment-assistant/` 디렉토리의 파일명/경로 구조는 절대 변경하지 말 것.**

`webapp1`과 `webapp2`가 이 경로를 직접 참조하고 있습니다. 구조를 바꾸면 두 앱 모두 수정해야 합니다.

- 스크립트 수정은 항상 `hahayshopenclaw/scripts/` 에서 하고 GitHub를 통해 자동 배포합니다.
- `investment-assistant/` 안의 파일을 직접 편집하거나 이름을 바꾸는 일은 하지 않습니다.

---

## GitHub 저장소 및 자동 배포

- **저장소**: `https://github.com/hahaysh/hahayshopenclaw`
- **기본 브랜치**: `main`

### 배포 흐름

```
로컬 수정 → git push origin main
    └─→ GitHub Actions (.github/workflows/deploy.yml)
            ├─→ SSH로 VM 접속
            ├─→ git pull origin main  (hahayshopenclaw/ 업데이트)
            └─→ rsync scripts/ → investment-assistant/  (운영 파일 동기화)
```

### GitHub Secrets

| Secret 이름 | 용도 |
|-------------|------|
| `DEPLOY_SSH_HOST` | `hahayshopenclaw.koreacentral.cloudapp.azure.com` |
| `HAHAYSHOPENCLAWSSH` | VM SSH private key (ed25519) |
| `VM_USER` | `hahaysh` |

---

## Telegram 설정

| 항목 | 값 |
|------|-----|
| Chat ID | `7733177955` |
| 확인 경로 | `~/.openclaw/agents/main/sessions/sessions.json` |

### OpenClaw Telegram 명령어

```bash
# 즉시 메시지 전송
openclaw message send --channel telegram --target 7733177955 --message "텍스트"

# AI 에이전트 실행 + 전송
openclaw agent --to telegram:7733177955 --deliver --message "프롬프트"

# 게이트웨이 상태 확인
openclaw status

# 게이트웨이 백그라운드 실행
openclaw gateway --background
```

- **OpenClaw 바이너리 경로**: `~/.npm-global/bin/openclaw` (cron에서는 풀 경로 필수)

---

## Cron 스케줄

```
# 일일 브리핑 — 매일 09:00 KST (UTC 00:00)
0 0 * * * python3 /home/hahaysh/investment-assistant/generate_briefing.py >> /home/hahaysh/investment-assistant/logs/daily.log 2>&1

# 주간 리포트 — 매주 월요일 09:10 KST (UTC 00:10)
10 0 * * 1 /home/hahaysh/.npm-global/bin/openclaw agent --to telegram:7733177955 --deliver --message "주간 포트폴리오 리포트 생성해줘. ~/investment-assistant/data 참조해서 weekly-portfolio-report 스킬 실행하고 ~/investment-assistant/reports/weekly/$(date +%Y-W%V).md 로 저장해줘." >> /home/hahaysh/investment-assistant/logs/weekly.log 2>&1
```

---

## generate_briefing.py 핵심 구조

```
1. yfinance로 매크로 데이터 수집 (KOSPI, S&P500, USDKRW, VIX 등 10개)
2. portfolio.csv / watchlist.csv 로드 + 현재가 조회
3. 마크다운 브리핑 파일 생성 → reports/daily/YYYY-MM-DD.md
4. openclaw message send → Telegram 5~8줄 요약 즉시 전송
5. 3초 대기
6. openclaw agent → AI가 시나리오(Bullish/Base/Bear) + 액션 아이디어 생성
```

### KRX 종목 yfinance ticker 매핑 (`.KS` 접미사 필수)

```python
ticker_map = {
    "005930": "005930.KS",  # 삼성전자
    "000660": "000660.KS",  # SK하이닉스
    "005380": "005380.KS",  # 현대차
    "105560": "105560.KS",  # KB금융
    "000270": "000270.KS",  # 기아
    "035420": "035420.KS",  # NAVER
    "035720": "035720.KS",  # 카카오
    "003690": "003690.KS",  # Korean RE
    "051910": "051910.KS",  # LG Chem
    "207940": "207940.KS",  # Samsung Biologics
    "012330": "012330.KS",  # Hyundai Mobis
    "BRK.B":  "BRK-B",
}
```

---

## 수동 실행 및 검증

```bash
# 스크립트 즉시 실행 (테스트)
python3 /home/hahaysh/investment-assistant/generate_briefing.py

# 배포 검증 (두 파일이 동일한지 확인)
diff /home/hahaysh/hahayshopenclaw/scripts/generate_briefing.py \
     /home/hahaysh/investment-assistant/generate_briefing.py

# 로그 확인
tail -50 /home/hahaysh/investment-assistant/logs/daily.log

# 리포트 파일 확인
ls -la /home/hahaysh/investment-assistant/reports/daily/
```

---

## 로컬 개발 환경

- **로컬 경로**: `c:\Demo\Copilot\hahayshopenclaw`
- **수정 → 배포 흐름**: 로컬에서 `scripts/generate_briefing.py` 수정 → `git push origin main` → GitHub Actions가 자동으로 VM에 배포

---

## AI 모델 옵션

OpenClaw에서 사용 가능한 AI 모델 (택 1):

| 모델 | 특징 |
|------|------|
| Anthropic Claude API | 웹 검색 가능, 권장 |
| Azure OpenAI (GPT-4o) | Microsoft Foundry, 웹 검색 없음 |
| GitHub Copilot | 구독 기반, 웹 검색 없음 |

> GPT-4o / GitHub Copilot은 웹 검색 도구가 없어 실시간 시장 데이터를 직접 가져올 수 없습니다. 그래서 yfinance로 먼저 데이터를 수집하는 구조입니다.
