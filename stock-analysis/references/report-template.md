# Professional Report Template

Use the user's language. This schema is the default structure for `standard` and `full SOP`. Per Adaptive Module Selection in `SKILL.md`, a section may be marked `n/a — <one-line reason>` when it genuinely does not apply to the ticker, or compressed when the user's objective de-emphasizes it — but never silently dropped. `basic` uses a trimmed subset.

This file is the **content schema** for the report — it lists every section and what each must contain. The report is always rendered as a single self-contained HTML file; `report-template.html` provides the matching HTML structure and styling.

For `full SOP`, the report should read like a professional research report, not a short memo. Each substantive section needs analytical paragraphs, dated evidence, tables where useful, uncertainty, what would change the view, and direct implications for the user's objective (target price, short-term trade, medium-term strategy, long-term investment, earnings review, or risk). Per-section length is governed by the Section Length Budget below — reach at least each section's floor, and treat Company Fundamentals and Financial Statement Review as the deepest, most detailed sections. Within a section's range, length scales with evidence weight; note when brevity is intentional. Do not pad past the ceiling.

Do not paste a short checklist as the final report. Fill the schema with complete analysis.

## Full SOP Minimum Gate

Before finalizing a `full SOP` report, verify:

- Data Health table covers quote, daily chart, weekly chart, requested intraday chart, financials/filings, macro, sector/peer, and news/transcript.
- Evidence Ledger has at least 10 items. If evidence is missing, include missing items as low-confidence or unavailable evidence.
- Recent Catalysts table covers the last 90 days (30 for `short-term trade`, 180 for `long-term`) with the 3–7 most material items, each dated and rated (Bull/Bear/Neutral, materiality High/Med/Low). Mark `n/a — no material catalysts` only when genuinely none exist.
- Ownership & Shareholder Structure covers float, institutional/insider %, top-holder concentration, share-class/voting, and structural short % of float (or `n/a — <reason>`).
- Valuation includes bear/base/bull assumptions, target ranges, sensitivity, share-count logic, net cash/debt when available, and margin of safety.
- Technical analysis includes weekly, daily, and requested intraday tables, chart paths, support/resistance, breakout/invalidation, ATR risk band, and reward/risk.
- Risk plan includes conservative, balanced, and aggressive frameworks when account size or risk style is unknown.
- Event Risk Check covers earnings/company catalysts and macro events inside the selected window.
- Debate includes 1-3 rounds, role confidence, rejected arguments, and moderator synthesis.
- Backtest validation sub-section is present under Technical (signal event-study on the strongest identified signal), unless no registered signal matched the technical thesis.
- Final strategy is split by short-term, medium-term, and long-term when requested.

## Rendering

The report is always a single self-contained HTML file. Use `report-template.html` for structure + styling (inline CSS, light/dark mode via `prefers-color-scheme`, an `@media print` stylesheet, and collapsible `<details>` sections for the Evidence Ledger and raw data). Embed chart PNGs via `<img>` with relative paths, or base64-inline them for a fully portable file. See "HTML formatting" in `SKILL.md` for the full rule list.

## Section Length Budget

Per-section word **targets** for the report body (prose only — tables, the HTML chrome, and chart images do not count). The ranges below are **guidelines, not hard caps**: each has a floor (write at least this much; below it the section is too thin) and an upper guideline (a comfortable depth, not a wall). The previous hard ceiling has been removed — now that the report is built incrementally via `Write` + `Edit` (see SKILL.md Workflow step 12), there is **no technical cap on total length**. **Company Fundamentals and Financial Statement Review carry the heaviest budget by design — they are the priority sections and must be the most detailed.** Going past a band when evidence warrants is fine; going past it with filler is still padding.

### full SOP

