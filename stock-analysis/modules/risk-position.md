# Risk & Position Module

> Internal module of the orchestrator. Loaded on demand by the
> orchestrator when the report needs this section, or when the user
> invokes it directly.
>
> Originally shipped as the standalone skill `stock-risk-position-analysis` (pre-2026-05-merge).


## Overview

Convert analysis into risk controls and conditional strategy. This skill does not force a buy/sell call; it defines what must be true for a trade or thesis to remain valid.

## Standalone Markdown Report Mode

When called directly by a user, produce a self-contained Markdown risk and position plan in the user's language. If ticker, entry/current price, horizon, risk tolerance, current holding status, or objective is unclear and materially affects the answer, ask one concise clarification first.

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

- Position budget (account size, or a dollar/% allocation) if provided; otherwise use percentage-based sizing only.
- Risk tolerance — the paper drawdown the user can sit through on this position (conservative ≈ ≤10%, balanced ≈ 10-20%, aggressive ≈ 25%+, or a specific number). Usually supplied by the orchestrator's Request Gate (item 3); if absent, present all three variants.
- Current holding status and average cost basis, if the user already owns the stock — triggers Held-Position Analysis below.
- Entry price or current price, stop level, target levels, ATR, support/resistance, and macro regime.
- Portfolio concentration constraints if provided.

## Position Sizing

Use the SOP formula when account size and stop are known:

`position value = (account value * risk per trade) / abs(entry price - stop price) * entry price`

Default risk styles:

| Style | Tolerable position drawdown | Risk per trade | Single-stock cap | Sector cap | Min reward/risk |
|---|---:|---:|---:|---:|---:|
| conservative | up to ~10% | 0.5% | 5% | 20% | 2:1 |
| balanced | ~10-20% | 1.0% | 10% | 30% | 2:1 |
| aggressive | ~25-40% | 2.0% | 15% | 40% | 3:1 |

The Request Gate captures risk tolerance as the **paper drawdown the user can sit through on this position**. When it is supplied, use that one row and do not present the other two as variants. If the user gave a specific number (e.g. "15%"), use that number directly for the stop logic and map it to the nearest style for the caps (≤10% → conservative, 10-20% → balanced, >20% → aggressive).

**Tolerable drawdown drives the stop.** Place the stop within the user's tolerable-drawdown band. If the volatility-correct stop (2×ATR, or below structural support) is *wider* than that band, the position is too volatile for this risk tolerance at full size — either size down so the dollar loss at the wider stop stays acceptable, or flag the name as unsuitable for this profile. State which applies, and check the stock's annualized volatility (see Volatility-Adjusted Single-Stock Cap below) against the band — a name that routinely swings more than the band will stop the user out on noise.

## Held-Position Analysis

When the user already owns the stock and gave an average cost basis, the recommendation is a **hold / add / trim / exit** decision, not a fresh entry. Produce:

- **Unrealized P&L** — current price vs cost basis, in % and (when budget is known) in dollars; repeat at the bear / base / bull scenario targets so the user sees the gain/loss range, not just the price range.
- **Decision framing** — is the stock a buy *at today's price*? The cost basis is a sunk cost and must not drive the call. State this explicitly when the position is underwater ("the question is whether `<TICKER>` is worth owning now, not whether it returns to your cost").
- **Add vs trim** — if the thesis is intact and the position sits below the single-stock cap, define an add level and size; if the position is above the cap or the thesis has weakened, define a trim/exit plan with levels.
- **Two stop references** — a thesis-invalidation stop (technical) and a capital-preservation stop relative to cost basis; name which one binds first.
- **Holding-period note** — flag short-term vs long-term holding as a factor for the user to check; do not give tax advice.

If the user holds the stock but skipped the cost basis, run the normal fresh-entry framework and note that P&L-relative guidance was not possible.

## Volatility-Adjusted Single-Stock Cap

The single-stock cap above assumes typical 15-30% annualized volatility. Adjust the cap when the name is materially more or less volatile than that baseline.

Compute annualized volatility:

```
daily_vol = stdev(daily_returns, last 60 trading days)
annualized_vol = daily_vol × sqrt(252)
vol_percentile = current annualized_vol vs 252-day rolling distribution
```

Apply this multiplier on top of the style cap, then floor by the style minimum:

| Annualized vol | Cap multiplier | Reasoning |
|---|---|---|
| < 15% (low-vol) | 1.0x (no change, optional 1.25x for utilities/staples) | stable; baseline cap is conservative |
| 15-30% (normal) | 1.0x (baseline) | style cap applies as-is |
| 30-50% (high-vol) | 0.5x to 0.75x | reduce to 5-11% even for balanced/aggressive |
| > 50% (extreme) | 0.5x and not above 10% absolute | small-cap, biotech binary, event names |

If `vol_percentile > 80` (current vol is in top quintile of trailing year), additionally reduce cap by 0.8x — the name is in its own high-vol regime even relative to its history.

Correlation overlay (optional, for portfolio context):

| Average correlation with existing portfolio | Multiplier |
|---|---|
| ≥ 0.80 | 0.70x (highly correlated; diversification fails) |
| 0.60 - 0.80 | 0.85x |
| 0.40 - 0.60 | 1.00x |
| < 0.40 | 1.05x - 1.10x (true diversifier) |

Final cap = style_cap × vol_multiplier × percentile_multiplier × correlation_multiplier.

Always state which adjustments were applied and the resulting cap. When data for the multiplier is missing, fall back to the style cap and disclose the gap.

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

- the risk tolerance used (or conservative / balanced / aggressive variants if none was supplied)
- entry/stop/target plan
- reward/risk ratio
- position sizing formula or percentage guidance
- hold / add / trim / exit guidance and unrealized P&L vs cost basis when the user already owns the stock
- scale-in and scale-out rules
- short-term strategy
- medium-term strategy
- invalidation checklist
- event-risk and gap-risk handling when relevant
- standalone disclaimer when called directly: `Not investment advice -- for your own research.`
