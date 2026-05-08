---
name: stock-analysis
description: Use when analyzing stocks, ETFs, tickers, target prices, trade strategy, valuation, technicals, earnings, fundamentals, macro risk, or Markdown/DOCX stock reports.
---

# Stock Analysis

## Overview

Use this as the main orchestrator for SOP-driven US stock analysis. It clarifies ambiguous requests, selects report depth and output format, gathers current evidence, invokes the relevant standalone stock sub-skills, and produces one professional Markdown or DOCX report.

Always treat financial facts as time-sensitive. Fetch current market data, filings, earnings dates, guidance, news, analyst estimates, macro data, and technical prices when tools or browsing are available. If live data cannot be fetched, state the data limitation clearly and avoid pretending the report is current.

End user-facing reports with: `Not investment advice -- for your own research.`

## Claude.ai Web Compatibility

This skill supports Claude Code, Claude Desktop, Codex, and Claude.ai web. In Claude.ai web, direct network access from Python may be restricted even when web search or web fetch tools work.

Before running `scripts/fetch_price_charts.py`, locate API keys in this order:

1. explicit user-provided path
2. `./key.txt`
3. `/mnt/user-data/uploads/key.txt`
4. `/mnt/data/key.txt`

Run the script normally first. If the output Data Health shows `network_blocked`, `missing_key`, or `all_providers_failed` for quote/daily/weekly/intraday data, use `scripts/web_prefetch_helper.md`:

1. gather quote and OHLCV data with web search / web fetch
2. write JSON files to `/tmp/prefetched_data`
3. re-run the same script command, preferably with `--output-dir auto`

Always disclose provider fields in the final report. Mark `prefetched_web` as a secondary source with lower confidence for intraday precision.

## Request Gate

Before producing any report, determine ticker, report depth, output format, user objective, and technical-analysis window.

If the user already specifies these items, proceed. If any item is unclear, ask one concise clarification before analysis. Do not default to `standard`.

Use this combined question when the request is vague, such as a bare ticker:

`Please confirm report depth (basic / standard / full SOP), output format (Markdown / DOCX), objective (target price / short-term trade / medium-term strategy / long-term investment / earnings review), and technical window (today intraday / 1-week K-line / daily swing / weekly medium-term).`

A bare ticker such as `NVDA` is considered vague. Ask the combined question rather than defaulting to `basic`, `standard`, or `full SOP`.

If the user requests technical analysis, K-line/candlestick analysis, RSI/KDJ timing, breakout confirmation, or short-term trading but does not specify the window, ask what period to analyze before running the script. Examples: today intraday, last 1 trading day, 1 week, 2 weeks, 1 month, daily swing, or weekly medium-term.

If the user explicitly asks for "complete", "full", "professional report", or "完整报告", use `full SOP`. If the user asks for "quick", use `basic`. Use the user's latest language for the report.

See `references/depth-framework.md` for the depth matrix. For `full` reports, also read `references/Stock_Analysis_SOP_v1.0.md` and follow the seven-step SOP unless the user narrows the task.

## Report Depth Matrix

| Depth | Use when | Required output |
|---|---|---|
| `basic` | Quick view, first-pass ticker opinion, simple risk check | Data Health, price/trend snapshot, key support/resistance, valuation snapshot, main risks, short conditional view. No full DCF and no formal debate. |
| `standard` | Normal stock analysis, target price, report, or strategy request | Macro, sector/peer, fundamentals, financial statement review, valuation, technicals, risk plan, bear/base/bull range, and one counter-thesis section. No formal multi-agent debate unless requested. |
| `full SOP` | Complete SOP, institutional-style report, professional report, multi-agent debate, or highest-depth request | Full seven-step SOP, primary-source evidence, Evidence Ledger, relative valuation and DCF/scenario math, daily/weekly/requested intraday charts, sensitivity, catalysts, invalidation levels, scoring, event risk, and bull/bear/quant/risk/moderator debate. |

## Report Format Gate

Default to Markdown only when the user explicitly says Markdown, md, chat report, or when they ask for an answer in chat. Produce DOCX when the user asks for docx, Word, formal document, polished report, or a file attachment.

For DOCX output:

