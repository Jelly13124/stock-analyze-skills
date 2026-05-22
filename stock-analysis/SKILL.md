---
name: stock-analysis
description: Use when analyzing stocks, ETFs, tickers, target prices, trade strategy, valuation, DCF, technicals, KDJ/RSI/MACD/Bollinger Bands, support/resistance, breakout, earnings, 10-K/10-Q, fundamentals, sector/peer comparison, macro regime, sentiment, position sizing, stop loss, bull/bear debate, investment committee review, historical backtest (indicator strategy / signal validation / persona allocation), investor personas (Buffett/Munger/Graham/Lynch/Fisher/Wood/Druckenmiller/Burry), or HTML stock reports.
---

# Stock Analysis Suite

## Overview

Single-skill SOP-driven US stock analysis suite. This skill is the orchestrator. It contains 18 internal modules under `modules/` (9 analytical + 8 investor personas + 1 backtest). Modules are loaded on demand via the `Read` tool; do not preload modules that the current request does not need.

Use this as the main entry point for SOP-driven US stock analysis. It clarifies ambiguous requests, selects report depth, gathers current evidence, reads the relevant modules, and produces one professional self-contained HTML report. Modules can also be invoked directly when the user asks for a single sub-report ("just run the technical module on NVDA").

Always treat financial facts as time-sensitive. Fetch current market data, filings, earnings dates, guidance, news, analyst estimates, macro data, and technical prices when tools or browsing are available. If live data cannot be fetched, state the data limitation clearly and avoid pretending the report is current.

End user-facing reports with: `Not investment advice -- for your own research.`

## Data Sources

This skill supports Claude Code, Claude Desktop, Codex, Cowork, and Claude.ai web. **No API key is required to run an analysis.**

### Data source priority — quotes, OHLCV, fundamentals

Use this exact priority for prices and core financial data:

1. **Direct API (Finnhub / Alpha Vantage / Yahoo chart)** — used *only* when an API key is found. Before running `scripts/fetch_price_charts.py` or `scripts/backtest.py`, locate keys in this order: explicit user-provided path → `./key.txt` → `/mnt/user-data/uploads/key.txt` → `/mnt/data/key.txt`.
2. **yfinance — the PRIMARY source whenever there is no API key.** When no key is found, `yfinance` is the main data source for real-time stock prices, OHLCV history, and fundamentals — treat it as a normal, citable price source, not a degraded fallback. The data scripts call `ensure_yfinance()` at startup, which pip-installs `yfinance` automatically (with `--break-system-packages` / `--user` retries) if it is missing, so the no-key path works out of the box without you running pip. Disclose `provider: yfinance` in Data Health; do not warn the user that the analysis is unreliable just because no key was supplied.
3. **Prefetched web JSON** — last resort, used only in network-restricted environments (e.g. Claude.ai web, where Python cannot reach the network and yfinance returns `network_blocked`). See `scripts/web_prefetch_helper.md`: gather quote/OHLCV data with web search / web fetch, write JSON files to `/tmp/prefetched_data`, then re-run the same script command with `--output-dir auto`.

`scripts/data_provider.py` walks this chain automatically (`direct API → yfinance → prefetched`). Run the script normally first; only invoke the prefetch helper if Data Health shows `network_blocked` or `all_providers_failed`. Always disclose the `provider` and `source` fields in the final report, and mark `prefetched_web` as a secondary source with lower confidence for intraday precision.

### Filling missing data with web search

yfinance and the direct APIs cover prices, OHLCV, and core fundamentals. For information they do **not** cover — recent news flow, analyst estimate revisions, management guidance, upcoming earnings / catalyst dates, macro prints, regulatory or legal events — use the web search / web fetch tools.

**Recency gate — verify before you use.** Web search frequently surfaces stale pages. Before using any web-sourced figure, confirm it is current: check the publish/updated date of the source, prefer items dated within the relevant window (days for quotes and news, the latest reported quarter for estimates and fundamentals), and reject or down-weight anything undated or clearly old. State the date of every web-sourced fact in the report, and mark web-sourced data lower-confidence than API / yfinance data. Never present an outdated web figure as the current value — if you cannot confirm recency, say the data point is unverified rather than guessing.

## Request Gate

**Always confirm report parameters before producing an analytical report.** A bare ticker is not enough to start — ask the combined question below. The only request type that skips this gate is an explicit backtest request, which routes to its own gate.

