# Step 1. 프로젝트 폴더 및 데이터 파일 생성

## 개요
투자 비서에 필요한 폴더 구조와 기초 데이터 파일을 생성합니다.
- `investor_profile.md`: 투자자 스타일과 기준 정의
- `portfolio.csv`: 보유 종목 목록
- `watchlist.csv`: 관심 종목 목록

---

## 1-1. 폴더 구조 생성

```bash
mkdir -p ~/investment-assistant/{data,reports/{daily,weekly},logs}
```

확인:
```bash
find ~/investment-assistant -type d
```

---

## 1-2. 투자자 프로필 생성

```bash
cat > ~/investment-assistant/data/investor_profile.md << 'EOF'
# 투자자 프로필

## Basic Info
- 이름: 홍길동                    # 본인 이름으로 변경
- 투자 경력: 3년
- 자산 통화: KRW + USD
- 위험 성향: 공격적 중립

## Investment Philosophy & Style
- Value, Quality, Cash Flow 중심
- Shareholder Return, Margin of Safety 중시
- 단기 모멘텀보다 thesis 기반 중장기 보유

## Preferred Sectors / Themes
- 한국: 반도체, 금융, 자동차
- 미국: 금융, 헬스케어, 에너지, 고품질 플랫폼

## Daily Reference Metrics
- KOSPI, KOSDAQ 등락률
- S&P500, 나스닥 등락률
- USDKRW, 미국10년물금리, DXY, WTI, 금, VIX

## Current Investment Themes
- AI 인프라 수혜 반도체
- 고배당 금융주 (금리 환경 수혜)
- 에너지 전환 수혜 소재/에너지

## Risk Management Rules
- 단일 종목 최대 비중 20%
- 섹터 집중도 40% 초과 금지
- thesis 훼손 시 3거래일 내 재검토

## Briefing Highlights
- 보유 종목 thesis 변화 여부
- watchlist 진입 조건 충족 여부
- 즉각 대응 필요한 리스크
EOF
```

> 💡 **팁**: `이름`, `위험 성향`, `Preferred Sectors` 등을 본인 스타일에 맞게 수정하세요.
> 이 파일 내용이 AI 브리핑의 맥락이 됩니다.

---

## 1-3. 포트폴리오 CSV 생성

> ⚠️ **주의**: 아래는 샘플 데이터입니다. 실제 보유 종목과 수량/평단으로 교체하세요.

```bash
cat > ~/investment-assistant/data/portfolio.csv << 'EOF'
ticker,company_name,market,holding_status,quantity,avg_cost,currency,target_weight,thesis,risk_notes,priority
005930,삼성전자,KRX,active,100,72000,KRW,0.15,HBM/파운드리 회복+고배당,실적 가이던스 하향 리스크,1
000660,SK하이닉스,KRX,active,30,180000,KRW,0.10,HBM3E 점유율 확대,AI 수요 둔화시 밸류 재조정,1
005380,현대차,KRX,active,20,220000,KRW,0.08,EV전환+주주환원 확대,미국 관세 리스크,2
105560,KB금융,KRX,active,50,85000,KRW,0.08,고금리 수혜+배당성향 확대,부동산 PF 리스크,2
JPM,JPMorgan Chase,NYSE,active,10,200.0,USD,0.10,글로벌 금융 프랜차이즈+자본배분,경기침체시 대손 증가,1
UNH,UnitedHealth Group,NYSE,active,5,530.0,USD,0.10,헬스케어 플랫폼 독점적 지위,정책 규제 리스크,1
XOM,ExxonMobil,NYSE,active,15,115.0,USD,0.08,자유현금흐름+주주환원,유가 변동성,2
BRK.B,Berkshire Hathaway B,NYSE,active,20,390.0,USD,0.10,복합 가치투자+현금 보유력,승계 리스크 장기,3
CASH_KRW,현금(원화),KRX,cash,0,1,KRW,0.08,유동성 확보,,5
CASH_USD,현금(달러),NYSE,cash,0,1,USD,0.09,환헤지+기회비용,,5
EOF
```

**컬럼 설명:**

| 컬럼 | 설명 | 예시 |
|------|------|------|
| ticker | 종목 코드 | `005930`, `AAPL` |
| company_name | 종목명 | `삼성전자` |
| market | 거래소 | `KRX`, `NYSE`, `NASDAQ` |
| holding_status | 보유 상태 | `active` 또는 `cash` |
| quantity | 보유 수량 | `100` |
| avg_cost | 평균 매입 단가 | `72000` |
| currency | 통화 | `KRW` 또는 `USD` |
| target_weight | 목표 비중 (0~1) | `0.15` = 15% |
| thesis | 보유 이유 | `HBM 수혜+고배당` |
| risk_notes | 주요 리스크 | `실적 하향 리스크` |
| priority | 우선순위 (1=높음) | `1` |

> 💡 **팁**: `holding_status=cash` 행은 브리핑 스크립트에서 자동으로 제외됩니다.
>
> ⚠️ **한국 종목 주의**: yfinance에서 KRX 종목은 `.KS` 접미사가 필요합니다.
> `portfolio.csv`에는 `005930`으로 저장하고, `generate_briefing.py` 내부의 `ticker_map`에서 자동 변환합니다.

---

## 1-4. Watchlist CSV 생성

```bash
cat > ~/investment-assistant/data/watchlist.csv << 'EOF'
ticker,company_name,market,watch_reason,ideal_entry,trigger_condition,invalidation,risk_notes,priority
035420,NAVER,KRX,AI검색 전환+클라우드 성장,170000,클라우드 매출 YoY 30%+,광고 매출 3분기 연속 역성장,라인야후 지배구조,2
035720,카카오,KRX,플랫폼 정상화+밸류 저점,35000,영업이익 흑자전환 확인,규제 리스크 재확대,오버행 리스크,3
MSFT,Microsoft,NASDAQ,Azure 성장 재가속,380,Azure 성장률 30%+ 복귀,AI 수익화 지연,밸류에이션 부담,1
GOOGL,Alphabet,NASDAQ,광고+클라우드 이중 성장,155,GCP 점유율 상승 확인,AI 검색 점유율 잠식,반독점 규제,1
000270,기아,KRX,현대차 대비 밸류 디스카운트,80000,PBR 0.8 이하+자사주 소각,미국 판매 부진,관세 리스크,2
CVX,Chevron,NYSE,XOM 보완+배당 안정성,145,WTI 70달러 이상 안정,카자흐스탄 생산 차질,인수합병 불확실성,3
EOF
```

**컬럼 설명:**

| 컬럼 | 설명 |
|------|------|
| watch_reason | 관심 갖는 이유 |
| ideal_entry | 이상적인 매수 진입가 |
| trigger_condition | 실제 매수 검토 트리거 |
| invalidation | 이 조건이 되면 관심 종목에서 제외 |
| risk_notes | 주요 리스크 |

---

## 1-5. 최종 확인

```bash
echo "=== 폴더 구조 ===" && find ~/investment-assistant -type f
echo ""
echo "=== portfolio.csv ===" && cat ~/investment-assistant/data/portfolio.csv
echo ""
echo "=== watchlist.csv ===" && cat ~/investment-assistant/data/watchlist.csv
```

정상 출력 예:
```
/home/USERNAME/investment-assistant/data/investor_profile.md
/home/USERNAME/investment-assistant/data/portfolio.csv
/home/USERNAME/investment-assistant/data/watchlist.csv
```

✅ Step 1 완료 → [Step 2로 이동](./step2-skills.md)
