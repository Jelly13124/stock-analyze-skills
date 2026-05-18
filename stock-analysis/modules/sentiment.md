# Sentiment Module

> Internal module of the orchestrator. Loaded on demand by the
> orchestrator when the report needs this section, or when the user
> invokes it directly.
>
> Originally shipped as the standalone skill `stock-sentiment-analysis` (pre-2026-05-merge).


## Overview

Translate information flow around a stock into a forward-looking signal. Sentiment is leading on price more often than fundamentals, but it is also the noisiest input. Always weight by source quality and dating, and never present sentiment as a standalone buy/sell call without fundamentals or technicals confirming.

This skill covers four information channels: insider transactions, company news flow, analyst EPS estimate revisions, and short interest / options positioning. It does not cover macro-level risk appetite (VIX, put/call) — that belongs in `stock-macro-analysis`.

## Standalone Markdown Report Mode

When called directly by a user, produce a self-contained Markdown sentiment report in the user's language. If ticker, time window, depth, or objective is unclear, ask one concise clarification first.

Use this structure:

1. `## Sentiment Verdict`
2. `## Data Window And Source Quality`
3. `## Insider Transactions`
4. `## News Flow And Tone`
5. `## Analyst EPS Revisions And Target Changes`
6. `## Short Interest And Options Positioning`
7. `## Aggregated Signal And Confidence`
8. `## Implication For Strategy And Risk`

For full-depth requests, include per-channel tables with dates, quote at least one transcript-grounded news item per direction, and break out the weighted aggregation arithmetic. Avoid returning only bullet summaries.

## Data Failure and Low-Confidence Rules

- If insider Form 4 data is unavailable, use only news + analyst + short interest and disclose the missing channel.
- If news is older than 2 weeks for a near-term call, mark the news channel low confidence rather than letting it dominate.
- If analyst estimate revision data is unavailable, do not infer Wall Street direction from price action alone.
- If short interest is older than the latest FINRA bi-monthly report (typical lag ~15 days), state the report date and label as lagging.
- If options data (IV, skew, put/call) is unavailable, omit options positioning rather than guessing.
- Never label sentiment "extreme bullish" or "extreme bearish" without at least three of four channels confirming in the same direction.

## Required Output Elements

Every standalone report or main-report section must include a conclusion, source dates, at least one key table when evidence exists, bullish interpretation, bearish interpretation, uncertain/missing evidence, implications for valuation/strategy/risk, and missing data.

## Inputs

- Target ticker, sector, current price, and reporting window (default 30/60/90 days; specify if user narrows).
- Insider transactions (SEC Form 4): buyer/seller name, role, share count, transaction value, date, transaction type (open-market buy/sell vs option exercise vs 10b5-1 plan).
- News flow: company-specific news from reputable feeds (Bloomberg, Reuters, WSJ, company IR, sector trades), with publication date and tone.
- Analyst data: number of upward/downward EPS estimate revisions in last 4 weeks, current vs prior consensus EPS, target price changes, recommendation upgrades/downgrades.
- Short interest: latest FINRA bi-monthly short interest, days-to-cover, short interest as % of float, change vs prior period.
- Options data when available: 30D implied volatility vs 30D historical, put/call open interest ratio, skew, unusual options activity.

## Channel Weighting

Default weights for the aggregated signal:

| Channel | Weight | Rationale |
|---|---:|---|
| Analyst EPS revisions | 35% | Strongest leading indicator of forward EPS direction; market reprices on revisions |
| News flow and tone | 25% | Captures catalysts and demand/supply commentary, but noisy |
| Insider transactions | 20% | Open-market cluster buying is high-signal; selling is noisy due to comp/diversification |
| Short interest and options | 20% | Short squeeze risk and option positioning, useful but secondary |

Adjust weights only when one channel is missing or stale. State adjustments in the report.

## Per-Channel Scoring

### Insider Transactions

Score on **open-market** transactions only. Exclude 10b5-1 pre-planned trades, option exercises, gift transfers, and tax withholdings.

