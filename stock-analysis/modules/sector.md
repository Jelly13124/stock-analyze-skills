# Sector Module

> Internal module of the orchestrator. Loaded on demand by the
> orchestrator when the report needs this section, or when the user
> invokes it directly.
>
> Originally shipped as the standalone skill `stock-sector-analysis` (pre-2026-05-merge).


## Overview

Evaluate whether the company's sector and peer group support or weaken the stock thesis. This skill can be used standalone for sector rotation work or as a sub-skill in a full stock report.

## Standalone Markdown Report Mode

When called directly by a user, produce a self-contained Markdown sector/peer report in the user's language. If ticker, peer set, sector ETF, horizon, or objective is unclear, ask one concise clarification first.

Use this structure:

1. `## Sector Verdict`
2. `## Sector And Industry Classification`
3. `## Relative Strength Versus SPY And Sector ETF`
4. `## Peer Comparison`
5. `## Sector Catalysts And Headwinds`
6. `## Premium Or Discount Justification`
7. `## Implication For Valuation And Strategy`
8. `## Peer Data Gaps`

For full-depth requests, include peer tables and explain why the target should trade at a premium, discount, or event-driven exception.

## Data Failure and Low-Confidence Rules

- If sector ETF or peer data is unavailable, avoid strong sector-relative conclusions.
- If peer estimates are stale or missing, mark valuation and growth comparisons low confidence.
- If the target has no clean peer set, explain the proxy group and why each peer is imperfect.
- If relative-strength data conflicts across windows, state the window used for the strategy horizon.

## Required Output Elements

Every standalone report or main-report section must include a conclusion, source dates, at least one key table when evidence exists, bullish interpretation, bearish interpretation, uncertain/missing evidence, implications for valuation/strategy/risk, and missing data.

## Inputs

- Target ticker, sector, industry, and peer set.
- Sector ETF proxy when available: XLK, XLV, XLF, XLE, XLY, XLP, XLI, XLB, XLRE, XLU, XLC.
- SPY benchmark and relevant industry ETF if one exists.
- Peer valuation, revenue growth, margin, profitability, leverage, price performance, and estimate revision data.

## Procedure

1. Identify the sector, industry, main peers, and clean peer exclusions.
2. Measure sector strength versus SPY over 20D, 60D, 6M, and YTD where possible.
3. Compare the target against peers:
   - growth: revenue/EPS growth, guidance direction
   - quality: gross margin, operating margin, ROIC/ROE, FCF conversion
   - valuation: forward P/E, EV/EBITDA, P/S, P/FCF, PEG
   - technical: relative performance and drawdown
4. Map the sector to the economic cycle:
   - early recovery: Technology, Consumer Discretionary, Industrials, Real Estate
   - mid expansion: Technology, Communication Services, Financials
   - late cycle: Energy, Materials, Healthcare
   - recession: Utilities, Consumer Staples, Healthcare
5. Identify catalysts: policy, regulation, AI/semis/EV/software cycles, supply-demand, inventory, commodity prices, geopolitics.

## Output Contract

Return a Markdown report or report section with:

- sector/industry verdict and confidence
- relative strength ranking versus SPY and peers
- peer table covering growth, margins, profitability, leverage, valuation, and price performance when available
- peer premium/discount explanation
- 3-5 industry catalysts or headwinds
- implication for valuation multiple and strategy
- peer data gaps or stale estimates
- standalone disclaimer when called directly: `Not investment advice -- for your own research.`
