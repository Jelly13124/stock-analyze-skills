# Professional Report Template

Use the user's language. This schema is the default structure for `standard` and `full SOP`. Per Adaptive Module Selection in `SKILL.md`, a section may be marked `n/a — <one-line reason>` when it genuinely does not apply to the ticker, or compressed when the user's objective de-emphasizes it — but never silently dropped. `basic` uses a trimmed subset.

This schema is format-agnostic: the same 12-section content fills a Markdown report (`report-template.md` structure), an HTML report (`report-template.html` structure + styling), or a DOCX report.

For `full SOP`, the report should read like a professional research report, not a short memo. Each substantive section needs analytical paragraphs, dated evidence, tables where useful, uncertainty, what would change the view, and direct implications for the user's objective (target price, short-term trade, medium-term strategy, long-term investment, earnings review, or risk). Length scales with evidence weight — a clear-cut section can be one tight paragraph; note when brevity is intentional. Do not pad.

Do not paste a short checklist as the final report. Fill the schema with complete analysis.

## Full SOP Minimum Gate

Before finalizing a `full SOP` report, verify:

- Data Health table covers quote, daily chart, weekly chart, requested intraday chart, financials/filings, macro, sector/peer, and news/transcript.
- Evidence Ledger has at least 10 items. If evidence is missing, include missing items as low-confidence or unavailable evidence.
- Valuation includes bear/base/bull assumptions, target ranges, sensitivity, share-count logic, net cash/debt when available, and margin of safety.
- Technical analysis includes weekly, daily, and requested intraday tables, chart paths, support/resistance, breakout/invalidation, ATR risk band, and reward/risk.
- Risk plan includes conservative, balanced, and aggressive frameworks when account size or risk style is unknown.
- Event Risk Check covers earnings/company catalysts and macro events inside the selected window.
- Debate includes 1-3 rounds, role confidence, rejected arguments, and moderator synthesis.
- Backtest validation sub-section is present under Technical (signal event-study on the strongest identified signal), unless no registered signal matched the technical thesis.
- Final strategy is split by short-term, medium-term, and long-term when requested.

## Per-Format Notes

- **Markdown** — this file's schema, standard Markdown tables, relative `![](...)` image links to chart PNGs.
- **HTML** — use `report-template.html` for structure + styling (self-contained CSS, dark mode, print stylesheet, collapsible `<details>` sections). Same 12-section content.
- **DOCX** — DOCX Formatting Rules below.

## DOCX Formatting Rules

For DOCX output:

- Use a clean professional layout with consistent heading levels.
- Title page is optional for `basic` and `standard`, recommended for `full SOP`.
- Place data timestamp near the title.
- Keep tables narrow enough for Word page width.
- Add chart captions below images.
- Use bullets for executive summary, risk, and final strategy, but use paragraphs for analysis sections.
- Avoid dense walls of text.
- End with the required disclaimer.
- If visual verification is unavailable, state that visual verification was not run.

## Default Report Output Schema

```markdown
# Stock Analysis Report: {TICKER}

## Data Timestamp
- Report generated at:
- Market data timestamp:
- Filing/financial data date:
- Technical chart data window:
- Report depth:
- Output format:
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
- Overall view:
- Main bullish argument:
- Main bearish risk:
- Bear/base/bull target range:
- Strategy type:
- Confidence:
- Key invalidation:
- Score:

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
| Module | Weight | Score | Rationale |
|---|---:|---:|---|
| Macro and sector environment | 15 |  |  |
| Company fundamentals | 25 |  |  |
| Valuation | 20 |  |  |
| Technical setup | 20 |  |  |
| Risk and event profile | 15 |  |  |
| Catalyst/news quality | 5 |  |  |
| Total | 100 |  |  |

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
