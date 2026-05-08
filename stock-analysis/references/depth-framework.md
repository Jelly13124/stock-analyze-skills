# Stock Analysis Depth Framework

Use this matrix after the request gate in `stock-analysis`. If depth, output format, objective, or technical window is unclear, ask before analysis. A bare ticker is vague and should trigger clarification, not a default report.

| Depth | Use when | Sub-skills | Debate | Output |
|---|---|---|---|---|
| basic | User wants quick view, ticker opinion, or a first-pass answer | valuation, technical, risk; add fundamentals only if needed | No | Professional memo in requested Markdown/DOCX format |
| standard | User asks for analysis/report/target price with a normal research depth | macro, sector, company fundamentals, financial statements, valuation, technical, risk | No formal debate; include one counter-thesis paragraph | Complete professional report in requested Markdown/DOCX format |
| full | User asks for complete SOP, deep report, institutional-style review, multi-agent debate, or highest depth | all sub-skills | Yes: bull, bear, quant, risk manager, moderator; 2-3 rounds | Institutional-style report with fixed schema, charts, scorecard, event risk, evidence ledger, scenarios, and debate appendix |

Minimum evidence by depth:

- basic: current quote, daily chart, weekly chart when available, valuation snapshot, 3-5 core risks.
- standard: add latest filing/earnings, sector/peer context, macro regime, financial trend, daily and weekly technical charts.
- full: add detailed assumptions, scenario valuation, sensitivity, catalysts calendar, invalidation points, daily/weekly/intraday charts when requested, event risk, scorecard, missing-data table, and multi-round debate. Financial statement, valuation, technical, and risk sections must contain enough explanation to support the final strategy, not only bullet summaries.

If data access is incomplete, downgrade only the data-dependent part and disclose the gap. Do not silently omit a required section.
