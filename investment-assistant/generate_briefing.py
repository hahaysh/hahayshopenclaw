#!/usr/bin/env python3
import yfinance as yf
import csv
from datetime import datetime
import subprocess
import os
import time
import re
import shutil

# =========================
# 기본 설정
# =========================
today = datetime.now().strftime("%Y-%m-%d")
output_path = os.path.expanduser(f"~/investment-assistant/reports/daily/{today}.md")

OPENCLAW_BIN = os.environ.get("OPENCLAW_BIN") or shutil.which("openclaw") or os.path.expanduser("~/.npm-global/bin/openclaw")
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
    try:
        result = subprocess.run(
            [OPENCLAW_BIN, "message", "send", "--channel", "telegram", "--target", TELEGRAM_TARGET, "--message", message],
            capture_output=True,
            text=True
        )
    except FileNotFoundError:
        print(f"⚠️ OpenClaw 실행 파일을 찾을 수 없음: {OPENCLAW_BIN}")
        return False
    if result.returncode == 0:
        print("✅ Telegram 전송 완료 (message send)")
        return True
    else:
        print(f"⚠️ Telegram 전송 실패 (message send): {result.stderr}")
        return False

def sanitize_telegram_plain_text(message: str) -> str:
    """
    Telegram plain chat 스타일로 정리.
    - 문서용 Markdown 토큰 제거
    - markdown 링크 [text](url) -> text (url)
    """
    s = (message or "").replace("\r\n", "\n").replace("\r", "\n")

    # markdown 링크를 일반 텍스트로 치환
    s = re.sub(r"\[([^\]]+)\]\((https?://[^)]+)\)", r"\1 (\2)", s)

    # fenced code block 토큰 제거
    s = s.replace("```", "")

    cleaned_lines = []
    for raw_line in s.split("\n"):
        line = raw_line

        # heading marker 제거 (line 시작의 #)
        line = re.sub(r"^\s*#{1,6}\s*", "", line)

        # horizontal rule 스타일 제거
        line = re.sub(r"^\s*-{3,}\s*$", "", line)

        # 문서용 강조 토큰 제거
        line = line.replace("**", "")
        line = line.replace("__", "")
        line = line.replace("`", "")

        cleaned_lines.append(line.rstrip())

    # 빈 줄 3개 이상은 2개로 축소
    out = "\n".join(cleaned_lines)
    out = re.sub(r"\n{3,}", "\n\n", out).strip()
    return out

def openclaw_llm_generate_message(prompt: str) -> str | None:
    """
    OpenClaw agent로 텍스트 생성만 수행.
    CLI 버전에 따라 옵션이 다를 수 있어 2가지 형태를 순차 시도한다.
    """
    candidate_cmds = [
        [OPENCLAW_BIN, "agent", "--message", prompt],
        [OPENCLAW_BIN, "agent", prompt],
    ]

    for cmd in candidate_cmds:
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True
            )
        except FileNotFoundError:
            print(f"⚠️ OpenClaw 실행 파일을 찾을 수 없음: {OPENCLAW_BIN}")
            return None
        if result.returncode == 0:
            text = (result.stdout or "").strip()
            if text:
                return text
    return None

def openclaw_llm_deliver_to_telegram(prompt: str) -> bool:
    """
    OpenClaw agent를 이용해 LLM이 Telegram용 메시지를 작성해서 바로 deliver하게 한다.
    실패 시 False 반환.
    """
    try:
        result = subprocess.run(
            [OPENCLAW_BIN, "agent", "--to", f"telegram:{TELEGRAM_TARGET}", "--deliver", "--message", prompt],
            capture_output=True,
            text=True
        )
    except FileNotFoundError:
        print(f"⚠️ OpenClaw 실행 파일을 찾을 수 없음: {OPENCLAW_BIN}")
        return False
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

with open(csv_path, encoding="utf-8-sig", newline="") as f:
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
with open(watch_path, encoding="utf-8-sig", newline="") as f:
    reader = csv.DictReader(f)
    lines.append("| 종목 | 감시 이유 | 진입 조건 | 무효화 |")
    lines.append("|------|-----------|-----------|--------|")
    for row in reader:
        row["yf_ticker"] = normalize_yf_ticker(row.get("ticker", ""), row.get("market", ""))
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
with open(output_path, "w", encoding="utf-8") as f:
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
너는 개인 투자 비서다. 아래는 오늘의 팩트 요약이다.

[팩트 요약 시작]
{fact_summary}
[팩트 요약 끝]

작성 지침:
- Telegram 채팅용 plain text로 작성한다.
- 반드시 금지: ###, ##, #, **, __, ---, ```, `, [텍스트](URL)
- 허용: 줄바꿈, 빈 줄, 일반 불릿(- 또는 •), 이모지(📊📈⚠️✅)
- 분량은 충분히 자세하게 작성하고, 전체 줄 수는 20~35줄 범위를 목표로 한다.
- 숫자와 사실은 팩트 요약에 있는 값만 사용한다. 추정/보정/새 수치/새 사실 추가를 절대 금지한다.
- 팩트 요약에 없는 종목, 지표, 뉴스, 이벤트를 새로 만들지 않는다.
- 문장은 자연스럽고 읽기 쉽게 쓰되, 정보 밀도는 유지한다.

출력 구조(이 구조 유지):
[오늘 한줄]
- 한 문장 요약

[시장]
- 주요 지표를 3~4줄로 정리

[포트폴리오]
- 상승 Top3를 각 1줄로 작성
- 하락 Top3를 각 1줄로 작성

[Watchlist]
- watchlist 약 5개를 각 1줄로 작성

[오늘 포인트]
- 오늘 체크할 포인트 3~4개

[리포트]
- 상세 리포트 경로 안내

한국어로 작성하라.
"""

llm_generated = openclaw_llm_generate_message(llm_prompt)
if llm_generated:
    telegram_message = sanitize_telegram_plain_text(llm_generated)
    if not openclaw_send_telegram(telegram_message):
        print("⚠️ LLM 메시지 전송 실패, fact_summary 폴백 전송 시도")
        openclaw_send_telegram(sanitize_telegram_plain_text(fact_summary))
else:
    print("⚠️ LLM 메시지 생성 실패, fact_summary 폴백 전송")
    openclaw_send_telegram(sanitize_telegram_plain_text(fact_summary))


# =========================
# 7. 시나리오/액션 자동 채우기 (기존 로직 유지)
# =========================
time.sleep(3)

briefing_content = open(output_path, encoding="utf-8").read()
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

try:
    result2 = subprocess.run(
        [OPENCLAW_BIN, "agent", "--to", f"telegram:{TELEGRAM_TARGET}", "--message", scenario_prompt],
        capture_output=True,
        text=True
    )
except FileNotFoundError:
    result2 = None
    print(f"⚠️ OpenClaw 실행 파일을 찾을 수 없음: {OPENCLAW_BIN}")

if result2 and result2.returncode == 0:
    print("✅ 시나리오/액션 채우기 요청 완료")
else:
    if result2 is not None:
        print(f"⚠️ 시나리오/액션 채우기 실패: {result2.stderr}")