| Section | Target words | Notes |
|---|---:|---|
| Executive Summary | 200–350 | decision-first, no padding |
| Evidence Ledger | table only | ≥ 10 rows, no prose |
| **Recent Catalysts (last 90 days)** | 150–300 + table | 3–7 most material items via web search; spotlight, not exhaustive |
| Macro Regime | 250–400 | |
| Sector and Peer Comparison | 280–450 | |
| **Company Fundamentals** | **700–1100** | **deepest section** — business/segment map, unit economics, moat, management, capital allocation, thesis breakers |
| Ownership & Shareholder Structure | 200–350 + table | float / holders / short structure; cross-ref Sentiment for flow |
| **Financial Statement Review** | **600–950** | **second deepest** — revenue/margin/EPS trend, balance sheet, cash-flow quality, GAAP vs non-GAAP, dilution/SBC |
| Valuation Analysis | 450–700 | relative + DCF/scenario math |
| Technical Analysis (incl. Backtest Validation) | 400–650 | the backtest sub-section is part of this budget |
| Risk and Position Sizing | 350–550 | |
| Bear/Base/Bull Scenarios | 150–280 + table | mostly the scenario table |
| Conviction / Setup Quality Score | table + 120–220 rationale | |
| Event Risk Check | 150–300 | |
| Debate Summary | 400–750 | scales with round count (1/2/3) |
| Final Conditional Strategy | 280–450 | |
| Missing Data / Low Confidence | table + ≤ 120 | |

**full SOP body total: target ≈ 5,000–7,800 words for a typical full-evidence report; no hard ceiling.** Going well past 8,000 is fine when evidence genuinely supports it (deep-dive on a complex business, contested thesis, dense debate). Going well past 8,000 *without* matching evidence is padding — tighten lower-priority sections, never the two priority sections.

### standard and basic

| Depth | Body total target | Per-section guidance |
|---|---:|---|
| `standard` | ≈ 2,000–3,400 words | most sections 1–3 tight paragraphs; Company Fundamentals and Financial Statement Review still get the largest share (~1.5–2× a normal section) |
| `basic` | ≈ 500–950 words | compact bullets; prose only where it adds clarity |

A section may be `n/a — <one-line reason>` when it genuinely does not apply (per Adaptive Module Selection) — that does not count against the budget.

## Default Report Output Schema

