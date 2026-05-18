# Financial Statements Module

> Internal module of the orchestrator. Loaded on demand by the
> orchestrator when the report needs this section, or when the user
> invokes it directly.
>
> Originally shipped as the standalone skill `stock-financial-statement-analysis` (pre-2026-05-merge).


## Overview

Analyze the latest filing and earnings evidence to judge financial quality, trend, and risk. Prefer primary filings and company earnings releases, then reputable financial data providers as secondary sources.

## Standalone Markdown Report Mode

When called directly by a user, produce a self-contained Markdown financial statement report in the user's language. If ticker, reporting period, depth, or objective is unclear, ask one concise clarification first.

Use this structure:

1. `## Financial Quality Verdict`
2. `## Reporting Period And Source Quality`
3. `## Income Statement Trend`
4. `## Balance Sheet And Liquidity`
5. `## Cash Flow And Dilution`
6. `## Earnings Quality And Guidance`
7. `## Red Flags And Accounting Risks`
8. `## Implication For Valuation, Strategy, And Risk`

For full-depth requests, include period-by-period tables and explain GAAP/non-GAAP quality. Avoid returning only bullet summaries.

## Data Failure and Low-Confidence Rules

- If SEC filings cannot be fetched, use company press releases or reputable third-party data only with low confidence and disclose the missing filing.
- If the latest earnings release or transcript is unavailable, do not claim management guidance unless another dated source verifies it.
- If cash flow, debt maturity, SBC, dilution, inventory, or receivables data is missing, include the missing item in the red-flag section rather than omitting it.
- If GAAP and non-GAAP figures conflict across sources, identify the basis used and lower confidence in earnings-quality conclusions.

## Required Output Elements

Every standalone report or main-report section must include a conclusion, source dates, at least one key table when evidence exists, bullish interpretation, bearish interpretation, uncertain/missing evidence, implications for valuation/strategy/risk, and missing data.

## Procedure

1. Establish the reporting period: latest annual, latest quarter, trailing twelve months, and fiscal year-end.
2. Income statement:
   - revenue growth YoY and sequential
   - gross margin, operating margin, net margin
   - EPS growth and estimate beat/miss
   - GAAP versus non-GAAP gap and unusual items
3. Balance sheet:
   - cash and equivalents
   - debt/equity, net debt, maturities if relevant
   - current ratio, liquidity, interest coverage
   - goodwill/intangibles and impairment risk
4. Cash flow:
   - operating cash flow, CapEx, FCF
   - FCF yield and FCF conversion
   - buybacks, dividends, SBC, dilution
5. Earnings quality:
   - guidance raise/lower/maintain
   - backlog, RPO, book-to-bill, AR/inventory signals if relevant
   - management tone from transcript: cautious, optimistic, headwind, demand, pricing, margin.
6. Compare trends to peers and to the company's own 3-5 year history when available.

## Health Checks

| Metric | Healthy signal | Warning signal |
|---|---|---|
| Revenue growth | sustained >10% or peer-leading | two quarters of deceleration |
| Gross margin | stable or expanding | down >3 percentage points YoY |
| FCF conversion | >80% of net income | <50% without clear reason |
| Debt load | manageable coverage | coverage <3x or refinancing pressure |
| Guidance | raise or resilient | lower guidance with demand weakness |

## Quantitative Quick Filters

Use this as a fast numeric overlay on the qualitative analysis above. Score each metric as bullish, neutral, or bearish using the explicit thresholds. These thresholds are calibrated for US large/mid-cap mature companies; adjust the bar lower for small-cap, early growth, or cyclical names and state the adjustment in the report.

### Profitability (bullish if 2 of 3 met)

| Metric | Bullish | Bearish |
|---|---|---|
| Return on equity (ROE, TTM) | > 15% | < 8% |
| Net margin (TTM) | > 20% | < 5% |
| Operating margin (TTM) | > 15% | < 5% |

### Growth (bullish if 2 of 3 met)

| Metric | Bullish | Bearish |
|---|---|---|
| Revenue growth (YoY) | > 10% | < 0% |
| EPS growth (YoY) | > 10% | < 0% |
| Book value per share growth (YoY) | > 10% | < 0% |

### Financial Health (bullish if 2 of 3 met)

| Metric | Bullish | Bearish |
|---|---|---|
| Current ratio | > 1.5 | < 1.0 |
| Debt-to-equity | < 0.5 | > 1.5 |
| Interest coverage (EBIT / interest) | > 5x | < 3x |

### Earnings Quality (bullish if 2 of 3 met)

| Metric | Bullish | Bearish |
|---|---|---|
| FCF per share vs EPS (cash quality) | FCF/share > EPS × 0.8 | FCF/share < EPS × 0.5 |
| FCF conversion (FCF / net income) | > 80% | < 50% |
| ROIC vs WACC spread | ROIC > WACC + 4 ppt | ROIC < WACC |

### Aggregation

Score each of the four categories as `bullish`, `neutral`, or `bearish` using the 2-of-3 majority rule. The overall quantitative verdict is:

- `bullish` when bullish categories > bearish categories
- `bearish` when bearish > bullish
- `neutral` otherwise

Confidence = max(bullish_categories, bearish_categories) / 4 × 100%.

This quantitative verdict is a **filter**, not a recommendation. Always reconcile with the qualitative trend analysis above. If they disagree, state the conflict in `Implication For Valuation, Strategy, And Risk` and lower confidence.

## Output Contract

Return a Markdown report or report section with:

- financial quality verdict
- key metrics table with periods and dates
- earnings/guidance interpretation
- revenue, margin, EPS, cash, debt, OCF/FCF, dilution/SBC, and working-capital discussion when available
- GAAP versus non-GAAP quality and one-time item analysis
- balance-sheet/liquidity risk assessment
- red flags and accounting-quality concerns
- implication for valuation and risk
- data gaps
- standalone disclaimer when called directly: `Not investment advice -- for your own research.`
