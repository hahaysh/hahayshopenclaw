#!/usr/bin/env python3
import yfinance as yf
import csv
from datetime import datetime
import subprocess
import os
import time

# =========================
# 기본 설정
# =========================
today = datetime.now().strftime("%Y-%m-%d")
output_path = os.path.expanduser(f"~/investment-assistant/reports/daily/{today}.md")

OPENCLAW_BIN = os.path.expanduser("~/.npm-global/bin/openclaw")
TELEGRAM_TARGET = "7733177955"

# =========================
# 유틸
# =========================
def pct(v):
    return f"{v:+.2f}%"

def arrow(v):
    return "▲" if v >= 0 else "▼"

def normalize_yf_ticker(raw_ticker: str, market: str | None = None) -> str:
    """
    yfinance용 ticker 정규화.
    - 6자리 숫자(KRX)는 .KS 또는 .KQ를 붙인다.
    - market 힌트가 있으면 KOSDAQ 계열은 .KQ를 우선.
    """
    t = (raw_ticker or "").strip()
    m = (market or "").strip().lower()

    # 이미 suffix가 있거나 특수 티커면 그대로
    if "." in t or t.startswith("^") or t.endswith("=X") or t in ["BRK.B", "BRK-B"]:
        if t == "BRK.B":
            return "BRK-B"
        return t

    # 6자리 숫자면 KRX로 가정
    if t.isdigit() and len(t) == 6:
        # market이 KOSDAQ이면 .KQ, 아니면 기본 .KS
        if m in ("kosdaq", "kq"):
            return f"{t}.KQ"
        return f"{t}.KS"

    return t

def safe_fastinfo(ticker: str):
    """
    yfinance fast_info 안전 조회.
    실패 시 (0,0) 반환.
    """
    try:
        t = yf.Ticker(ticker)
        i = t.fast_info
        prev = i.previous_close
        last = i.last_price
        chg = ((last - prev) / prev * 100) if prev else 0
        return float(last), float(chg)
    except Exception:
        return 0.0, 0.0

def openclaw_send_telegram(message: str) -> bool:
    """
    OpenClaw message tool로 Telegram 전송.
    """
    result = subprocess.run(
        [OPENCLAW_BIN, "message", "send", "--channel", "telegram", "--target", TELEGRAM_TARGET, "--message", message],
        capture_output=True,
        text=True
    )
    if result.returncode == 0:
        print("✅ Telegram 전송 완료 (message send)")
        return True
    else:
        print(f"⚠️ Telegram 전송 실패 (message send): {result.stderr}")
        return False

def openclaw_llm_deliver_to_telegram(prompt: str) -> bool:
    """
    OpenClaw agent를 이용해 LLM이 Telegram용 메시지를 작성해서 바로 deliver하게 한다.
    실패 시 False 반환.
    """
    result = subprocess.run(
        [OPENCLAW_BIN, "agent", "--to", f"telegram:{TELEGRAM_TARGET}", "--deliver", "--message", prompt],
        capture_output=True,
        text=True
    )
    if result.returncode == 0:
        print("✅ Telegram 전송 완료 (LLM deliver)")
        return True
    else:
        print(f"⚠️ LLM deliver 실패: {result.stderr}")
        return False

# =========================
# 1. 매크로 데이터 수집
# =========================
macro_tickers = {
    "KOSPI": "^KS11",
    "KOSDAQ": "^KQ11",
    "S&P500": "^GSPC",
    "NASDAQ": "^IXIC",
    "USDKRW": "USDKRW=X",
    "미국10년물": "^TNX",
    "DXY": "DX-Y.NYB",
    "WTI": "CL=F",
    "금": "GC=F",
    "VIX": "^VIX"
}

macro = {}
for name, ticker in macro_tickers.items():
    last, chg = safe_fastinfo(ticker)
    macro[name] = {"price": last, "chg": chg}

# =========================
# 2. 포트폴리오 데이터 수집
# =========================
portfolio = []
csv_path = os.path.expanduser("~/investment-assistant/data/portfolio.csv")

with open(csv_path) as f:
    reader = csv.DictReader(f)
    for row in reader:
        holding_status = (row.get("holding_status", "") or "").strip().lower()

        # cash는 제외
        if holding_status == "cash":
            continue

        # "보유 종목"만 포트폴리오로 취급 (watch/observe 같은 값이면 제외)
        # (환경에 따라 값이 다를 수 있어 폭넓게 허용)
        HOLDING_WHITELIST = {"active", "holding", "hold", "owned", "open", "position"}
        if holding_status and holding_status not in HOLDING_WHITELIST:
            continue

        raw = row.get("ticker", "")
        market = row.get("market", "")
        yf_ticker = normalize_yf_ticker(raw, market)

        last, chg = safe_fastinfo(yf_ticker)
        row["current_price"] = last
        row["chg"] = chg

        portfolio.append(row)

