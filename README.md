<div align="right">

**English** · [中文](README.zh-CN.md)

</div>

# Stock Analyze Skills

![Skills](https://img.shields.io/badge/skills-18-blue)
![Personas](https://img.shields.io/badge/investor%20personas-8-success)
![Multi-Subagent Debate](https://img.shields.io/badge/debate-real%20multi--subagent-orange)
![Platforms](https://img.shields.io/badge/platforms-Claude%20Code%20·%20Desktop%20·%20Codex%20·%20Web-purple)
![Last Commit](https://img.shields.io/github/last-commit/Jelly13124/stock-analyze-skills)

A composable, institutional-grade equity research toolkit built as a suite of Claude Code Skills. Translates a multi-step analyst SOP into Markdown prompt files — with explicit numeric thresholds, real multi-subagent debate, and a panel of named investor personas you can converse with directly.

Works in Claude Code, Claude Desktop, Codex, and (with one extra zip step) Claude.ai web.

## What's New (2026-05)

- **8 investor persona skills** — Buffett · Munger · Graham · Lynch · Fisher · Wood · Druckenmiller · Burry. Invoke any one to converse in that investor's voice, or substitute them into the debate panel.
- **Real multi-subagent debate** — `stock-debate-panel` now dispatches one parallel `Agent` tool call per role per round in Claude Code. Asks the user for round count (1 / 2 / 3) and persona roster at call time. Falls back to single-LLM simulation only when the Agent tool isn't available, and labels the transcript as such.
- **`stock-sentiment-analysis`** added — 4-channel sentiment skill covering insider transactions (20%), news flow (25%), analyst EPS revisions (35%), and short interest / options positioning (20%).
- **Quantitative layer** added to financials, technical, valuation, and risk skills — explicit numeric thresholds (ROE > 15%, P/B < 1.5, FCF yield ≥ 15%, ADX, Z-score, Owner Earnings, vol-adjusted position cap, etc.) sit on top of the existing qualitative framework rather than replacing it.

## Skill Map

### Analytical Skills (10)

| Skill | Purpose |
|---|---|
| `stock-analysis` | Main orchestrator. Routes between depths (basic / standard / full SOP), invokes sub-skills, produces final Markdown or DOCX report. |
| `stock-macro-analysis` | Macro regime: Fed, rates, yield curve, CPI, jobs, VIX, liquidity. |
| `stock-sector-analysis` | Sector / industry / GICS, peer comparison, sector ETF strength. |
| `stock-company-fundamentals` | Business model, moat, TAM, pricing power, management, capital allocation. |
| `stock-financial-statement-analysis` | 10-K / 10-Q, income / balance / cash flow, earnings quality + new Quantitative Quick Filters. |
| `stock-valuation-analysis` | Relative + intrinsic valuation, DCF, Owner Earnings, Residual Income, WACC reference, scenario expected value. |
| `stock-technical-analysis` | Multi-timeframe trend, RSI / KDJ / MACD / BB / ATR / OBV + new 4-strategy Quantitative Layer (trend / momentum / mean-reversion / vol regime). |
| `stock-sentiment-analysis` | Insider trades, news flow, analyst EPS revisions, short interest, options positioning. |
| `stock-risk-position-analysis` | Position sizing, stop logic, R:R, sector cap, vol-adjusted single-stock cap. |
| `stock-debate-panel` | Real multi-subagent investment-committee debate (1 / 2 / 3 rounds). |

### Investor Persona Skills (8)

| Skill | Lens |
|---|---|
| `stock-investor-buffett` | Moat + owner earnings + margin of safety + circle of competence. |
| `stock-investor-munger` | ROIC + capital allocation + business predictability + quality > price. |
| `stock-investor-graham` | Net-Net + Graham number + dividend record + defensive tests. |
| `stock-investor-lynch` | GARP + PEG ≤ 1 + 6-category classification + invest-in-what-you-know. |
| `stock-investor-fisher` | 15-point checklist + scuttlebutt + R&D intensity + management depth. |
| `stock-investor-wood` | Disruptive innovation + R&D > 15% + 5-year exponential model + 25x terminal. |
| `stock-investor-druckenmiller` | Macro-first + concentrated + asymmetric R:R + momentum overlay. |
| `stock-investor-burry` | Deep value + FCF yield ≥ 15% + EV/EBIT < 6 + contrarian setup. |

Each persona has explicit Conflict And Pass Rules — a Buffett persona refusing to opine on a pre-profit biotech is correct behavior, not a failure to analyze. Persona scoring weights and thresholds are calibrated from `virattt/ai-hedge-fund/src/agents/<persona>.py` and translated into SKILL.md prompt form.

## How This Differs From ai-hedge-fund

| Aspect | This repo (Skill suite) | virattt/ai-hedge-fund |
|---|---|---|
| Form | Markdown SKILL.md prompts | Python + LangGraph framework |
| Customization | Edit a prompt file | Edit code + framework |
| Data-failure handling | Built-in Data Health gates and degradation rules | Crashes on missing fields |
| Qualitative + quantitative | Both layered (qualitative is authoritative; quantitative is a filter) | Quantitative-only |
| Persona-based debate | Yes — Claude Code Agent tool dispatches each persona as an independent subagent | Yes — LangGraph nodes |
| Backtesting | Not yet (planned) | Yes |
| Setup cost | `git clone` + copy folders | `pip install` + LLM API key + data API key |
| Final output | Professional Markdown / DOCX report | JSON signals + reasoning |

The two projects solve different problems. ai-hedge-fund is a programmable hedge-fund simulator. This repo is an analyst's prompt library that produces report-grade output and stays useful when data is incomplete.

## Quick Install

```powershell
git clone https://github.com/Jelly13124/stock-analyze-skills.git
cd stock-analyze-skills
```

### Claude Code

```powershell
Copy-Item .\stock-* "$env:USERPROFILE\.claude\skills\" -Recurse -Force
```

### Codex

```powershell
Copy-Item .\stock-* "$env:USERPROFILE\.codex\skills\" -Recurse -Force
```

### Claude Desktop

Import every `stock-*` folder in the Skills page. At minimum import `stock-analysis`; for full SOP reports import all sub-skills; for persona conversations or persona-driven debate, import the `stock-investor-*` folders too.

### Claude.ai Web

Build per-skill zips first:

```powershell
.\tools\build_claude_zips.ps1
```

Then upload the zips via the Skills UI. Detailed cross-platform notes in `docs/CROSS_PLATFORM.md`.

## API Key Setup

Create `key.txt` in the repo root:

```text
FINNHUB_API_KEY=your_finnhub_key
ALPHA_VANTAGE_API_KEY=your_alpha_vantage_key
FRED_API_KEY=your_fred_key
```

| Key | Purpose | Required? |
|---|---|---|
| `FINNHUB_API_KEY` | Quotes and some intraday data | Recommended |
| `ALPHA_VANTAGE_API_KEY` | Daily / weekly historical OHLCV | Recommended |
| `FRED_API_KEY` | Macro data (rates, VIX, credit spreads) | Optional |

Yahoo intraday charts work without any key — the data script uses Yahoo as the default intraday source.

Smoke test:

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

### Mode 1 — Full SOP report

```text
/stock-analysis NFLX full SOP md intraday target-price / short-term / medium-term / long-term / earnings-review
```

The orchestrator collects evidence, invokes every sub-skill in order, and assembles a single Markdown / DOCX report.

### Mode 2 — Single sub-skill

```text
/stock-valuation-analysis NFLX full target-price
/stock-technical-analysis NFLX intraday 5m KDJ RSI
/stock-sentiment-analysis NFLX 30-day window
/stock-company-fundamentals NFLX full fundamentals report
```

### Mode 3 — Persona conversation (new)

```text
/stock-investor-buffett
> What do you think of NVDA at current price?
```

The entire conversation runs in that investor's voice. Buffett will refuse to opine on names outside his circle of competence; Wood will reject mature dividend-payers as uninteresting. That's by design.

### Mode 4 — Real multi-subagent debate (new)

```text
/stock-debate-panel
```

The panel asks two things via its Request Gate:

1. **Rounds** — 1 (independent thesis only), 2 (adds rebuttals), or 3 (adds confidence revision)
2. **Personas** — default = generic Bull / Bear / Quant / Risk / Moderator; or specify investor swaps, e.g. "Buffett vs Wood + standard Quant / Risk / Moderator"

In Claude Code, each role is dispatched as an independent parallel `Agent` subagent — not the same LLM modelling multiple voices.

## Report Depth

| Depth | When | Output |
|---|---|---|
| `basic` | Quick view, first-pass opinion | Data Health, price snapshot, valuation snapshot, key risks |
| `standard` | Normal research request | Macro / sector / fundamentals / financials / valuation / technicals / sentiment / risk plan + bear / base / bull range |
| `full SOP` | Institutional-style report or explicit "full" request | Full 7-step SOP + Evidence Ledger + DCF / scenario math + charts + scoring + event risk + real multi-subagent debate (1-3 rounds) |

If the user enters a bare ticker, the main skill asks for depth, output format, objective, and technical window before generating anything.

## Repository Layout

```text
stock-analyze-skills/
├── stock-analysis/                       # main orchestrator
├── stock-macro-analysis/
├── stock-sector-analysis/
├── stock-company-fundamentals/
├── stock-financial-statement-analysis/
├── stock-valuation-analysis/
├── stock-technical-analysis/
├── stock-sentiment-analysis/             # new (2026-05)
├── stock-risk-position-analysis/
├── stock-debate-panel/                   # upgraded to real multi-subagent
├── stock-investor-buffett/               # new persona skills (2026-05)
│   └── references/persona-skill-template.md   # shared structural template
├── stock-investor-munger/
├── stock-investor-graham/
├── stock-investor-lynch/
├── stock-investor-fisher/
├── stock-investor-wood/
├── stock-investor-druckenmiller/
├── stock-investor-burry/
├── docs/                                 # cross-platform notes
├── tools/                                # zip builder for Claude.ai web
└── README.md / README.zh-CN.md
```

## Disclaimer

These skills produce research output, not investment advice. Every report this suite generates ends with `Not investment advice -- for your own research.` — that line is non-negotiable.