**Technical window is never asked** — Claude derives it from the stated objective via the Technical Window Defaults table below. Asking would be redundant.

### The combined question (ask whenever the request is not fully specified)

A bare ticker (`NVDA`, `分析一下 DPZ`, `NVDA 怎么样`) specifies none of the parameters. Ask this one combined question before any analysis:

`Before I analyze <TICKER> (<one-line company identification, e.g. "Domino's Pizza">), please confirm:
(1) Depth — basic (quick snapshot) / standard (full analyst report) / full SOP (institutional-grade: debate, scoring, scenarios, backtest validation);
(2) Objective — target price / short-term trade / medium-term strategy / long-term investment / earnings review;
(3) Position & risk — (a) budget: a dollar amount or % of portfolio; (b) do you already hold <TICKER>, and if so your average cost basis; (c) risk tolerance — how big a paper drawdown on this position can you sit through? conservative (≈ up to 10%) / balanced (≈ 10-20%) / aggressive (≈ 25%+), or give your own number. Reply "skip" to any part you'd rather not give;
(4) Debate mode (full SOP only) — should the multi-agent debate use investor-persona agents (Buffett / Wood / Burry etc. — I auto-select the matchup) or generic Bull / Bear / Quant / Risk roles? Default is persona agents.
You can also reply with a one-liner like "standard, target price, $10k, hold at $9.50, OK with a ~15% drawdown" and I'll start straight away. The report is always delivered as an HTML file — format is not asked.`

Notes:
- Always identify the company by name in the question so the user knows the ticker resolved correctly (the screenshot failure mode: user typing `DPZ` and not being sure Claude knows it's Domino's Pizza).
- **Output format is not asked** — every report is a self-contained HTML file (see Output Format below).
- Backtest validation is **not** a separate question — it is automatically included for `full SOP`, and offered in the report footer for `basic`/`standard`.
- **Item (3) shapes the risk section.** Budget → concrete dollar sizing in `risk-position.md`. "Already hold it at $X" → the report frames the call as hold / add / trim / exit with unrealized P&L vs scenarios, not a fresh entry. Risk tolerance → selects the conservative/balanced/aggressive framework directly. Any part the user skips falls back to its default — see Position & Risk Profile Use below.
- **Item (4) is the only persona question, and only matters for `full SOP`** (basic/standard have no debate). It is a simple on/off toggle for *persona-based* debate — Claude still auto-selects *which* personas; the user is never asked to name them. If the user picks `full SOP` and skips item (4), default to persona agents. See the Persona Selection Table and Investor Persona Routing below.

### Partial specification

If the user already named some parameters ("full SOP on NVDA, target price"), ask only for the missing ones in one concise follow-up — never re-ask what they already gave.

### Fully specified — proceed

If the user supplied everything (depth + objective + position-&-risk-or-skip, plus debate mode when depth is `full SOP`), or replied with the one-liner, proceed directly to analysis. Do not ask again.

### Explicit backtest request

An explicit backtest request (`backtest NVDA`, `回测 NVDA KDJ 5 年`) skips the combined question and routes directly to `modules/backtest.md`'s Request Gate (mode / strategy or persona or signal / window / costs).

### Technical Window Defaults (by Objective)

When the user states an objective, derive the technical window automatically — don't ask:

| Objective | Daily/weekly charts | Intraday charts | `fetch_price_charts.py` flags |
|---|---|---|---|
| general overview (when objective left unspecified) | daily + weekly | no | (omit `--intraday-window`) |
| target price | daily + weekly | no | (omit) |
| short-term trade (< 1 week hold) | daily | yes | `--intraday-window 1d --intraday-resolution 5` |
| medium-term strategy (1–3 months) | daily + weekly | no | (omit) |
| long-term investment (> 1 year) | weekly + monthly-derived | no | (omit) |
| earnings review | daily | yes — last ~10 trading days | `--intraday-window 2w --intraday-resolution 15` |
| risk check | daily + weekly | no | (omit) |

If the user *explicitly* requests a window contrary to the table ("show me intraday for a long-term investment"), honor the explicit request and note the deviation. The table is the default, not a mandate.

### Position & Risk Profile Use

Item (3) of the Request Gate has three parts. Pass whatever the user gives into `modules/risk-position.md`:

