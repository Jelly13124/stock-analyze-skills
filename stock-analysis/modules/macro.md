# Macro Module

> Internal module of the orchestrator. Loaded on demand by the
> orchestrator when the report needs this section, or when the user
> invokes it directly.
>
> Originally shipped as the standalone skill `stock-macro-analysis` (pre-2026-05-merge).


## Overview

Assess the market regime that frames stock selection, valuation multiples, technical risk, and position sizing. Always use current data when tools are available and label every macro data point with its date.

## Standalone Markdown Report Mode

When called directly by a user, produce a self-contained Markdown macro report in the user's language. If ticker/sector, horizon, or objective is unclear, ask one concise clarification first.

Use this structure:

1. `## Macro Regime Verdict`
2. `## Rates, Yield Curve, And Fed Policy`
3. `## Growth, Inflation, And Labor Data`
4. `## Liquidity, Credit, And Volatility`
5. `## Index Trend And Market Breadth`
6. `## Implication For The Target Stock Or Sector`
7. `## Strategy And Risk Adjustment`
8. `## Missing Or Stale Data`

For full-depth requests, include current values, observation dates, trend context, and direct implications for valuation multiple and position sizing.

## Data Failure and Low-Confidence Rules

- If current macro data cannot be fetched, do not label the regime Risk-On or Risk-Off with high confidence.
- If rates, inflation, labor, credit, volatility, or index-trend data is stale, state the observation date and lower confidence.
- If macro signals conflict, present both sides and translate the conflict into valuation and position-sizing uncertainty.
- Do not use macro narrative alone to override stock-specific earnings or valuation evidence.

## Required Output Elements

Every standalone report or main-report section must include a conclusion, source dates, at least one key table when evidence exists, bullish interpretation, bearish interpretation, uncertain/missing evidence, implications for valuation/strategy/risk, and missing data.

## Inputs

- User objective and horizon: short-term trade, medium-term swing, long-term investment, earnings event, or portfolio risk.
- Target ticker or sector if provided.
- Current macro data: Fed Funds, FOMC tone, 2Y/10Y yields, 2Y-10Y spread, real rates/TIPS, DXY, CPI/Core CPI, PCE, NFP, unemployment, GDP, ISM PMI, initial claims.
- Market risk data: VIX, put/call ratio, SPY/QQQ/IWM trend, market breadth, new highs/lows, credit spreads if available.

## Regime Matrix

| Regime | Typical evidence | Strategy implication |
|---|---|---|
| Risk-On aggressive | stable/falling rates, VIX < 20, broad index participation, growth improving | higher equity exposure, growth/cyclical bias |
| Risk-On cautious | mixed data, narrow breadth, VIX 20-25, rates uncertain | moderate exposure, quality bias, tighter stops |
| Risk-Off mild | VIX 25-35, hotter inflation, growth slowing, credit stress rising | lower exposure, defensive sectors, smaller positions |
| Risk-Off extreme | VIX > 35, breadth breakdown, deep curve inversion, liquidity stress | cash/defense first, wait for stabilization |

## Procedure

1. Separate hard data from narrative: quote exact latest values and publication dates.
2. Compare the latest value to trend: 1 month, 3 month, and year-over-year where useful.
3. Determine whether macro supports multiple expansion, multiple compression, or neutral valuation.
4. Translate the regime into stock-specific implications: sector preference, beta tolerance, stop width, earnings multiple, and catalyst risk.
5. Flag conflicts instead of forcing certainty, such as "falling yields bullish for growth, but breadth is deteriorating."

## Output Contract

Return a Markdown report or report section with:

- macro regime label and confidence
- 3-6 evidence bullets with dates
- rates/yield curve table and risk appetite table when data is available
- bullish and bearish interpretation for the target stock
- implication for target price assumptions
- implication for short-term and medium-term strategy
- missing data or stale-source warning
- standalone disclaimer when called directly: `Not investment advice -- for your own research.`
