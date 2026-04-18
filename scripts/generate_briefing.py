#!/usr/bin/env python3
"""
투자 일일 브리핑 생성 스크립트(OpenClaw + yfinance 활용)
- yfinance로 실시간 시장 데이터 수집
- 마크다운 브리핑 파일 저장
- Telegram으로 요약 전송
- OpenClaw agent로 시나리오/액션 자동 채우기
"""
import yfinance as yf
import csv
from datetime import datetime
import subprocess
import os

# ── 설정 ──────────────────────────────────────────
today = datetime.now().strftime("%Y-%m-%d")
output_path = os.path.expanduser(f"~/investment-assistant/reports/daily/{today}.md")

OPENCLAW_BIN = os.path.expanduser("~/.npm-global/bin/openclaw")
TELEGRAM_CHAT_ID = "7733177955"
# ──────────────────────────────────────────────────

# ── 1. 매크로 데이터 수집 ──
macro_tickers = {
    "KOSPI": "^KS11", "KOSDAQ": "^KQ11",
    "S&P500": "^GSPC", "NASDAQ": "^IXIC",
    "USDKRW": "USDKRW=X", "미국10년물": "^TNX",
    "DXY": "DX-Y.NYB", "WTI": "CL=F",
    "금": "GC=F", "VIX": "^VIX"
}

macro = {}
for name, ticker in macro_tickers.items():
    try:
        t = yf.Ticker(ticker)
        i = t.fast_info
        prev = i.previous_close
        last = i.last_price
        chg = ((last - prev) / prev * 100) if prev else 0
        macro[name] = {"price": last, "chg": chg}
    except:
        macro[name] = {"price": 0, "chg": 0}

# ── 2. 포트폴리오 데이터 수집 ──
portfolio = []
csv_path = os.path.expanduser("~/investment-assistant/data/portfolio.csv")
with open(csv_path) as f:
    reader = csv.DictReader(f)
    for row in reader:
        if row["holding_status"] == "cash":
            continue
        # 한국 KRX 종목은 yfinance에서 .KS 접미사 필요
        ticker_map = {
            "005930": "005930.KS", "000660": "000660.KS",
            "005380": "005380.KS", "105560": "105560.KS",
            "000270": "000270.KS", "035420": "035420.KS",
            "035720": "035720.KS", "003690": "003690.KS",
            "051910": "051910.KS", "207940": "207940.KS",
            "012330": "012330.KS",
            "BRK.B": "BRK-B"
        }
        yf_ticker = ticker_map.get(row["ticker"], row["ticker"])
        try:
            t = yf.Ticker(yf_ticker)
            i = t.fast_info
            prev = i.previous_close
            last = i.last_price
            chg = ((last - prev) / prev * 100) if prev else 0
            row["current_price"] = last
            row["chg"] = chg
        except:
            row["current_price"] = 0
            row["chg"] = 0
        portfolio.append(row)

# ── 3. 마크다운 브리핑 생성 ──
def fmt(name):
    m = macro[name]
    arrow = "▲" if m["chg"] >= 0 else "▼"
    return f"{m['price']:,.2f} ({arrow}{abs(m['chg']):.2f}%)"

lines = []
lines.append(f"# 📊 일일 투자 브리핑 — {today}\n")

lines.append("## 1. 시장 요약\n")
lines.append("| 지표 | 수치 |")
lines.append("|------|------|")
for name in macro_tickers:
    lines.append(f"| {name} | {fmt(name)} |")
lines.append("")

lines.append("## 2. 보유 종목 현황\n")
lines.append("| 종목 | 현재가 | 등락 | Thesis | 리스크 |")
lines.append("|------|--------|------|--------|--------|")
for p in portfolio:
    arrow = "▲" if p["chg"] >= 0 else "▼"
    lines.append(f"| {p['company_name']}({p['ticker']}) | {p['current_price']:,.0f} | {arrow}{abs(p['chg']):.2f}% | {p['thesis']} | {p['risk_notes']} |")
lines.append("")