**Budget** (dollar amount or % of portfolio) — the risk section produces concrete numbers:

- exact share count or notional based on the entry level
- dollar value at each scenario (bear / base / bull)
- dollar value at the stop level (max loss in $) and at the take-profit / target (max gain in $)
- R:R ratio with dollar context
- whether the position exceeds the recommended single-stock cap (default 5% of portfolio; warn if the budget implies higher concentration)

**Current holding + cost basis** — if the user already owns `<TICKER>`:

- frame the final strategy as **hold / add / trim / exit**, not a fresh entry
- compute unrealized P&L at the current price and at each bear/base/bull scenario, relative to the stated cost basis
- set the stop and invalidation against both the cost basis and the technical levels (distinguish "protect the gain" from "cap the loss")
- if the position is underwater, address the sunk-cost framing explicitly — the decision is whether the stock is a buy *today*, not whether it will "come back"

**Risk tolerance** — captured as the paper drawdown the user can sit through on this position (conservative ≈ ≤10%, balanced ≈ 10-20%, aggressive ≈ 25%+, or a custom number):

- map the band/number to a style row in `risk-position.md` and use that one style's risk-per-trade, single-stock cap, and minimum R:R — do not present all three variants
- feed the tolerable-drawdown number into the stop logic: the stop should sit within that band; if the volatility-correct stop is wider, size down or flag the name as too volatile for this tolerance
- for the final score, the band maps to a Scoring Framework weight column (≤10% → Conservative, 10-20% → Balanced, >20% → Aggressive)

If the user replied `skip` to a part, the risk section falls back to the default for that part: budget skipped → % terms only, no dollar sizing; holding skipped → assume a fresh entry; risk tolerance skipped → present conservative / balanced / aggressive variants.

### Persona Selection Table

This table is **internal** — the user is asked only the on/off toggle (Request Gate item 4), never *which* persona to pick. When persona-mode debate is on, Claude uses this table to **auto-select** which investor personas fill the Bull/Bear slots in the `full SOP` multi-agent debate; it also answers if the user later asks "which persona suits this name". Match by the **dominant ticker profile**, not by sector alone:

| Ticker profile | Suggest | Reasoning |
|---|---|---|
| Mature dividend payer (utilities, consumer staples, telecoms) | `graham` | Defensive value, dividend record, P/E and P/B discipline |
| Compounder with durable moat (premium consumer brand, fortress balance sheet) | `buffett` | Owner earnings, circle of competence, long-term hold |
| Disruptive innovator with R&D > 15% (AI, biotech, EV, fintech) | `wood` or `fisher` | Disruptive growth + exponential model (Wood) or 15-point growth quality (Fisher) |
| Quality growth at GARP price (mid-cap with 15–25% earnings growth, PEG ≤ 1) | `lynch` | GARP, 6-category classification |
| Deep value / cheap on hard numbers (FCF yield ≥ 15%, P/B < 1.5) | `burry` | FCF yield, balance sheet, contrarian |
| Macro-sensitive cyclical (commodity, bank, autos, industrial) | `druckenmiller` | Macro regime overlay, momentum, asymmetric R:R |
| Complex / multi-business conglomerate, capital allocator | `munger` | ROIC, capital allocation, multidisciplinary |
| Long-duration quality growth with patient management | `fisher` | 15-point checklist, scuttlebutt, R&D depth |
| Pre-revenue biotech or true unproven concept | none (suggest skip) | Most personas explicitly refuse pre-profit; respect Conflict Rules |

For ambiguous tickers, pick two contrasting personas (e.g. Buffett for the moat take vs Burry for the value-trap check) so the debate has genuine tension rather than forcing a single pick.

### Other gate triggers

- If the user explicitly asks for "complete", "full", "professional report", or "完整报告" — depth is known (`full SOP`); ask the combined question for the remaining items only.
- If the user asks for "quick" — depth is known (`basic`); ask the combined question for the remaining items only.
- If the user requests **technical analysis, K-line, RSI/KDJ, breakout, or short-term trading** — that implies depth and objective leanings, but still ask the combined question for whatever is unconfirmed. Never ask the technical window directly; derive it from the objective.
- If the user gives a position budget but no objective, still ask the objective in the combined question; do not silently default it.
- Use the user's latest language for the report.