| Signal | Threshold | Direction |
|---|---|---|
| Cluster buying | 3+ insiders buying within 30 days, or any single CEO/CFO buy >$500k | Strong bullish |
| Single insider buy | One insider open-market buy >$100k | Mild bullish |
| Cluster selling | 3+ insiders selling within 30 days outside 10b5-1 | Mild bearish |
| Single sale | One sale, especially routine | Neutral |
| No transactions | Window has no Form 4 activity | Neutral |

Insider buying is a much stronger signal than selling. Selling has many non-bearish reasons (diversification, taxes, scheduled plans).

### News Flow

Classify each news item by category and tone:

- **Company-specific positive**: earnings beat, guidance raise, contract win, product launch success, FDA approval, M&A as acquirer at accretive price
- **Company-specific negative**: earnings miss, guidance cut, contract loss, recall, FDA rejection, regulatory probe, key executive departure
- **Sector/macro spillover**: tariff/regulation hitting the sector, peer warnings
- **Neutral**: routine PR, conference appearances, analyst day announcements

Score = (positive count - negative count) / total items. Heavy news periods (>20 items in 30 days) often coincide with catalysts and warrant horizon adjustment.

### Analyst EPS Revisions

Compute over **last 4 weeks**:

| Metric | Bullish | Bearish |
|---|---|---|
| Net revision count | (Up - Down) > 3 | (Up - Down) < -3 |
| Revision ratio | Up / Total > 65% | Down / Total > 65% |
| Forward EPS change | Current vs 30 days ago > +2% | < -2% |
| Target price change | Avg target up >5% | Avg target down >5% |
| Upgrades vs downgrades | Net upgrades ≥ 2 | Net downgrades ≥ 2 |

3+ rows bullish or 3+ rows bearish carries the channel.

### Short Interest and Options

| Metric | Bullish | Bearish |
|---|---|---|
| Short interest as % of float | <5% and falling | >15% and rising |
| Days to cover | <3 | >7 |
| Put/Call OI ratio | <0.7 | >1.3 |
| 30D IV vs 30D HV | IV ≈ HV | IV >> HV (event premium) |

High short interest is **not automatically bearish** — it can fuel a short squeeze on positive catalysts. Note the setup rather than mechanically scoring it bearish.

## Aggregation

For each channel, output one of: `bullish` (+1), `neutral` (0), `bearish` (-1), with a per-channel confidence 0-100%.

Weighted score = Σ (channel signal × channel weight × channel confidence / 100).

Final label:

| Weighted score | Label |
|---:|---|
| > +0.30 | Bullish sentiment |
| +0.10 to +0.30 | Mild bullish |
| -0.10 to +0.10 | Neutral / mixed |
| -0.30 to -0.10 | Mild bearish |
| < -0.30 | Bearish sentiment |

Aggregate confidence = max(\|weighted score\| / 0.5, 0) × 100%, capped at 100%.

## Conflict Rules

- If insider buying is strong but news/analyst are bearish, flag as **divergence — insiders see something the Street has not priced**. Do not auto-resolve; surface for the moderator/debate panel.
- If short interest is high and analyst revisions are turning up, flag **squeeze setup risk** — useful for risk-position skill to widen stop on shorts and tighten stop on longs.
- If news is dominated by a single catalyst (e.g., earnings day), separate "event-driven" from "structural" sentiment so it does not bleed into the medium-term thesis.

## Output Contract

Return a Markdown report or report section with:

- one-sentence sentiment verdict and aggregate confidence
- per-channel signal table (insider / news / analyst / short-options) with direction, confidence, and 1-2 supporting data points each with date
- aggregated weighted score with arithmetic shown
- bullish interpretation, bearish interpretation, and divergences
- implication for short-term strategy (sentiment is a near-term variable)
- implication for risk plan (squeeze setup, event premium, insider divergence)
- data gaps and stale-source warnings
- standalone disclaimer when called directly: `Not investment advice -- for your own research.`