- Use a document-generation workflow available in the environment, such as the `documents` or `doc` skill when present.
- Include title, data timestamp, Data Health, executive summary, consistent section headings, tables, daily/weekly/requested intraday charts, evidence ledger, and disclaimer.
- For `full SOP`, use a clean professional layout, add chart captions below images, keep tables narrow enough for Word page width, and place the data timestamp near the title.
- Render or inspect the DOCX when the environment supports it; if not, state that visual verification was not run.

## Workflow

1. Resolve the ticker, exchange, company name, sector, industry, and report language.
2. Confirm depth and user objective: quick view, target price, short-term trade, medium-term swing, long-term investment, earnings review, or risk check.
3. Collect source data with dates:
   - price, volume, market cap, beta, 52-week range
   - latest 10-K/10-Q, earnings release, guidance, transcript if available
   - revenue/EPS estimates, analyst targets, recommendation trend
   - macro indicators: rates, yield curve, VIX, SPY/QQQ trend, credit/risk appetite
   - sector ETF and peer comparison
   - technical history sufficient for SMA/EMA, RSI, KDJ, MACD, Bollinger Bands, ATR, support/resistance
4. Fetch API-based daily, weekly, and requested intraday charts:
   - Use the bundled data script: `scripts/fetch_price_charts.py <TICKER> --key-file <workspace-key-file> --output-dir <workspace>/outputs --benchmark SPY --sector <sector-etf>`.
   - In Claude.ai web, use `--output-dir auto` so the script writes to a platform-appropriate output directory.
   - When the user specifies or confirms an intraday/K-line window, add `--intraday-window <today|1d|2d|5d|1w|2w|1m|3m> --intraday-resolution <1|5|15|30|60>`.
   - Intraday source defaults to Yahoo chart current-session bars because that is sufficient for K-line/KDJ/volume analysis and avoids repeated failures from realtime-only candle endpoints. Use `--intraday-source auto` or `--intraday-source finnhub` only when the user explicitly asks for a realtime-capable candle source.
   - This is currently the only bundled data script. It uses `scripts/data_provider.py` to choose direct API, prefetched web JSON, or yfinance data, then generates artifacts only: quote status, daily/weekly OHLCV-derived indicators, optional intraday candle-derived indicators, daily/weekly/intraday PNG charts, benchmark/sector relative strength data, volume ratios, support/resistance distances, KDJ cross events, indicator metadata, and a `technical_data_summary`.
   - KDJ values are computed from OHLCV high/low/close bars. Daily/weekly KDJ is completed-bar close-based. Intraday KDJ is candle-based from the selected intraday source. Always describe `intraday.source`, `data_quality`, `has_intraday_today`, `usable_for_report`, latest bar timestamp, resolution, and window. Do not frame `is_realtime=false` as a data failure when `usable_for_report=true`; simply state that the chart is current-session or delayed bars rather than exchange-direct realtime.
   - Charts should include candlesticks, volume, KDJ, support/resistance lines, and detected KDJ golden/death crosses when data is available.
   - The script must not make recommendations or label a setup bullish/bearish. Skills interpret its data by priority: trend structure, relative strength, volume, support/resistance, then indicator confirmation.
   - If chart generation fails, disclose the failure in Data Health and do not invent chart readings.
5. Invoke sub-skills according to depth:
   - `stock-macro-analysis`
   - `stock-sector-analysis`
   - `stock-company-fundamentals`
   - `stock-financial-statement-analysis`
   - `stock-valuation-analysis`
   - `stock-technical-analysis`
   - `stock-risk-position-analysis`
   - `stock-debate-panel` only for `full` or when explicitly requested.
   - For `full SOP`, the `stock-company-fundamentals` section must follow its bilingual institutional report reference and include investment question, business/segment map, unit economics, industry structure, competitive position, catalysts, management/capital allocation, financial translation, thesis breakers, and evidence gaps.
6. Build an evidence ledger: bullish facts, bearish facts, uncertain/missing data, catalysts, invalidation points.
7. Produce the requested Markdown or DOCX report using `references/report-template.md`.

## Data Failure and Fallback Rules

Apply these rules before drawing conclusions:

- If SEC filings cannot be fetched, use third-party financial data only with low confidence and disclose the limitation.
- If company IR, earnings release, or transcript cannot be fetched, do not claim management guidance unless another dated source verifies it.
- If analyst estimates are unavailable, omit estimate-based target price logic or mark it low confidence.
- If macro data cannot be fetched, do not classify the macro regime as Risk-On or Risk-Off with high confidence.
- If sector ETF or peer data is unavailable, avoid strong sector-relative conclusions.
- If intraday data is unavailable, provide only daily/weekly technical analysis.
- If current quote is stale, avoid immediate entry/exit language and use conditional levels only.
- If data sources conflict, list the conflict, state which source is used, and lower confidence where the conflict affects strategy.
- Data Health is a gate: if quote, filings/earnings, or technical data are insufficient for the requested objective, downgrade only that objective and state the gap rather than filling it with assumptions.

