# Step 5. 테스트 및 검증

## 개요
전체 시스템이 정상 동작하는지 단계별로 확인합니다.

---

## 5-1. 전체 상태 한 번에 점검

```bash
echo "=== 1. OpenClaw 버전 ===" && openclaw --version
echo "=== 2. 스킬 현황 ===" && openclaw skills list 2>/dev/null | grep -E "daily-investment|weekly-portfolio"
echo "=== 3. 데이터 파일 ===" && ls ~/investment-assistant/data/
echo "=== 4. crontab ===" && crontab -l
echo "=== 5. Timezone ===" && timedatectl | grep "Time zone"
echo "=== 6. Telegram 채널 ===" && openclaw status | grep -A 2 "Telegram"
echo "=== 7. openclaw 프로세스 ===" && ps aux | grep openclaw-gateway | grep -v grep
```

정상 체크리스트:
- [ ] OpenClaw 버전 출력됨
- [ ] 스킬 2개 `✓ ready` 상태
- [ ] 데이터 파일 3개 존재
- [ ] crontab 2개 등록됨
- [ ] Timezone: UTC
- [ ] Telegram: `ON · OK`
- [ ] `openclaw-gateway` 프로세스 실행 중

---

## 5-2. 일일 브리핑 수동 테스트

```bash
python3 ~/investment-assistant/generate_briefing.py
```

확인할 것:
1. 터미널에 `✅ 브리핑 저장 완료` 출력
2. 터미널에 `✅ Telegram 전송 완료` 출력
3. **Telegram에 브리핑 요약 메시지 수신 확인**
4. 파일 생성 확인:

```bash
ls ~/investment-assistant/reports/daily/
cat ~/investment-assistant/reports/daily/$(date +%Y-%m-%d).md
```

---

## 5-3. 주간 리포트 수동 테스트

```bash
# YOUR_CHAT_ID를 본인 Chat ID로 변경
openclaw agent \
  --to telegram:YOUR_CHAT_ID \
  --deliver \
  --message "주간 포트폴리오 리포트 생성해줘. ~/investment-assistant/data 참조해서 weekly-portfolio-report 스킬 실행하고 ~/investment-assistant/reports/weekly/$(date +%Y-W%V).md 로 저장해줘."
```

```bash
ls ~/investment-assistant/reports/weekly/
```

---

## 5-4. 최종 파일 구조 확인

```bash
find ~/investment-assistant -type f | sort
```

정상 출력 예:
```
/home/USERNAME/investment-assistant/data/investor_profile.md
/home/USERNAME/investment-assistant/data/portfolio.csv
/home/USERNAME/investment-assistant/data/watchlist.csv
/home/USERNAME/investment-assistant/generate_briefing.py
/home/USERNAME/investment-assistant/logs/daily.log
/home/USERNAME/investment-assistant/reports/daily/2026-04-17.md
/home/USERNAME/investment-assistant/reports/weekly/2026-W16.md
```

---

## 5-5. 이후 관리

```bash
# 포트폴리오 업데이트 (매수/매도 후)
nano ~/investment-assistant/data/portfolio.csv

# Watchlist 업데이트
nano ~/investment-assistant/data/watchlist.csv

# 브리핑 로그 확인
tail -20 ~/investment-assistant/logs/daily.log
```

---

🎉 **모든 Step 완료!**

이제 매일 KST 09:00에 Telegram으로 투자 브리핑이 자동 전송됩니다.

문제가 생기면 → [troubleshooting.md](./troubleshooting.md)
