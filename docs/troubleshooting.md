# 트러블슈팅 가이드

실제 세팅 과정에서 만났던 문제들과 해결 방법을 정리했습니다.

---

## ❌ 문제 1: `openclaw message "..."` 명령어 오류

**증상:**
```
error: too many arguments for 'message'. Expected 0 arguments but got 1.
```

**원인:** `openclaw message`는 서브커맨드가 필요합니다. 문자열을 직접 인자로 받지 않습니다.

**해결:**
```bash
# ❌ 잘못된 방법
openclaw message "안녕하세요"

# ✅ AI 에이전트에게 작업 요청
openclaw agent --to telegram:CHAT_ID --message "안녕하세요" --deliver

# ✅ Telegram으로 단순 메시지 전송
openclaw message send --channel telegram --target CHAT_ID --message "안녕하세요"
```

---

## ❌ 문제 2: cron에서 openclaw를 찾지 못함

**증상:** cron은 실행되지만 브리핑이 생성되지 않고 로그에 `command not found` 에러 발생

**원인:** cron의 PATH에는 npm global 경로(`~/.npm-global/bin`)가 포함되지 않습니다.

**해결:** crontab에 전체 경로(full path) 사용

```bash
# 실제 경로 확인
which openclaw
# 출력: /home/USERNAME/.npm-global/bin/openclaw

# ❌ 잘못된 cron 등록 — 경로 없음
0 0 * * * openclaw agent ...

# ✅ 올바른 cron 등록 — 전체 경로 사용
0 0 * * * /home/USERNAME/.npm-global/bin/openclaw agent ...
```

---

## ❌ 문제 3: 웹 검색 실패 (403 오류)

**증상:**
```
외부 웹 검색에서 많은 페이지가 접근 제한(403 오류)으로 정보를 가져올 수 없었습니다.
```

**원인:** Microsoft Foundry(gpt-4o, gpt-5-mini) 모델은 웹 검색 도구가 없습니다.
Claude API나 OpenAI API 키가 있어야 웹 검색이 가능합니다.

**해결:** yfinance Python 스크립트로 직접 시장 데이터 수집 → [Step 3 참고](./step3-briefing-script.md)

```bash
pip install yfinance --break-system-packages
python3 -c "import yfinance as yf; t=yf.Ticker('^GSPC'); print(t.fast_info.last_price)"
```

---

## ❌ 문제 4: openclaw agent가 파일을 저장하지 않음

**증상:** `openclaw agent`로 브리핑 요청 시 터미널에는 내용이 출력되지만 실제 파일이 생성되지 않음

**원인:** 에이전트가 응답을 생성하더라도 실제로 bash 파일 쓰기를 실행하지 않는 경우가 있습니다.

**해결 방법 1:** 명시적으로 bash 실행 요청
```bash
openclaw agent --to telegram:CHAT_ID \
  --message "bash로 echo 'test' > ~/test.md 실행해줘"
```

**해결 방법 2 (권장):** Python 스크립트가 파일 저장을 직접 처리
→ `generate_briefing.py`가 파일 저장을 직접 수행합니다. Step 3의 방식을 따르세요.

---

## ❌ 문제 5: Telegram Chat ID를 모를 때

**해결 방법 1:** 세션 파일에서 확인
```bash
cat ~/.openclaw/agents/main/sessions/sessions.json \
  | python3 -m json.tool \
  | grep "telegram:direct"
# 출력: "agent:main:telegram:direct:7733177955"
# → Chat ID = 7733177955
```

**해결 방법 2:** Telegram 전송 기록에서 확인
```bash
cat ~/.openclaw/agents/main/sessions/sessions.json.telegram-sent-messages.json
# 출력: {"7733177955": {...}}
# → 첫 번째 키가 Chat ID
```

---

## ❌ 문제 6: 한국 종목 주가 조회 실패

**증상:** `005930` 같은 KRX 종목이 yfinance에서 조회되지 않거나 0이 반환됨

**원인:** yfinance에서 한국 KRX 종목은 `.KS` 접미사가 필요합니다.

**해결:** `generate_briefing.py`의 `ticker_map`에 매핑 추가

```python
ticker_map = {
    "005930": "005930.KS",   # 삼성전자
    "000660": "000660.KS",   # SK하이닉스
    "005380": "005380.KS",   # 현대차
    "105560": "105560.KS",   # KB금융
    "000270": "000270.KS",   # 기아
    "035420": "035420.KS",   # NAVER
    "035720": "035720.KS",   # 카카오
    "BRK.B":  "BRK-B",       # Berkshire (점 대신 하이픈)
}
```

---

## ❌ 문제 7: 시나리오/액션 섹션이 비어있음

**증상:** 브리핑 파일의 `## 4. 시나리오`와 `## 5. 액션 아이디어`가 빈칸으로 저장됨

**원인:** `openclaw agent`로 파일 업데이트 요청이 실제 파일 쓰기로 이어지지 않은 경우

**해결:** `generate_briefing.py` 하단의 시나리오 채우기 섹션이 실행됐는지 확인

```bash
# 스크립트 실행 시 마지막 출력 확인
python3 ~/investment-assistant/generate_briefing.py
# 마지막 줄에 "✅ 시나리오/액션 채우기 완료" 가 출력되어야 함
```

출력됐지만 파일에 반영이 안 됐다면 에이전트 응답을 직접 확인:
```bash
openclaw agent \
  --to telegram:CHAT_ID \
  --message "~/investment-assistant/reports/daily/오늘날짜.md 파일의 4번 시나리오와 5번 액션 아이디어를 구체적으로 채워서 파일을 업데이트해줘."
```

---

## 💡 일반 팁

### Telegram에서 직접 브리핑 요청
OpenClaw가 연결된 Telegram 채팅에서 직접 메시지로도 트리거 가능합니다:
```
오늘 투자 브리핑 생성해줘
주간 포트폴리오 리포트 만들어줘
```

### VM 재시작 후 OpenClaw 상태 확인
```bash
# openclaw-gateway 자동 시작 확인
ps aux | grep openclaw-gateway | grep -v grep

# 실행 안 됐으면
openclaw gateway --background
```

### yfinance 장 마감 시간 주의
- **한국 KRX**: 16:00 KST 마감 → 이후 종가 수집 가능
- **미국 NYSE/NASDAQ**: 04:00 KST(다음날) 마감
- 09:00 KST 브리핑 = **전일 종가 기준** 데이터

### OpenClaw 업데이트
```bash
npm update -g openclaw
openclaw --version
```