lines.append("## 3. Watchlist 점검\n")
watch_path = os.path.expanduser("~/investment-assistant/data/watchlist.csv")
with open(watch_path) as f:
    reader = csv.DictReader(f)
    lines.append("| 종목 | 감시 이유 | 진입 조건 | 무효화 |")
    lines.append("|------|-----------|-----------|--------|")
    for row in reader:
        lines.append(f"| {row['company_name']}({row['ticker']}) | {row['watch_reason']} | {row['trigger_condition']} | {row['invalidation']} |")
lines.append("")

lines.append("## 4. 시나리오\n")
lines.append("- **Bullish**: \n- **Base**: \n- **Bear**: \n")
lines.append("## 5. 액션 아이디어\n")
lines.append("- [ ] \n")
lines.append("## 6. Thesis 변화\n")
lines.append("- 없음\n")
lines.append(f"\n---\n*생성: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} KST*")

# ── 4. 파일 저장 ──
with open(output_path, "w") as f:
    f.write("\n".join(lines))
print(f"✅ 브리핑 저장 완료: {output_path}")

# ── 5. Telegram 요약 전송 ──
best = max(portfolio, key=lambda x: x["chg"])
worst = min(portfolio, key=lambda x: x["chg"])

summary = f"""📊 {today} 일일 투자 브리핑
• 시장: KOSPI {macro['KOSPI']['price']:,.0f} ({macro['KOSPI']['chg']:+.2f}%) / S&P500 {macro['S&P500']['price']:,.0f} ({macro['S&P500']['chg']:+.2f}%)
• 매크로: USDKRW {macro['USDKRW']['price']:,.0f} / 미국10년물 {macro['미국10년물']['price']:.2f}% / VIX {macro['VIX']['price']:.1f}
• WTI: {macro['WTI']['price']:.2f} ({macro['WTI']['chg']:+.2f}%) / 금: {macro['금']['price']:,.0f}
• 포트폴리오: {best['company_name']} 최고 ({best['chg']:+.2f}%) / {worst['company_name']} 최저 ({worst['chg']:+.2f}%)
• 리포트: {output_path}"""

print("\n" + summary)

result = subprocess.run([
    OPENCLAW_BIN, "message", "send",
    "--channel", "telegram",
    "--target", TELEGRAM_CHAT_ID,
    "--message", summary
], capture_output=True, text=True)

if result.returncode == 0:
    print("✅ Telegram 전송 완료")
else:
    print(f"⚠️ Telegram 전송 실패: {result.stderr}")

# ── 6. AI 시나리오/액션 자동 채우기 ──
import time
time.sleep(3)

scenario_prompt = f"""아래 브리핑 파일의 4번 시나리오와 5번 액션 아이디어를 실제 시장 데이터 기반으로 구체적으로 채워서 {output_path} 파일을 업데이트해줘.
현재 데이터:
- KOSPI: {macro['KOSPI']['price']:,.0f} ({macro['KOSPI']['chg']:+.2f}%)
- S&P500: {macro['S&P500']['price']:,.0f} ({macro['S&P500']['chg']:+.2f}%)
- VIX: {macro['VIX']['price']:.1f} / WTI: {macro['WTI']['price']:.2f} ({macro['WTI']['chg']:+.2f}%)
- USDKRW: {macro['USDKRW']['price']:,.0f}
- 최고 종목: {best['company_name']} ({best['chg']:+.2f}%)
- 최저 종목: {worst['company_name']} ({worst['chg']:+.2f}%)
Bullish/Base/Bear 각 1~2줄, 액션 아이디어 3개 이상 작성해줘."""

result2 = subprocess.run([
    OPENCLAW_BIN, "agent",
    "--to", f"telegram:{TELEGRAM_CHAT_ID}",
    "--message", scenario_prompt
], capture_output=True, text=True)

if result2.returncode == 0:
    print("✅ 시나리오/액션 채우기 완료")
else:
    print(f"⚠️ 시나리오 채우기 실패: {result2.stderr}")