# =========================
# 3. 마크다운 브리핑 생성
# =========================
def fmt_macro(name):
    m = macro[name]
    a = "▲" if m["chg"] >= 0 else "▼"
    return f"{m['price']:,.2f} ({a}{abs(m['chg']):.2f}%)"

lines = []
lines.append(f"# 📊 일일 투자 브리핑 — {today}\n")

lines.append("## 1. 시장 요약\n")
lines.append("| 지표 | 수치 |")
lines.append("|------|------|")
for name in macro_tickers:
    lines.append(f"| {name} | {fmt_macro(name)} |")
lines.append("")

lines.append("## 2. 보유 종목 현황\n")
lines.append("| 종목 | 현재가 | 등락 | Thesis | 리스크 |")
lines.append("|------|--------|------|--------|--------|")
for p in portfolio:
    a = "▲" if p["chg"] >= 0 else "▼"
    # current_price가 0이면 표시를 단순화
    price_str = f"{p['current_price']:,.0f}" if p["current_price"] else "0"
    lines.append(
        f"| {p.get('company_name','')}({p.get('ticker','')}) | {price_str} | {a}{abs(p['chg']):.2f}% | {p.get('thesis','')} | {p.get('risk_notes','')} |"
    )
lines.append("")

# Watchlist는 리포트에 그대로 유지 (Telegram에서는 요약만)
lines.append("## 3. Watchlist 점검\n")
watchlist_rows = []
watch_path = os.path.expanduser("~/investment-assistant/data/watchlist.csv")
with open(watch_path) as f:
    reader = csv.DictReader(f)
    lines.append("| 종목 | 감시 이유 | 진입 조건 | 무효화 |")
    lines.append("|------|-----------|-----------|--------|")
    for row in reader:
        watchlist_rows.append(row)
        lines.append(
            f"| {row.get('company_name','')}({row.get('ticker','')}) | {row.get('watch_reason','')} | {row.get('trigger_condition','')} | {row.get('invalidation','')} |"
        )
lines.append("")

# 시나리오/액션은 나중에 OpenClaw로 채움
lines.append("## 4. 시나리오\n")
lines.append("- **Bullish**: \n- **Base**: \n- **Bear**: \n")

lines.append("## 5. 액션 아이디어\n")
lines.append("- [ ] \n")

lines.append("## 6. Thesis 변화\n")
lines.append("- 없음\n")

lines.append(f"\n---\n*생성: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} KST*")

# ── 4. 파일 저장 ──
os.makedirs(os.path.dirname(output_path), exist_ok=True)
with open(output_path, "w") as f:
    f.write("\n".join(lines))

print(f"✅ 브리핑 저장 완료: {output_path}")

# =========================
# 5. Telegram용 '팩트 요약' 생성 (LLM 입력으로 사용)
# =========================
TOP_N = 3
portfolio_sorted = sorted(portfolio, key=lambda x: x.get("chg", 0), reverse=True)
top_gainers = [p for p in portfolio_sorted[:TOP_N] if p.get("current_price", 0) != 0]
top_losers = [p for p in sorted(portfolio, key=lambda x: x.get("chg", 0))[:TOP_N] if p.get("current_price", 0) != 0]

WATCH_N = 5
watchlist_pick = watchlist_rows[:WATCH_N]

kospi = macro["KOSPI"]
kosdaq = macro["KOSDAQ"]
sp500 = macro["S&P500"]
nasdaq = macro["NASDAQ"]
usdkrw = macro["USDKRW"]
vix = macro["VIX"]
wti = macro["WTI"]
us10y = macro["미국10년물"]

fact_lines = []
fact_lines.append(f"📊 {today} 포트폴리오 브리핑\n")

fact_lines.append("[시장]")
fact_lines.append(f"- KOSPI {kospi['price']:,.0f} ({pct(kospi['chg'])}) / KOSDAQ {kosdaq['price']:,.0f} ({pct(kosdaq['chg'])})")
fact_lines.append(f"- S&P500 {sp500['price']:,.0f} ({pct(sp500['chg'])}) / NASDAQ {nasdaq['price']:,.0f} ({pct(nasdaq['chg'])})")
fact_lines.append(f"- USDKRW {usdkrw['price']:,.0f} / 미국10년물 {us10y['price']:.2f}% / VIX {vix['price']:.1f}")
fact_lines.append(f"- WTI {wti['price']:.2f} ({pct(wti['chg'])})")
fact_lines.append("")