See `references/depth-framework.md` for the depth matrix. For `full` reports, follow the Workflow + Adaptive Module Selection sections of this SKILL.md — they are the canonical SOP. (A longer prescriptive 7-step SOP file used to live at `references/Stock_Analysis_SOP_v1.0.md` but was removed for over-constraining Claude's judgment; the Workflow + per-module Standalone Mode + report-template now carry the SOP role.)

## Report Depth Matrix

| Depth | Use when | Required output |
|---|---|---|
| `basic` | Quick view, first-pass ticker opinion, simple risk check | Data Health, price/trend snapshot, key support/resistance, valuation snapshot, main risks, short conditional view. No full DCF and no formal debate. |
| `standard` | Normal stock analysis, target price, report, or strategy request | Macro, sector/peer, fundamentals, financial statement review, valuation, technicals, risk plan, bear/base/bull range, and one counter-thesis section. No formal multi-agent debate unless requested. |
| `full SOP` | Complete SOP, institutional-style report, professional report, multi-agent debate, or highest-depth request | Full institutional workflow per this SKILL.md (macro → sector → fundamentals → financials → valuation → technicals + backtest validation → sentiment → risk → debate), primary-source evidence, Evidence Ledger, relative valuation and DCF/scenario math, daily/weekly/requested intraday charts, sensitivity, catalysts, invalidation levels, scoring, event risk, and real multi-subagent debate (1-3 rounds) with an auto-selected investor-persona roster when the runtime supports the Agent tool; single-LLM-labeled fallback otherwise. |

## Output Format

**Every report is delivered as a single self-contained HTML file. There is no format question** — HTML is always used. HTML embeds charts cleanly, opens in any browser, is plain-text and LLM-friendly, prints to PDF via the browser, and renders as an artifact in Cowork. DOCX was dropped (slow to generate, loses chart fidelity, hard for LLMs to re-read) and Markdown was dropped as a *report* format (no chart embedding, weaker layout). If a user explicitly insists on DOCX or Markdown you may still produce it, but never offer the choice or ask.

(In-chat Markdown is still fine for a quick standalone single-module answer — "just run the technical module on NVDA" — since that is a conversational sub-look, not a generated report file.)

### HTML formatting

Use `references/report-template.html` as the structural and styling reference, and `references/report-template.md` as the content schema (section list + what each section must contain). Key rules:

- Single self-contained `.html` file (CSS inline in `<style>`, no external CDN), opens in any browser
- Embed chart PNGs via `<img src="NVDA_daily_chart.png" alt="...">` with paths relative to the HTML file's location, OR base64-encode them inline for a fully portable single file
- Use semantic HTML (`<h1>`, `<h2>`, `<table>`, `<details>`/`<summary>` for collapsible Evidence Ledger / raw data)
- Light + dark CSS via `prefers-color-scheme` media query
- Include a `@media print` stylesheet so the HTML prints to PDF cleanly via the browser
- Save the final `.html` to the user's workspace folder and share a `computer://` link
- For Cowork users: in addition to saving the file, render it as an artifact via the artifact tool so the report is live inside the chat

## Module Routing

Modules are internal instruction files in `modules/`. Load them with the `Read` tool only when the current request requires them. Do NOT inline the contents of every module into your context — the whole point of the router pattern is to keep token cost proportional to the work.

### Analytical modules

| Trigger | Module | Required for depth |
|---|---|---|
| Macro regime, Fed, rates, yield curve, CPI, VIX, liquidity | `modules/macro.md` | standard, full SOP |
| Sector / GICS / peer comparison / sector ETF strength | `modules/sector.md` | standard, full SOP |
| Business model, moat, TAM, management, capital allocation | `modules/company-fundamentals.md` | standard, full SOP |
| 10-K / 10-Q, income / balance / cash flow, earnings quality | `modules/financial-statements.md` | standard, full SOP |
| Valuation, DCF, target price, intrinsic value, multiples | `modules/valuation.md` | all depths |
| Charts, KDJ, RSI, MACD, BB, ATR, support/resistance, trend | `modules/technical.md` | all depths |
| Insider trades, news flow, EPS revisions, short interest | `modules/sentiment.md` | standard, full SOP (skip basic unless asked) |
| Position sizing, stop loss, R:R, event risk, sector cap | `modules/risk-position.md` | all depths |
| Bull/bear debate, investment committee, persona showdown | `modules/debate-panel.md` | full SOP, or when explicitly requested |
| Backtest signal-validation (validates technical thesis automatically) | `modules/backtest.md` (signal mode) | full SOP default; opt-in for standard |
| Backtest indicator strategy / persona allocation (full equity curve) | `modules/backtest.md` (indicator/persona mode) | only when user explicitly asks for a backtest |

### Investor persona modules

Persona modules are NOT loaded by depth, and the user is never asked to pick one. Load `modules/investors/<persona>.md` only when (a) the user explicitly names that persona, (b) the user asks for "X's lens on <TICKER>", or (c) a debate runs — for `full SOP` the debate auto-selects its persona roster via the Persona Selection Table, and the user may also explicitly request a substitution.

| Persona | Module |
|---|---|
| Warren Buffett | `modules/investors/buffett.md` |
| Charlie Munger | `modules/investors/munger.md` |
| Benjamin Graham | `modules/investors/graham.md` |
| Peter Lynch | `modules/investors/lynch.md` |
| Phil Fisher | `modules/investors/fisher.md` |
| Cathie Wood | `modules/investors/wood.md` |
| Stanley Druckenmiller | `modules/investors/druckenmiller.md` |
| Michael Burry | `modules/investors/burry.md` |

All eight personas share the structural contract in `references/persona-skill-template.md` — Read that first if it has not already been consumed in this session.

When a persona is dispatched as a debate subagent per the Subagent Dispatch Protocol in `modules/debate-panel.md`, copy the FULL content of that persona's module inline into the subagent prompt. Do NOT rely on the subagent loading the file itself.

## Workflow

1. Resolve the ticker, exchange, company name, sector, industry, and report language.
2. Confirm depth, objective, position & risk profile (budget, current holding + cost basis, risk tolerance), and (for `full SOP`) debate mode via the Request Gate. Derive the technical window from the objective via the Technical Window Defaults table — do not ask the user. Output format is not asked — the report is always HTML.
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
   - **Add intraday flags only when the Technical Window Defaults table says so for the user's objective.** Don't add intraday for `target price`, `medium-term`, `long-term`, `general overview`, or `risk check`. Do add for `short-term trade` (`--intraday-window 1d --intraday-resolution 5`) and `earnings review` (`--intraday-window 2w --intraday-resolution 15`). Honor explicit user overrides if they ask for a window outside the default.
   - Intraday source defaults to Yahoo chart current-session bars because that is sufficient for K-line/KDJ/volume analysis and avoids repeated failures from realtime-only candle endpoints. Use `--intraday-source auto` or `--intraday-source finnhub` only when the user explicitly asks for a realtime-capable candle source.
   - The script uses `scripts/data_provider.py` to pick the data source in priority order — direct API (only if a key is present), then `yfinance` (the no-key primary), then prefetched web JSON — and then generates artifacts only: quote status, daily/weekly OHLCV-derived indicators, optional intraday candle-derived indicators, daily/weekly/intraday PNG charts, benchmark/sector relative strength data, volume ratios, support/resistance distances, KDJ cross events, indicator metadata, and a `technical_data_summary`.
   - **No API key is required to get data.** When no key is present, `yfinance` is the **primary** source for real-time quotes, OHLCV, and fundamentals (not a degraded fallback), and Yahoo chart covers intraday. The data scripts call `ensure_yfinance()` at startup, which pip-installs `yfinance` automatically (one attempt, with `--break-system-packages` / `--user` retries) if it isn't already present — so the no-key path works without you running pip yourself. If the auto-install fails (no network), the script falls back to direct API or the prefetch helper and says so in stderr. Do not assume a missing key means the analysis can't run, and do not flag a yfinance-sourced report as low-confidence merely because no key was used.
   - KDJ values are computed from OHLCV high/low/close bars. Daily/weekly KDJ is completed-bar close-based. Intraday KDJ is candle-based from the selected intraday source. Always describe `intraday.source`, `data_quality`, `has_intraday_today`, `usable_for_report`, latest bar timestamp, resolution, and window. Do not frame `is_realtime=false` as a data failure when `usable_for_report=true`; simply state that the chart is current-session or delayed bars rather than exchange-direct realtime.
   - Charts should include candlesticks, volume, KDJ, support/resistance lines, and detected KDJ golden/death crosses when data is available.
   - The data script must not make recommendations or label a setup bullish/bearish. Modules interpret its data by priority: trend structure, relative strength, volume, support/resistance, then indicator confirmation.
   - If chart generation fails, disclose the failure in Data Health and do not invent chart readings.
5. **Read the modules required by depth using the Module Routing table above.** For each loaded module, apply its methodology to produce the corresponding section of the report. The module's "Standalone Markdown Report Mode" structure becomes the report section structure when invoked by the orchestrator. **The "Required for depth" column is a default starting point, not a hard mandate** — see Adaptive Module Selection below. The defaults are:
   - `basic` — `modules/valuation.md`, `modules/technical.md`, `modules/risk-position.md`. Add `modules/company-fundamentals.md` if business model materially drives the thesis.
   - `standard` — add `modules/macro.md`, `modules/sector.md`, `modules/company-fundamentals.md`, `modules/financial-statements.md`, `modules/sentiment.md`.
   - `full SOP` — all of the above plus `modules/debate-panel.md` plus the backtest signal-validation step (6).
6. **Backtest signal-validation (full SOP default, opt-in for standard).** After the Technical section identifies the strongest actionable signal (KDJ golden cross / SMA50-200 cross / RSI mean reversion / BB lower bounce / MACD signal cross / RSI oversold / volume spike / new 52w high / BB squeeze breakout), Read `modules/backtest.md` and run:
   ```
   scripts/backtest.py <TICKER> --mode signal --signal <identified_signal> --start <5y-ago> --end <today> --key-file <key> --output-dir <out> --no-charts
   ```
   Read the resulting bundle's `signal_stats` block and surface it as a **Backtest Validation** sub-section under Technical (not a standalone chapter). One short table with hit rate / mean return / t-stat at +5d, +20d, +60d horizons + baseline comparison + the `significant_at_p05` flag. If the technical thesis doesn't map to a registered signal, skip this step and note "no registered signal matches the technical thesis; backtest validation not run". Do not run more than one signal validation per report unless the user asks.
7. For `full SOP` AND when the `Agent` tool is available, run the debate as real parallel subagents per the Subagent Dispatch Protocol in `modules/debate-panel.md`. **Debate mode comes from Request Gate item (4):** if persona mode is on (the default), the Bull/Bear slots are investor personas and **Claude auto-selects which ones** via the Persona Selection Table — copy that persona module's content inline into each subagent prompt; if persona mode is off, run the debate with generic Bull / Bear / Quant / Risk / Moderator roles. Round count defaults to 2 for `full SOP`. The panel never asks the user which personas to use. Honor an explicit user override of personas or rounds if one is given.
8. **Persona lens (only on explicit user request).** The SOP does not auto-run a standalone persona overlay — in the automatic flow, personas appear only inside the Step 7 debate. If the user explicitly asks for a named persona's take ("add Buffett's view"), Read `modules/investors/<persona>.md` plus `references/persona-skill-template.md` and produce a Persona Lens appendix using the same evidence ledger, with scoring breakdown + conviction band. Respect Conflict And Pass Rules — if the persona refuses to opine, that's correct behavior.
9. For `full SOP`, the company-fundamentals section must follow `references/institutional-company-analysis-bilingual.md` and include investment question, business/segment map, unit economics, industry structure, competitive position, catalysts, management/capital allocation, financial translation, thesis breakers, and evidence gaps.
10. For explicit backtest requests (not the auto signal-validation in step 6), Read `modules/backtest.md` and run `scripts/backtest.py` with whichever mode the user picked. The backtest module enforces in-sample / out-of-sample reporting, transaction-cost honesty, and overfit checks — do not skip those.
11. Build an evidence ledger: bullish facts, bearish facts, uncertain/missing data, catalysts, invalidation points.
12. Produce the report as a single self-contained HTML file, using `references/report-template.html` for structure + styling and `references/report-template.md` for the content schema and the Section Length Budget. Save it to the user's workspace folder and share a `computer://` link.

## Adaptive Module Selection

The Module Routing "Required for depth" column is the **default** starting set, not a fixed list. Adjust based on:

- **The user's stated objective.** If the user explicitly asked for a target price, weight `valuation.md` and `sentiment.md` heavier and compress `macro.md` to a one-paragraph context check. If the user asked for a swing trade, weight `technical.md` and `risk-position.md` and compress fundamentals to a one-paragraph backdrop. If the user asked for an earnings review, expand `financial-statements.md` and `sentiment.md` (especially analyst revisions), and compress macro/sector.
- **Genuine non-applicability.** If a module truly doesn't apply to this ticker (e.g., sentiment for a delisted-on-foreign-exchange micro-cap with no analyst coverage; macro for a market-neutral pair the user is rotating into), mark that section as **n/a — <one-line reason>** instead of writing padded low-confidence content. Do not skip silently; document the skip.
- **Data Health.** If a module's required data isn't fetchable, downgrade to a brief acknowledgement with the gap noted, not a full prose section pretending data exists.

When in doubt, lean toward including a section briefly rather than skipping. The bar for skipping is "this section would be misleading or pointless if written", not "I don't have lots to say".

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

Score each of the six categories 0–100 on its own evidence, then take the weighted average for the final `/100`. **The weights depend on the user's risk tolerance (Request Gate item 3c)** — the same stock is a different-quality setup for a conservative vs. an aggressive investor, so the final score moves with the profile. Use the column matching the stated risk tolerance — if the user gave a tolerable-drawdown number rather than a label, map it (≤10% → Conservative, 10-20% → Balanced, >20% → Aggressive). If risk tolerance was skipped entirely, use `Balanced`.

| Category | Conservative | Balanced | Aggressive |
|---|---:|---:|---:|
| Macro and sector environment | 15 | 15 | 15 |
| Company fundamentals | 30 | 25 | 20 |
| Valuation (margin of safety) | 25 | 20 | 15 |
| Technical setup | 10 | 20 | 28 |
| Risk and event profile | 18 | 15 | 12 |
| Catalyst / news quality | 2 | 5 | 10 |
| **Total** | **100** | **100** | **100** |

The category scores (0–100) are identical across profiles — only the weights change. A conservative profile rewards durable fundamentals and a valuation cushion and penalizes thin risk buffers; an aggressive profile rewards technical momentum and catalyst optionality and tolerates a richer valuation; balanced is the neutral default.

| Score | Interpretation |
|---:|---|
| 80-100 | High-conviction candidate, still conditional on risk controls |
| 65-79 | Watchlist or conditional setup |
| 50-64 | Neutral / wait for better evidence |
| Below 50 | Avoid or low-priority |
| Data Health Fail | No actionable conclusion for the affected objective |

Always state which risk-tolerance column was used. When the profile materially changes the verdict, also show the score under the other two profiles so the sensitivity is visible — e.g. `Conviction 78 (Balanced) — 71 Conservative / 84 Aggressive; the spread is the stretched valuation`.

## Module Contract

Modules are loaded on demand by the orchestrator and can also be invoked directly by user request ("just run the technical module on NVDA"). When loaded by the orchestrator, each module returns a Markdown section that can be merged into the final report. When invoked standalone, the module produces a self-contained Markdown sub-report in the user's language.

### Required elements

- section title and one-sentence conclusion
- data timestamp and source dates
- at least one table when the section is metric-heavy
- bullish interpretation, bearish interpretation, and neutral/uncertain evidence
- explicit implication for the user's stated objective (target price / short-term trade / medium-term strategy / long-term investment / earnings review / risk)
- missing data, low-confidence assumptions, and what would change the conclusion

### Length

Length is governed by the **Section Length Budget** table in `references/report-template.md` — per-section word ranges with both a floor (so each section is genuinely detailed) and a ceiling (so it doesn't run away). Read that table before writing a `full SOP` or `standard` report. Two principles sit on top of the budget:

- **Company Fundamentals and Financial Statement Review are the priority sections.** They carry the largest word budget and must be the most detailed in the report — this is where the analytical work shows. Never compress them to hit an overall length target; compress lower-priority sections instead.
- **Within a section's range, length still scales with evidence weight.** Always reach at least the floor. If a section is genuinely clear-cut, land in the lower half of its range and say so explicitly ("Macro context is unambiguous risk-on; no further analysis warranted") so the reader doesn't assume Claude was lazy. Exceeding the ceiling means you are padding — a failure mode, not thoroughness.

For `basic`, compact bullets are usually right; apply the budget's `basic` global target.

### Standalone direct-invocation

When a user calls a module directly, produce a self-contained Markdown sub-report in the user's language. If ticker, objective, depth, or technical window is unclear and materially affects the answer, ask one concise clarification before analysis. End standalone sub-reports with `Not investment advice -- for your own research.`.

## Investor Persona Routing

The eight `modules/investors/*.md` files are NOT loaded automatically by report depth, and the Request Gate never asks the user to choose a persona. Personas surface in three ways:

1. **Solo persona conversation (user-initiated)** — when the user names a persona ("analyze NVDA through Buffett's lens"), Read only `modules/investors/<persona>.md` plus `references/persona-skill-template.md`. The entire conversation runs in that persona's voice. Output the persona's standalone Markdown report.
2. **Persona second opinion (user-initiated)** — after a `standard` or `full SOP` report, the user may ask for a single persona's read on the same name. Read the persona module against the same evidence ledger; surface its scoring breakdown and conviction band as an appendix.
3. **Persona as debate participant (`full SOP`, controlled by Request Gate item 4)** — when persona mode is on (the gate's default), the `full SOP` debate fills its Bull/Bear slots with investor personas; Claude **auto-selects which ones** via the Persona Selection Table — the user is asked only the on/off toggle, never which personas. When persona mode is off, the debate uses generic Bull / Bear / Quant / Risk / Moderator roles and no persona module is loaded. If the user explicitly requests a matchup ("Buffett vs Wood"), honor that. Read `modules/debate-panel.md` first, then dispatch each persona as a parallel subagent per the Subagent Dispatch Protocol with the persona module content copied inline into the subagent prompt.

Each persona has explicit Conflict And Pass Rules; respect them — a Buffett persona refusing to opine on a pre-profit biotech is correct behavior, not a failure to analyze.

## Backtest Routing

When the user requests a backtest:

1. Read `modules/backtest.md` for the request gate, output schema, and verdict rules.
2. Confirm mode (indicator / signal / persona), strategy or persona or signal name, window, costs assumption, and benchmark.
3. Run `scripts/backtest.py` with the agreed parameters.
4. Read the resulting `{TICKER}_backtest_bundle.json` and the trades CSV.
5. Produce the Standalone Backtest Report per the structure in `modules/backtest.md`. Apply all hard rules: report both in-sample and out-of-sample metrics, quote costs in the verdict, refuse to call a strategy "works" if `degradation_ratio < 0.4`.

For v1, supported persona backtests are Lynch / Graham / Burry / Druckenmiller-lite. Buffett / Munger / Fisher / Wood are deferred to v2 — the script returns exit code 6 with an explanation, and the orchestrator must not silently substitute.

See `references/strategy-registry.md`, `references/persona-criteria-v1.md`, and `references/overfitting-checklist.md` for the supporting rule sets.

## Output Rules

- Match the user's language.
- Produce a professional self-contained HTML report. Use `references/report-template.html` for structure + styling and `references/report-template.md` for the content schema and the Section Length Budget. Save the `.html` to the user's workspace folder and share a `computer://` link.
- For `full SOP`, do not produce a short memo unless the evidence is genuinely thin. Default is rich analytical paragraphs across macro, sector, fundamentals, financial statements, valuation, technicals (with backtest validation sub-section), risk, debate. Include assumptions, evidence dates, counterarguments, sensitivity, catalysts, and explicit invalidation levels.
- For `full SOP`, run a final report QA gate before answering. Expected sections: Data Health, Evidence Ledger, macro, sector/peer, fundamentals, financials, valuation, technicals + backtest validation, risk plan, scoring, event risk, debate, bear/base/bull scenarios, final strategy, missing-data section, and disclaimer. **A section may be marked `n/a — <reason>` (one line) when it genuinely doesn't apply to this ticker** (e.g., relative-valuation peers for a unique business; macro regime for a market-neutral position). The QA gate accepts `n/a` with a reason as a valid completion state — it does not accept silent omission.
- Include daily and weekly chart images when API data and chart generation are available.
- For `basic`, give a shorter professional report with enough data to be useful. End it with the footer suggesting upgrades (full SOP / backtest / persona lens / different technical window).
- Include exact data dates and source names when possible.
- Do not fabricate filings, estimates, analyst targets, or prices.
- Keep recommendations conditional: "if price holds X", "if earnings revisions improve", "if macro remains Risk-On".
- Include both short-term and medium-term strategy when the user asks for target price or trading plan.
- **Avoid padding.** A short, sharp section that says exactly what's true beats a long section with low-confidence filler. Note explicitly when brevity is intentional ("evidence is unambiguous" / "no further nuance to add").