```markdown
# Stock Analysis Report: {TICKER}

## Data Timestamp
- Report generated at:
- Market data timestamp:
- Filing/financial data date:
- Technical chart data window:
- Report depth:
- User objective:

## Data Health
| Item | Status | Source | Timestamp / Date | Notes |
|---|---|---|---|---|
| Quote |  |  |  |  |
| Daily chart / indicators |  |  |  |  |
| Weekly chart / indicators |  |  |  |  |
| Requested intraday chart / indicators |  |  |  | include source, data_quality, has_intraday_today, usable_for_report |
| Financials / filings |  |  |  |  |
| Earnings release / transcript |  |  |  |  |
| Macro data |  |  |  |  |
| Sector / peer data |  |  |  |  |
| News / catalysts |  |  |  |  |

## Executive Summary
- **Headline Verdict ({risk profile}):** {BUY / SMALL BUY / HOLD / SELL} · Composite Score {N}/100
- **Rationale:** {one-line, names the binding constraint, ≤30 words}
- Main bullish argument:
- Main bearish risk:
- Bear/base/bull target range:
- Strategy type:
- Confidence:
- Key invalidation:

## Recent Catalysts (last 90 days)

Spotlight of the 3–7 most material catalysts in the relevant window (default 90 days; 30 for `short-term trade`, 180 for `long-term`). Forward-looking events belong in **Event Risk Check** below, not here.

| Date | Catalyst | Direction | Materiality | Thesis Impact |
|---|---|---|---|---|
| YYYY-MM-DD | <one-line headline + source> | Bull / Bear / Neutral | High / Med / Low | <one line: how this changes the thesis> |

**Commentary** (≤200 words): cluster of related items, biggest single mover, what's still pending (announced but unproven), how this lines up with the bull / bear case.

If no material catalysts in the relevant window: `n/a — no material catalysts in the last 90 days; thesis rests on structural factors (see Company Fundamentals).`

## Evidence Ledger
| Claim | Evidence | Source | Date | Direction | Confidence |
|---|---|---|---|---|---|
|  |  |  |  | Bullish / Bearish / Neutral / Missing | High / Medium / Low |

## Macro Regime
- Regime label and confidence:
- Rates / yield curve:
- Credit / volatility / liquidity:
- SPY / QQQ / IWM trend:
- Implication for valuation multiple:
- Implication for position sizing and stop width:

## Sector and Peer Comparison
- Sector / industry:
- Sector ETF proxy:
- Relative strength versus SPY and sector ETF:
- Peer growth / margin / valuation / technical comparison:
- Sector catalysts and headwinds:
- Premium / discount justification:

## Company Fundamentals
- Core investment question:
- Business and segment map:
- Revenue model and unit economics:
- Industry structure and adoption cycle:
- Customer / segment / geography exposure:
- Moat, competitive position, and substitutes:
- Strategic changes and catalysts:
- Management, ownership, and capital allocation:
- Financial translation into revenue, margin, cash flow, and valuation assumptions:
- Thesis breakers and variant view:
- Evidence gaps and confidence:

## Ownership & Shareholder Structure
- Ownership composition (institutional % / insider % / retail residual):
- Float vs. shares outstanding; free float:
- Top-10 holders and concentration:
- Share classes and voting control (governance flag):
- Short interest as % of float; days-to-cover (structural; cross-ref Sentiment for the change/signal):
- Recent 13F / insider ownership changes (dated, web-sourced):
- Implication for risk (squeeze / liquidity → sizing caps) and fundamentals (governance / alignment):

## Financial Statement Review
- Reporting period and sources:
- Revenue / margin / EPS trend:
- Balance sheet and liquidity:
- Cash flow quality:
- Dilution / SBC / share-count considerations:
- GAAP versus non-GAAP quality:
- Guidance and transcript tone:

## Valuation Analysis
- Current market inputs:
- Relative valuation:
- Intrinsic valuation or scenario math:
- Bear/base/bull assumptions:
- Sensitivity:
- Margin of safety:
- What the market is pricing in:
- Target range and confidence:

## Technical Analysis
- Daily chart:
- Weekly chart:
- Requested intraday chart:
- Priority read: trend structure, relative strength, volume, support/resistance, indicator confirmation:
- Weekly trend table:
- Daily trend table:
- Intraday table when requested:
- RSI / KDJ / MACD / Bollinger Bands / ATR / OBV-volume:
- Support / resistance:
- Breakout trigger:
- Stop / invalidation:
- ATR risk band and reward/risk:

## Risk and Position Sizing
- Risk style assumption:
- Sizing mode: Kelly (total-capital) or fixed-amount:
- Kelly worktable (f*, fraction k, caps, stop-based size, binding constraint): when total capital given
- Recommended position (% of total capital + $ + shares):
- Conservative plan:
- Balanced plan:
- Aggressive plan:
- Entry / stop / target:
- Scale-in and scale-out:
- Event risk and gap-risk handling:
- Portfolio concentration constraints:
- Invalidation checklist:

## Bear/Base/Bull Scenarios
| Scenario | Target Range | Time Horizon | Key Assumptions | Confidence | Invalidation |
|---|---:|---|---|---|---|
| Bear |  |  |  |  |  |
| Base |  |  |  |  |  |
| Bull |  |  |  |  |  |

## Conviction / Setup Quality Score
Weights come from the risk-tolerance column of the SKILL.md Scoring Framework — state the profile used.

| Category | Weight (Conservative / Balanced / Aggressive) | Score 0-100 | Rationale |
|---|---:|---:|---|
| Macro and sector environment |  |  |  |
| Company fundamentals |  |  |  |
| Valuation (margin of safety) |  |  |  |
| Technical setup |  |  |  |
| Risk and event profile |  |  |  |
| Catalyst / news quality |  |  |  |
| Total | 100 |  |  |

Risk-tolerance sensitivity: __ Conservative / __ Balanced / __ Aggressive.

## Event Risk Check
- Upcoming earnings:
- Macro events inside the trading window:
- Company-specific events:
- Options IV / gap-risk notes:
- Effect on confidence:

## Debate Summary
Only include for `full SOP` or when requested.

### Round 1: Independent Theses
- Bull analyst:
- Bear analyst:
- Quant analyst:
- Risk manager:

### Round 2: Challenges
- Bull challenges:
- Bear challenges:
- Quant challenges:
- Risk manager challenges:

### Round 3: Revised Confidence
| Role | Confidence | What would change the view |
|---|---:|---|
| Bull |  |  |
| Bear |  |  |
| Quant |  |  |
| Risk manager |  |  |

### Moderator Synthesis
- Agreed facts:
- Rejected arguments:
- Unresolved disputes:
- Final target range:
- Strategy:
- Monitoring checklist:

## Final Conditional Strategy
- Short-term:
- Medium-term:
- Long-term:
- Watch levels:
- Stop / invalidation logic:
- What would change the view:
- Next 3-5 monitoring items:

## Missing Data / Low Confidence Areas
| Missing or conflicting item | Impact | Fallback used | Confidence effect |
|---|---|---|---|
|  |  |  |  |

## Disclaimer
Not investment advice -- for your own research.
```
