# Stock Analysis Depth Framework

Use this matrix together with the Request Gate in `stock-analysis/SKILL.md`. The Request Gate always asks the combined question (depth / objective / position & risk profile / debate mode) before producing a report — including for a bare ticker — unless the request is already fully specified or is an explicit backtest request. Output format is not asked — every report is a self-contained HTML file. Technical window is derived from the objective, never asked. The debate-mode item is an on/off toggle for persona-based debate (`full SOP` only); Claude still auto-selects *which* personas — the user is never asked to name them.

| Depth | Use when | Modules | Debate | Output |
|---|---|---|---|---|
| basic | Quick view, ticker opinion, or a first-pass answer | valuation, technical, risk; add fundamentals if the business model drives the thesis | No | Professional self-contained HTML report, with a footer offering upgrades |
| standard | User asks for analysis/report/target price with a normal research depth | macro, sector, company fundamentals, financial statements, valuation, technical, sentiment, ownership structure, risk | No formal debate; include one counter-thesis paragraph | Complete professional self-contained HTML report |
| full | User asks for complete SOP, deep report, institutional-style review, multi-agent debate, or highest depth | all modules (+ options-gamma when optionable) + backtest signal-validation | Yes: bull, bear, quant, risk manager, moderator; 1-3 rounds | Institutional-style HTML report with the report-template schema, charts, scorecard, event risk, evidence ledger, scenarios, backtest validation, and a debate appendix — Bull/Bear slots use an auto-selected investor-persona roster or generic roles, per Request Gate item 4 |

Minimum evidence by depth:

- basic: current quote, daily chart, weekly chart when available, valuation snapshot, 3-5 core risks.
- standard: add latest filing/earnings, sector/peer context, macro regime, financial trend, daily and weekly technical charts.
- full: add detailed assumptions, scenario valuation, sensitivity, catalysts calendar, invalidation points, daily/weekly/intraday charts when requested, event risk, scorecard, missing-data table, and multi-round debate. Financial statement, valuation, technical, and risk sections must contain enough explanation to support the final strategy, not only bullet summaries.

If data access is incomplete, downgrade only the data-dependent part and disclose the gap. A section may be marked `n/a — <one-line reason>` when it genuinely does not apply to the ticker (per Adaptive Module Selection in `SKILL.md`) — but never silently omit a section.
