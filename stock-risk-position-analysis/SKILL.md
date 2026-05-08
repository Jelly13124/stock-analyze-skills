---
name: stock-risk-position-analysis
description: Use when stock analysis needs position sizing, stop loss, take profit, risk-reward, event risk, portfolio exposure, trade plan, or short/medium strategy.
---

# Stock Risk Position Analysis

## Overview

Convert analysis into risk controls and conditional strategy. This skill does not force a buy/sell call; it defines what must be true for a trade or thesis to remain valid.

## Standalone Markdown Report Mode

When called directly by a user, produce a self-contained Markdown risk and position plan in the user's language. If ticker, entry/current price, horizon, risk style, or objective is unclear, ask one concise clarification first.

Use this structure:

1. `## Risk Verdict`
2. `## Assumptions`
3. `## Key Levels And Invalidation`
4. `## Position Sizing`
5. `## Entry, Stop, Take-Profit, And Time Stop`
6. `## Scale-In And Scale-Out Plan`
7. `## Short-Term And Medium-Term Strategy`
8. `## Execution Checklist`

For full-depth requests, provide conservative/balanced/aggressive variants when account size or risk style is unknown.

## Data Failure and Low-Confidence Rules

- If current quote is stale, avoid immediate entry/exit language and provide conditional levels only.
- If ATR, support/resistance, or intraday data is missing, base risk on daily/weekly levels and lower confidence.
- If account size or risk style is unknown, provide conservative, balanced, and aggressive percentage-based variants.
- If a major event is inside the selected trade window, reduce confidence and avoid aggressive entry language unless the user explicitly requests event-driven trading.

## Event Risk Check

Before short-term or medium-term strategy, check upcoming earnings, FOMC/CPI/PCE/jobs dates, company-specific catalysts, unusual options implied volatility when available, and after-hours/pre-market gap risk.

## Required Output Elements

Every standalone report or main-report section must include a conclusion, source dates, at least one key table when evidence exists, bullish interpretation, bearish interpretation, uncertain/missing evidence, implications for valuation/strategy/risk, and missing data.

## Inputs

- Account size if provided; otherwise use percentage-based sizing only.
- User risk style if provided: conservative, balanced, aggressive.
- Entry price or current price, stop level, target levels, ATR, support/resistance, and macro regime.
- Portfolio concentration constraints if provided.

## Position Sizing

Use the SOP formula when account size and stop are known:

`position value = (account value * risk per trade) / abs(entry price - stop price) * entry price`

Default risk styles:

| Style | Risk per trade | Single-stock cap | Sector cap | Min reward/risk |
|---|---:|---:|---:|---:|
| conservative | 0.5% | 5% | 20% | 2:1 |
| balanced | 1.0% | 10% | 30% | 2:1 |
| aggressive | 2.0% | 15% | 40% | 3:1 |

## Stop And Exit Matrix

| Stop type | Method | Use when |
|---|---|---|
| fixed percent | entry minus 5-8% | simple liquid large-cap setup |
| ATR | entry minus 2x ATR(14) | volatility-adjusted setup |
| technical | below support by 1-2% | structure-based trade |
| trailing | trail from high or moving average | protect gains |
| time stop | exit if catalyst/setup fails after N days | capital is tied up |

## Output Contract

Return a Markdown report or report section with:

- risk style assumption
- entry/stop/target plan
- reward/risk ratio
- position sizing formula or percentage guidance
- conservative, balanced, and aggressive variants when user style is unknown
- scale-in and scale-out rules
- short-term strategy
- medium-term strategy
- invalidation checklist
- event-risk and gap-risk handling when relevant
- standalone disclaimer when called directly: `Not investment advice -- for your own research.`