## Event Risk Check

Before any short-term or medium-term strategy, check and disclose:

- upcoming earnings date, guidance update, investor day, product launch, FDA/regulatory decision, litigation event, or other company-specific catalyst
- FOMC, CPI, PCE, jobs report, GDP, or other macro events inside the selected trading window
- unusual options implied volatility when available
- gap risk around after-hours or pre-market events

If a major event is inside the selected trading window, reduce confidence and avoid aggressive entry language unless the user explicitly asks for event-driven trading.

## Target Price Discipline

Do not output a single unsupported target price. Provide bear/base/bull target ranges with assumptions, time horizon, and confidence. Separate:

| Output | Required basis |
|---|---|
| Short-term tactical levels | Technical support/resistance, ATR, moving averages, volume, catalysts |
| Medium-term target | Earnings revisions, valuation multiple, sector trend, macro regime |
| Intrinsic value | DCF or normalized FCF/EPS assumptions plus sensitivity |
| Risk level | Downside level, stop logic, invalidation trigger, position sizing |

## Scoring Framework

Use scoring as a `Conviction / Setup Quality Score`, not a mechanical buy/sell rating. Data Health is a gate, not a score; if Data Health fails for the user's objective, do not produce an actionable conclusion for that objective.

| Module | Weight |
|---|---:|
| Macro and sector environment | 15 |
| Company fundamentals | 25 |
| Valuation | 20 |
| Technical setup | 20 |
| Risk and event profile | 15 |
| Catalyst/news quality | 5 |

| Score | Interpretation |
|---:|---|
| 80-100 | High-conviction candidate, still conditional on risk controls |
| 65-79 | Watchlist or conditional setup |
| 50-64 | Neutral / wait for better evidence |
| Below 50 | Avoid or low-priority |
| Data Health Fail | No actionable conclusion for the affected objective |

## Sub-Skill Contract

Sub-skills are independently callable Markdown report skills and also feed the main report.

When invoked by `stock-analysis`, each sub-skill must return a Markdown section that can be merged into the final report. Do not reduce it to a few bullets for `standard` or `full SOP`. Return:

- section title and one-sentence conclusion
- data timestamp and source dates
- 2-5 analytical paragraphs for `full SOP`; 1-3 for `standard`; compact bullets only for `basic`
- at least one table when the section is metric-heavy
- bullish interpretation, bearish interpretation, and neutral/uncertain evidence
- explicit implication for target price, short-term trading, medium-term strategy, long-term investment, earnings review, or risk
- missing data, low-confidence assumptions, and what would change the conclusion

When a user calls a sub-skill directly, produce a self-contained Markdown sub-report in the user's language. If ticker, objective, depth, or technical window is unclear and materially affects the answer, ask one concise clarification before analysis. End standalone sub-reports with `Not investment advice -- for your own research.`.

## Output Rules

- Match the user's language.
- Produce a professional Markdown or DOCX report according to the requested format.
- For `full SOP`, do not produce a short memo. Expand macro, sector, fundamentals, financial statements, valuation, technicals, risk, and debate into analytical paragraphs plus tables. Include assumptions, evidence dates, counterarguments, sensitivity, catalysts, and explicit invalidation levels.
- For `full SOP`, run a final report QA gate before answering: verify that Data Health, Evidence Ledger, macro, sector/peer, fundamentals, financials, valuation, technicals, risk plan, scoring, event risk, debate, bear/base/bull scenarios, final strategy, missing-data section, and disclaimer are present. If any required section cannot be completed, include it with a low-confidence or missing-data explanation rather than omitting it.
- Include daily and weekly chart images when API data and chart generation are available.
- For `basic`, give a shorter professional memo with enough data to be useful.
- Include exact data dates and source names when possible.
- Do not fabricate filings, estimates, analyst targets, or prices.
- Keep recommendations conditional: "if price holds X", "if earnings revisions improve", "if macro remains Risk-On".
- Include both short-term and medium-term strategy when the user asks for target price or trading plan.
