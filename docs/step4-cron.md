# Step 4. cron 자동 스케줄 등록

## 개요
매일 09:00 KST, 매주 월요일 09:10 KST에 자동으로 브리핑이 실행되도록 cron을 등록합니다.

---

## 4-1. Timezone 확인

Azure VM의 기본 Timezone은 **UTC**입니다.
KST(UTC+9) 기준으로 변환해서 cron을 등록해야 합니다.

```bash
timedatectl | grep "Time zone"
# 출력: Time zone: Etc/UTC (UTC, +0000)
```

| KST | UTC | 설명 |
|-----|-----|------|
| 매일 09:00 | 매일 00:00 | 일일 브리핑 |
| 매주 월 09:10 | 매주 월 00:10 | 주간 리포트 |

---

## 4-2. openclaw 실행 경로 확인

cron은 일반 셸과 PATH가 달라서 **반드시 전체 경로**를 사용해야 합니다.

```bash
which openclaw
# 출력 예: /home/hahaysh/.npm-global/bin/openclaw
```

> ⚠️ `/usr/bin/openclaw` 가 아닐 수 있습니다.
> `which openclaw` 결과를 반드시 확인하고 아래 명령어의 경로와 일치시키세요.

---

## 4-3. cron 등록

아래에서 두 가지를 본인 값으로 변경하세요:
- `/home/hahaysh` → 본인 홈 디렉토리 (`echo $HOME` 으로 확인)
- `7733177955` → 본인 Telegram Chat ID

```bash
(crontab -l 2>/dev/null; cat << 'CRON'
# 투자 일일 브리핑 - 매일 09:00 KST (UTC 00:00)
0 0 * * * python3 /home/hahaysh/investment-assistant/generate_briefing.py >> /home/hahaysh/investment-assistant/logs/daily.log 2>&1

# 주간 포트폴리오 리포트 - 매주 월요일 09:10 KST (UTC 00:10)
10 0 * * 1 /home/hahaysh/.npm-global/bin/openclaw agent --to telegram:7733177955 --deliver --message "주간 포트폴리오 리포트 생성해줘. ~/investment-assistant/data 참조해서 weekly-portfolio-report 스킬 실행하고 ~/investment-assistant/reports/weekly/$(date +%Y-W%V).md 로 저장해줘." >> /home/hahaysh/investment-assistant/logs/weekly.log 2>&1
CRON
) | crontab -
```

---

## 4-4. 등록 확인

```bash
crontab -l
```

정상 출력:
```
# 투자 일일 브리핑 - 매일 09:00 KST (UTC 00:00)
0 0 * * * python3 /home/hahaysh/investment-assistant/generate_briefing.py >> ...

# 주간 포트폴리오 리포트 - 매주 월요일 09:10 KST (UTC 00:10)
10 0 * * 1 /home/hahaysh/.npm-global/bin/openclaw agent ...
```

---

## 4-5. cron 로그 확인

```bash
# 실행 후 로그 확인
tail -f ~/investment-assistant/logs/daily.log
tail -f ~/investment-assistant/logs/weekly.log
```

---

## 4-6. cron 수정/삭제

```bash
# cron 편집
crontab -e

# cron 전체 삭제 후 재등록
crontab -r
```

✅ Step 4 완료 → [Step 5로 이동](./step5-test.md)
