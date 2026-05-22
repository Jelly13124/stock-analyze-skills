<div align="right">

**English** · [中文](README.zh-CN.md)

</div>

# Stock Analyze Skills

![Skills](https://img.shields.io/badge/skills-1%20suite%2C%2018%20modules-blue)
![Personas](https://img.shields.io/badge/investor%20personas-8-success)
![Multi-Subagent Debate](https://img.shields.io/badge/debate-real%20multi--subagent-orange)
![Backtest](https://img.shields.io/badge/backtest-v1%20indicator%20%2B%20signal%20%2B%20persona-yellow)
![Platforms](https://img.shields.io/badge/platforms-Claude%20Code%20·%20Desktop%20·%20Codex%20·%20Web-purple)
![Last Commit](https://img.shields.io/github/last-commit/Jelly13124/stock-analyze-skills)

A composable, institutional-grade equity research toolkit built as a suite of Claude Code Skills. Translates a multi-step analyst SOP into Markdown prompt files — with explicit numeric thresholds, real multi-subagent debate, and a panel of named investor personas you can converse with directly.

Works in Claude Code, Claude Desktop, Cowork, Codex, and (with one extra zip step) Claude.ai web.

## What's New (2026-05)

- **HTML-only output** — Every report is now a single self-contained HTML file: charts embedded, light/dark mode, prints cleanly to PDF. The output-format question was removed — DOCX (slow, loses chart fidelity) and Markdown-as-a-report (no chart embedding) were dropped.
- **No API key needed — `yfinance` is the primary source** — With no key present, `yfinance` is the main data source for real-time quotes, OHLCV, and fundamentals (auto-installed on first run); Yahoo covers intraday. Web search fills non-price gaps (news, analyst revisions, catalyst dates) with a recency check. API keys are now fully optional.
- **Section Length Budget** — Per-section word budgets with a floor (genuinely detailed) and a ceiling (no padding). Company Fundamentals and Financial Statement Review carry the heaviest budget and are the most detailed sections of the report.
- **Persona-debate toggle** — The Request Gate's only persona question is one on/off toggle (full SOP only): persona-agent debate vs. generic Bull/Bear/Quant/Risk roles. Claude still auto-selects *which* personas from the ticker profile — the user is never asked to name them.
- **Single-skill consolidation** — The 18 previously separate `stock-*` skills are now 18 modules under one `stock-analysis` skill. Installation goes from "18 ZIP uploads" to one. The orchestrator's top-level `SKILL.md` is a router that lazily `Read`s modules from `stock-analysis/modules/` on demand, so token cost still scales with the work. See `MIGRATION_PLAN.md` for the consolidation design; the 18 originals remain recoverable from git history.
- **`stock-backtest` v1** (now `modules/backtest.md`) — Single-ticker backtest engine. Three modes: rule-based indicator strategies (KDJ golden cross, SMA50/200, RSI mean reversion, Bollinger lower bounce, MACD), signal event-study (does signal X predict positive forward returns at +1/+5/+10/+20/+60d?), and investor-persona allocation backtest (Lynch / Graham / Burry / Druckenmiller-lite). Reports in-sample vs out-of-sample metrics, deducts transaction costs, and refuses to label a strategy "works" if the out-of-sample evidence is weak. Buffett / Munger / Fisher / Wood personas return `data_insufficient` in v1 — they're deferred to v2 until the fundamentals layer covers owner earnings + ROIC time series.
- **8 investor persona skills** — Buffett · Munger · Graham · Lynch · Fisher · Wood · Druckenmiller · Burry. Invoke any one to converse in that investor's voice, or substitute them into the debate panel.
- **Real multi-subagent debate** — `modules/debate-panel.md` dispatches one parallel `Agent` tool call per role per round in Claude Code. Round count defaults to 2 for full SOP; the persona roster is auto-selected from the ticker profile. Falls back to single-LLM simulation only when the Agent tool isn't available, and labels the transcript as such.
- **`stock-sentiment-analysis`** added — 4-channel sentiment skill covering insider transactions (20%), news flow (25%), analyst EPS revisions (35%), and short interest / options positioning (20%).
- **Quantitative layer** added to the financials, technical, valuation, and risk modules — explicit numeric thresholds (ROE > 15%, P/B < 1.5, FCF yield ≥ 15%, ADX, Z-score, Owner Earnings, vol-adjusted position cap, etc.) sit on top of the existing qualitative framework rather than replacing it.

## Module Map

The suite is one skill (`stock-analysis`) containing 18 internal modules loaded on demand by the orchestrator.

### Analytical modules (10)

| Module | Purpose |
|---|---|
| `modules/macro.md` | Macro regime: Fed, rates, yield curve, CPI, jobs, VIX, liquidity. |
| `modules/sector.md` | Sector / industry / GICS, peer comparison, sector ETF strength. |
| `modules/company-fundamentals.md` | Business model, moat, TAM, pricing power, management, capital allocation. |
| `modules/financial-statements.md` | 10-K / 10-Q, income / balance / cash flow, earnings quality + Quantitative Quick Filters. |
| `modules/valuation.md` | Relative + intrinsic valuation, DCF, Owner Earnings, Residual Income, WACC reference, scenario expected value. |
| `modules/technical.md` | Multi-timeframe trend, RSI / KDJ / MACD / BB / ATR / OBV + 4-strategy Quantitative Layer. |
| `modules/sentiment.md` | Insider trades, news flow, analyst EPS revisions, short interest, options positioning. |
| `modules/risk-position.md` | Position sizing, stop logic, R:R, sector cap, vol-adjusted single-stock cap. |
| `modules/debate-panel.md` | Real multi-subagent investment-committee debate (1 / 2 / 3 rounds). |
| `modules/backtest.md` | Single-ticker historical backtest. Indicator strategies, signal event-study, or persona allocation. Outputs equity curve, Sharpe, MDD, trades CSV, in-sample / out-of-sample split, overfit diagnostics. |

### Investor persona modules (8)

| Module | Lens |
|---|---|
| `modules/investors/buffett.md` | Moat + owner earnings + margin of safety + circle of competence. |
| `modules/investors/munger.md` | ROIC + capital allocation + business predictability + quality > price. |
| `modules/investors/graham.md` | Net-Net + Graham number + dividend record + defensive tests. |
| `modules/investors/lynch.md` | GARP + PEG ≤ 1 + 6-category classification + invest-in-what-you-know. |
| `modules/investors/fisher.md` | 15-point checklist + scuttlebutt + R&D intensity + management depth. |
| `modules/investors/wood.md` | Disruptive innovation + R&D > 15% + 5-year exponential model + 25x terminal. |
| `modules/investors/druckenmiller.md` | Macro-first + concentrated + asymmetric R:R + momentum overlay. |
| `modules/investors/burry.md` | Deep value + FCF yield ≥ 15% + EV/EBIT < 6 + contrarian setup. |

Each persona has explicit Conflict And Pass Rules — a Buffett persona refusing to opine on a pre-profit biotech is correct behavior, not a failure to analyze. Persona scoring weights and thresholds are calibrated from `virattt/ai-hedge-fund/src/agents/<persona>.py` and translated into SKILL.md prompt form.

## How This Differs From ai-hedge-fund

| Aspect | This repo (Skill suite) | virattt/ai-hedge-fund |
|---|---|---|
| Form | Markdown SKILL.md prompts | Python + LangGraph framework |
| Customization | Edit a prompt file | Edit code + framework |
| Data-failure handling | Built-in Data Health gates and degradation rules | Crashes on missing fields |
| Qualitative + quantitative | Both layered (qualitative is authoritative; quantitative is a filter) | Quantitative-only |
| Persona-based debate | Yes — Claude Code Agent tool dispatches each persona as an independent subagent | Yes — LangGraph nodes |
| Backtesting | **v1 single-ticker (indicator / signal / persona) — `modules/backtest.md`** | Yes (multi-stock + walk-forward) |
| Setup cost | `git clone` + copy folders | `pip install` + LLM API key + data API key |
| Final output | Professional self-contained HTML report | JSON signals + reasoning |

The two projects solve different problems. ai-hedge-fund is a programmable hedge-fund simulator. This repo is an analyst's prompt library that produces report-grade output and stays useful when data is incomplete.

## Quick Install

```powershell
git clone https://github.com/Jelly13124/stock-analyze-skills.git
cd stock-analyze-skills
```

### Claude Code

```powershell
Copy-Item .\stock-analysis "$env:USERPROFILE\.claude\skills\" -Recurse -Force
```

### Codex

```powershell
Copy-Item .\stock-analysis "$env:USERPROFILE\.codex\skills\" -Recurse -Force
```

### Claude Desktop

Import the single `stock-analysis` folder in the Skills page. All 18 modules ship inside it.

### Claude.ai Web

Build one ZIP:

```powershell
.\tools\build_claude_zips.ps1
```

Then go to **Customize → Skills → + → Upload a skill** and upload `claude_web_zips/stock-analysis.zip`. Upload the `.zip` **file** itself (compressed-folder icon) — not the unzipped `stock-analysis` folder, which the uploader rejects with a *"must have a .skill, .zip, or .md extension"* error. A `.skill` file (a renamed ZIP of the same skill folder) works too. Detailed cross-platform notes in `docs/CROSS_PLATFORM.md`.

## API Keys (optional)

**No API key is required.** With no key present, the data scripts use `yfinance` as the primary source for real-time quotes, OHLCV, and fundamentals — it is auto-installed on first run — and Yahoo for intraday charts. Web search fills non-price gaps (news, analyst revisions, catalyst dates) with a recency check.

Adding keys is optional and only changes which provider is tried first. To use them, create `key.txt` in the repo root:

```text
FINNHUB_API_KEY=your_finnhub_key
ALPHA_VANTAGE_API_KEY=your_alpha_vantage_key
FRED_API_KEY=your_fred_key
```

| Key | Purpose | Required? |
|---|---|---|
| `FINNHUB_API_KEY` | Quotes and some intraday data | Optional |
| `ALPHA_VANTAGE_API_KEY` | Daily / weekly historical OHLCV | Optional |
| `FRED_API_KEY` | Macro data (rates, VIX, credit spreads) | Optional |

Smoke test (works with or without `key.txt` — omit `--key-file` if you have no keys):

```powershell
python .\stock-analysis\scripts\fetch_price_charts.py NFLX `
  --key-file .\key.txt --output-dir .\outputs\NFLX_test `
  --benchmark SPY --sector XLC `
  --intraday-window 1d --intraday-resolution 5
```

Success produces:

```text
outputs/NFLX_test/NFLX_technical_bundle.json
outputs/NFLX_test/NFLX_daily_chart.png
outputs/NFLX_test/NFLX_intraday_1d_5m_chart.png
```

## Usage

All five modes use the single `/stock-analysis` slash command — what changes is what you ask for. The orchestrator routes to the right modules.

### Mode 1 — Full SOP report

```text
/stock-analysis NFLX full SOP, objective target-price (or short-term / medium-term / long-term / earnings-review)
```

The orchestrator collects evidence, reads every required module in order, and assembles a single self-contained HTML report.

### Mode 2 — Single module

```text
/stock-analysis just the valuation module on NFLX, full depth, target price
/stock-analysis run the technical module on NFLX, intraday 5m KDJ RSI
/stock-analysis sentiment module only, NFLX, 30-day window
```

There is no separate slash command per module anymore — name the module in the prompt.

### Mode 3 — Persona conversation

```text
/stock-analysis analyze NVDA through Buffett's lens
```

The orchestrator loads `modules/investors/buffett.md` and runs the conversation in that voice. Buffett will refuse to opine on names outside his circle of competence; Wood will reject mature dividend-payers as uninteresting. That's by design.

### Mode 4 — Real multi-subagent debate

```text
/stock-analysis Buffett vs Wood debate on TSLA, 2 rounds
```

The orchestrator loads `modules/debate-panel.md` and dispatches each role as an independent parallel `Agent` subagent (in Claude Code; falls back to labeled single-LLM mode otherwise). Round count defaults to 2; Claude auto-selects the persona roster from the ticker profile.

### Mode 5 — Backtest

```text
/stock-analysis backtest NVDA, indicator kdj_golden_cross, 2020-01-01 to 2025-12-31
/stock-analysis backtest NVDA, signal kdj_golden_cross, 20-day forward horizon
/stock-analysis backtest MSFT, Lynch persona, quarterly, 2018 to 2025
```

Outputs equity-curve PNG, trades CSV, and a Markdown verdict with in-sample vs out-of-sample split, costs assumption, and an overfit diagnostic. Single ticker only; multi-stock portfolio + walk-forward optimization are v2.

## Report Depth

| Depth | When | Output |
|---|---|---|
| `basic` | Quick view, first-pass opinion | Data Health, price snapshot, valuation snapshot, key risks |
| `standard` | Normal research request | Macro / sector / fundamentals / financials / valuation / technicals / sentiment / risk plan + bear / base / bull range |
| `full SOP` | Institutional-style report or explicit "full" request | Full institutional workflow + Evidence Ledger + DCF / scenario math + charts + scoring + event risk + backtest validation + real multi-subagent debate (1-3 rounds) |

If the user enters a bare ticker, the main skill asks for depth, objective, position budget, and — for full SOP — debate mode (persona agents or generic roles) before generating anything. The report is always delivered as a self-contained HTML file; output format is not asked, and the technical window is derived from the objective.

## Repository Layout

```text
stock-analyze-skills/
├── stock-analysis/                       # the one skill that ships
│   ├── SKILL.md                          # router + workflow + SOP
│   ├── agents/openai.yaml
│   ├── modules/                          # internal modules, loaded on demand
│   │   ├── macro.md
│   │   ├── sector.md
│   │   ├── company-fundamentals.md
│   │   ├── financial-statements.md
│   │   ├── valuation.md
│   │   ├── technical.md
│   │   ├── sentiment.md
│   │   ├── risk-position.md
│   │   ├── debate-panel.md
│   │   ├── backtest.md
│   │   └── investors/
│   │       ├── buffett.md       munger.md       graham.md       lynch.md
│   │       └── fisher.md        wood.md         druckenmiller.md burry.md
│   ├── references/
│   │   ├── depth-framework.md
│   │   ├── report-template.md            # content schema + Section Length Budget
│   │   ├── report-template.html          # HTML structure + styling
│   │   ├── institutional-company-analysis-bilingual.md
│   │   ├── persona-skill-template.md
│   │   ├── strategy-registry.md
│   │   ├── persona-criteria-v1.md
│   │   ├── persona-criteria-v1.yaml
│   │   └── overfitting-checklist.md
│   └── scripts/
│       ├── data_provider.py
│       ├── fetch_price_charts.py
│       ├── backtest.py
│       └── web_prefetch_helper.md
├── docs/                                 # cross-platform notes
├── tools/                                # zip builder for Claude.ai web (single ZIP)
├── MIGRATION_PLAN.md                     # the 18→1 consolidation design
├── BACKTEST_DESIGN.md                    # backtest v1 design
└── README.md / README.zh-CN.md
```

## Disclaimer

These skills produce research output, not investment advice. Every report this suite generates ends with `Not investment advice -- for your own research.` — that line is non-negotiable.
