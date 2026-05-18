# Technical Module

> Internal module of the orchestrator. Loaded on demand by the
> orchestrator when the report needs this section, or when the user
> invokes it directly.
>
> Originally shipped as the standalone skill `stock-technical-analysis` (pre-2026-05-merge).


## Overview

Analyze price action for timing, risk levels, and invalidation. Use current OHLCV data when available and state the last price date/time.

For stock reports, prefer API-generated daily and weekly charts over prose-only technical analysis. If the orchestrator (this skill's SKILL.md) is active, use its `scripts/fetch_price_charts.py` output when available.

The script is a data provider only. It must not make recommendations. This skill interprets the script's quote, OHLCV indicators, relative-strength data, volume ratios, support/resistance distances, and chart artifacts.

If the user asks for technical analysis, K-line/candlestick analysis, RSI/KDJ timing, breakout confirmation, or short-term trading but does not specify the analysis window, ask one concise clarification first: today intraday, last 1 trading day, 1 week, 2 weeks, 1 month, daily swing, or weekly medium-term.

## Standalone Markdown Report Mode

When called directly by a user, produce a self-contained Markdown technical report in the user's language. If ticker, technical window, depth, or objective is unclear, ask one concise clarification first.

Use this structure:

1. `## Technical Verdict`
2. `## Data Health And Chart Artifacts`
3. `## Multi-Timeframe Trend`
4. `## Relative Strength And Volume`
5. `## Support, Resistance, And Reward/Risk`
6. `## Indicator Confirmation`
7. `## KDJ/RSI Overbought-Oversold Read`
8. `## Entry, Stop, Target, And Invalidation`
9. `## Bullish Setup And Bearish Setup`

For full-depth requests, include daily, weekly, and requested intraday tables plus chart paths. Avoid relying on RSI/KDJ alone.

## Data Failure and Low-Confidence Rules

- If intraday data is unavailable, provide only daily/weekly technical analysis and state that intraday timing is unavailable.
- If current-session bars are available but not exchange-direct realtime, use them when `usable_for_report=true` and label the source, latest bar time, and data quality.
- If chart generation fails, disclose the failure and do not invent chart readings.
- If volume, relative-strength, or benchmark data is missing, lower confidence in breakout/breakdown calls.

## Required Output Elements

Every standalone report or main-report section must include a conclusion, source dates, at least one key table when evidence exists, bullish interpretation, bearish interpretation, uncertain/missing evidence, implications for valuation/strategy/risk, and missing data.

## Decision Priority

Resolve conflicting indicators with this priority order:

1. Trend structure: price versus 50EMA/50SMA and 200SMA, slope, higher highs/lows or lower highs/lows.
2. Relative strength: performance versus SPY, QQQ when relevant, and the relevant sector/industry ETF.
3. Volume: breakout/breakdown confirmation, volume ratio, accumulation/distribution, and OBV when available.
4. Support/resistance: entry location, nearby supply, invalidation level, and reward/risk.
5. Indicator confirmation: RSI, KDJ, MACD, Bollinger Bands, ATR, and OBV confirm or warn, but do not override trend/structure by themselves.
6. Candlestick pattern: use only as secondary confirmation.

If RSI/KDJ are overbought while trend, relative strength, and volume are bullish, interpret the setup as "strong but extended" rather than bearish. If RSI/KDJ are oversold while trend and relative strength are bearish, interpret it as "falling knife risk" rather than bullish.

## Procedure

1. Use multi-timeframe structure:
   - weekly: primary trend and major support/resistance
   - daily: medium-term setup and signal confirmation
   - 4H/1H when data is available: entry timing only
   - intraday K-line: use only when the user requested or confirmed an intraday window.
2. Apply the priority framework before reading oscillators.
3. Calculate or inspect:
   - EMA 10/20, EMA 50, SMA 200
   - relative strength versus SPY and sector/industry ETF
   - volume versus 20-period average
   - support/resistance and reward/risk
   - RSI(14), KDJ(9,3,3), MACD(12,26,9), Bollinger Bands(20,2), ATR(14), OBV
   - KDJ cross events, but treat them as detected technical events rather than standalone recommendations.
4. Read trend:
   - bullish: price above EMA50/SMA200, rising averages, higher highs/lows
   - bearish: price below key averages, lower highs/lows, failed breakouts
   - neutral: range-bound, mixed averages, low conviction
5. Identify patterns only when visible in data: cup and handle, double bottom, ascending triangle, bull flag, head and shoulders, double top, descending triangle, bear flag.
6. Convert analysis into levels:
   - support
   - resistance
   - breakout trigger
   - stop/invalidation
   - ATR-adjusted risk band

## Signal Checklist

| Priority | Area | Bullish | Bearish |
|---:|---|---|---|
| 1 | Trend structure | above EMA50/SMA200, rising averages, higher highs/lows | below key averages, lower highs/lows, failed breakouts |
| 2 | Relative strength | outperforming SPY and sector ETF | underperforming SPY and sector ETF |
| 3 | Volume | breakout with volume expansion | breakdown with volume expansion |
| 4 | Support/resistance | entry near support or clean breakout with reward/risk >= 2:1 | entry directly below resistance or poor reward/risk |
| 5 | RSI/KDJ/MACD/Bollinger/ATR/OBV | confirms setup or flags extension | confirms breakdown or flags oversold bounce risk |

Use RSI and KDJ together as the primary overbought/oversold confirmation pair, but only as priority-5 evidence. A single extreme reading is a risk state, not a standalone entry or exit. Treat RSI<30 plus K/D<20 or J<0 as a stronger oversold candidate, and RSI>70 plus K/D>80 or J>100 as a stronger overbought warning. Confirm with trend, relative strength, support/resistance, and volume before strategy output.

Do not treat a single KDJ golden cross, RSI oversold reading, or MACD cross as a standalone buy/sell recommendation.

KDJ basis rule: daily/weekly `kdj_9_3_3` from the script is completed OHLCV-bar KDJ, not realtime. Intraday `kdj_9_3_3` is candle-based from the selected intraday source. Report the data source, `data_quality`, resolution, window, latest bar timestamp, `has_intraday_today`, and `usable_for_report`. Do not over-emphasize `is_realtime=false`; when `usable_for_report=true`, state that the intraday chart is usable current-session or delayed-bar analysis, not exchange-direct realtime.

## Quantitative Strategy Layer

Use this as an optional numeric overlay running **alongside** Decision Priority, not replacing it. Score four independent strategies, then blend into a single score. The qualitative trend/RS/volume/structure read in Decision Priority always wins ties.

### Four Strategies And Weights

| Strategy | Weight | Indicators |
|---|---:|---|
| Trend Following | 30% | EMA(8/21/55) alignment + ADX(14) trend strength |
| Momentum | 30% | 1M / 3M / 6M return + volume momentum |
| Mean Reversion | 20% | Z-score(20) + Bollinger position + RSI(14/28) |
| Volatility Regime | 20% | Annualized vol + vol percentile + ATR ratio |

Compute each strategy's signal as `+1` bullish, `0` neutral, `-1` bearish, with per-strategy confidence 0-100%.

### Trend Following (weight 30%)

| Signal | Bullish | Bearish |
|---|---|---|
| EMA stack | EMA_8 > EMA_21 > EMA_55 | EMA_8 < EMA_21 < EMA_55 |
| ADX(14) | > 25 with rising +DI | > 25 with rising -DI |
| Slope | All EMAs rising | All EMAs falling |

3 of 3 met = bullish/bearish; 2 of 3 = mild; otherwise neutral.

### Momentum (weight 30%)

| Signal | Bullish | Bearish |
|---|---|---|
| 1-month return | > +5% | < -5% |
| 3-month return | > +10% | < -10% |
| 6-month return | > +15% | < -15% |
| Volume momentum | 20D avg volume > 1.2x 60D avg | < 0.8x 60D avg |

3+ rows bullish = bullish; 3+ rows bearish = bearish.

### Mean Reversion (weight 20%)

Compute 20-day Z-score of price: `z = (close - SMA20) / stdev20`.

| Signal | Bullish (oversold reversion) | Bearish (overbought reversion) |
|---|---|---|
| Z-score | < -2.0 | > +2.0 |
| Bollinger position | < 0.2 (near lower band) | > 0.8 (near upper band) |
| RSI(14) and RSI(28) | both < 30 | both > 70 |

Mean reversion signals **conflict with trend signals by design**. When trend is strong (ADX > 30) and mean reversion is extreme, prefer the trend read and treat MR as a "do not chase" warning, not a counter-trade trigger.

### Volatility Regime (weight 20%)

Compute annualized volatility: `ann_vol = stdev(daily_returns, 60) × sqrt(252)`.
Vol regime = `ann_vol / median(rolling_60d_ann_vol over last 252 days)`.

| Signal | Bullish | Bearish |
|---|---|---|
| Vol regime | < 0.8 (compressed) with bullish trend | > 1.2 (expanded) with bearish trend |
| ATR ratio (ATR14 / price) | declining, < 90D median | rising, > 90D median |
| Z-score interaction | vol compression + price Z < -1 | vol expansion + price Z > +1 |

Low volatility favors trend continuation; expanding volatility into resistance is a breakdown warning.

### Aggregated Strategy Score

```
strategy_score = Σ (signal × weight × confidence/100)
```

| Score | Label |
|---:|---|
| > +0.25 | Quantitative bullish |
| +0.10 to +0.25 | Mild bullish |
| -0.10 to +0.10 | Neutral / mixed |
| -0.25 to -0.10 | Mild bearish |
| < -0.25 | Quantitative bearish |

### Reconciliation With Decision Priority

When Quantitative Strategy Score and Decision Priority verdict **agree**, raise overall confidence.

When they **disagree**, Decision Priority wins for the strategy call, but surface the disagreement explicitly in the report (e.g., "trend structure bullish but momentum and volatility regime warn extended; reduce size or widen stop"). Never let the quantitative score override the qualitative trend/structure read on its own.

## Output Contract

Return a Markdown report or report section with:

- trend label by timeframe
- priority interpretation table: trend, relative strength, volume, support/resistance, indicator confirmation
- indicator table
- daily and weekly chart paths or explicit chart-generation failure
- intraday candlestick/KDJ/volume chart path when requested, or explicit failure/skip status
- intraday usability status: source, latest bar timestamp, current-session coverage, and whether it is suitable for report analysis
- detected KDJ golden/death cross events with dates/timestamps when available
- support/resistance levels
- entry/stop/target zones
- bullish and bearish setup
- data timestamp and limitations
- standalone disclaimer when called directly: `Not investment advice -- for your own research.`