fact_lines.append("[보유 종목 변화]")
if not top_gainers and not top_losers:
    fact_lines.append("- 변동 데이터 없음(가격 조회 실패 가능)")
else:
    if top_gainers:
        fact_lines.append(f"- 상승 Top{len(top_gainers)}")
        for p in top_gainers:
            fact_lines.append(f"  • {p.get('company_name','')} {arrow(p['chg'])}{abs(p['chg']):.2f}% (현재가 {p['current_price']:,.0f})")
    if top_losers:
        fact_lines.append(f"- 하락 Top{len(top_losers)}")
        for p in top_losers:
            fact_lines.append(f"  • {p.get('company_name','')} {arrow(p['chg'])}{abs(p['chg']):.2f}% (현재가 {p['current_price']:,.0f})")
fact_lines.append("")

fact_lines.append("[Watchlist 체크]")
if not watchlist_pick:
    fact_lines.append("- watchlist 비어 있음")
else:
    for w in watchlist_pick:
        trig = (w.get("trigger_condition", "") or "").strip()
        if len(trig) > 60:
            trig = trig[:60] + "…"
        fact_lines.append(f"- {w.get('company_name','')}({w.get('ticker','')}): {trig}")
fact_lines.append("")

fact_lines.append("📄 상세 리포트")
fact_lines.append(f"→ {output_path}")

fact_summary = "\n".join(fact_lines)
print("\n" + fact_summary)

# =========================
# 6. (NEW) LLM 기반 Telegram 메시지 생성 & 전송
# =========================
llm_prompt = f"""
너는 개인 투자 비서다. 아래는 오늘의 '팩트 요약'이다.

[팩트 요약 시작]
{fact_summary}
[팩트 요약 끝]

작성 지침:
- Telegram 채팅 메시지 형식으로 작성하라.
- 문서용 Markdown 문법은 사용하지 말 것.
  (###, ##, **굵게**, --- 같은 문서 표기만 금지)
- 단순 텍스트 불릿(-, •)과 줄바꿈은 사용해도 된다.
- 내용은 최대한 상세하게 유지하라. 요약하지 말 것.
- 보고서처럼 딱딱하게 쓰지 말고, 사람이 읽기 좋은 톤을 유지하라.
- 숫자와 사실은 위 요약에 있는 것만 사용하라. 새 정보 생성 금지.

출력 구조(이 구조 유지):
[오늘 한줄]
- 한 문장 요약

[시장]
- 주요 지표 정리

[포트폴리오]
- 상승 Top3
- 하락 Top3

[Watchlist]
- 감시 중인 종목 요약

[오늘 포인트]
- 체크할 포인트 3~4개

[리포트]
- 상세 리포트 경로 안내

한국어로 작성하라.
"""


# =========================
# 7. 시나리오/액션 자동 채우기 (기존 로직 유지)
# =========================
time.sleep(3)

briefing_content = open(output_path).read()
scenario_prompt = f"""아래 브리핑 파일의 4번 시나리오와 5번 액션 아이디어를 실제 시장 데이터 기반으로 구체적으로 채워서 {output_path} 파일을 업데이트해줘.
현재 데이터:
- KOSPI: {macro['KOSPI']['price']:,.0f} ({macro['KOSPI']['chg']:+.2f}%)
- S&P500: {macro['S&P500']['price']:,.0f} ({macro['S&P500']['chg']:+.2f}%)
- VIX: {macro['VIX']['price']:.1f}
- WTI: {macro['WTI']['price']:.2f} ({macro['WTI']['chg']:+.2f}%)
- USDKRW: {macro['USDKRW']['price']:,.0f}
- 최고 종목: {max(portfolio, key=lambda x: x['chg'])['company_name']} ({max(portfolio, key=lambda x: x['chg'])['chg']:+.2f}%)
- 최저 종목: {min(portfolio, key=lambda x: x['chg'])['company_name']} ({min(portfolio, key=lambda x: x['chg'])['chg']:+.2f}%)
Bullish/Base/Bear 각 1~2줄, 액션 아이디어 3개 이상 작성해줘."""

result2 = subprocess.run(
    [OPENCLAW_BIN, "agent", "--to", f"telegram:{TELEGRAM_TARGET}", "--message", scenario_prompt],
    capture_output=True,
    text=True
)

if result2.returncode == 0:
    print("✅ 시나리오/액션 채우기 요청 완료")
else:
    print(f"⚠️ 시나리오/액션 채우기 실패: {result2.stderr}")
