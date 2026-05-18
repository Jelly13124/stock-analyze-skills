# Company Fundamentals Module

> Internal module of the orchestrator. Loaded on demand by the
> orchestrator when the report needs this section, or when the user
> invokes it directly.
>
> Originally shipped as the standalone skill `stock-company-fundamentals` (pre-2026-05-merge).


## Overview

Assess business quality before valuation or technical timing. Use evidence from filings, earnings calls, company presentations, reputable news, and industry data.

For full-depth work, follow the bilingual institutional report logic in `../references/institutional-company-analysis-bilingual.md`. Read that reference before writing a standalone full company report or a `full SOP` company fundamentals section.

Language discipline: match the user's language. If the user asks in Chinese, use Chinese headings, Chinese table labels, and Chinese analysis. Keep only unavoidable tickers, company legal names, source names, accounting labels, and URLs in English. Translate key finance terms on first use.

## Standalone Markdown Report Mode

When called directly by a user, produce a self-contained Markdown sub-report in the user's language. If ticker, company, depth, or objective is unclear, ask one concise clarification first.

Use this structure:

1. `## Fundamental Verdict` / `## 基本面结论`
2. `## Investment Question` / `## 投资问题`
3. `## Asset And Business Overview` / `## 资产与业务概览`
4. `## Industry Structure And Market Context` / `## 行业结构与市场背景`
5. `## Business Model And Unit Economics` / `## 商业模式与单位经济模型`
6. `## Competitive Position And Moat` / `## 竞争位置与护城河`
7. `## Strategic Change And Catalysts` / `## 战略变化与催化剂`
8. `## Management, Capital Allocation, And Ownership` / `## 管理层、资本配置与所有权`
9. `## Financial Translation` / `## 财务转化`
10. `## Risks, Thesis Breakers, And Variant View` / `## 风险、论点破坏条件与差异化观点`
11. `## Implication For Valuation And Strategy` / `## 对估值和策略的含义`
12. `## Evidence Gaps` / `## 证据缺口`

For full-depth requests, write analytical paragraphs plus score tables. Avoid returning only a checklist. A full company report must answer why the company deserves a higher, lower, or unchanged multiple.

## Data Failure and Low-Confidence Rules

- If filings, investor presentations, or earnings calls are unavailable, use third-party descriptions only with low confidence and disclose the limitation.
- If TAM, market share, customer concentration, or pricing-power evidence is missing, mark the affected moat or growth score low confidence.
- If sources conflict, list the conflict and explain which dated source is weighted most heavily.
- Do not infer management quality, capital allocation skill, or customer demand without dated evidence.

## Required Output Elements

Every standalone report or main-report section must include a conclusion, source dates, at least one key table when evidence exists, bullish interpretation, bearish interpretation, uncertain/missing evidence, implications for valuation/strategy/risk, and missing data.

For `full SOP`, the company fundamentals section is incomplete unless it includes:

- core investment question
- business and segment map
- revenue model and unit economics
- industry structure and adoption cycle
- competitive position and substitutes
- strategic changes and catalysts
- management, ownership, and capital allocation
- financial translation into revenue, margin, cash flow, and valuation assumptions
- thesis breakers and variant view
- evidence gaps and confidence

## Procedure

1. Start with the investment question: what must be true for the stock to deserve a higher or lower multiple?
2. Define the business or key asset: segments, revenue drivers, geography, customer base, ownership, cyclicality, and recurring versus transactional revenue.
3. Map the industry structure: market size, adoption curve, pricing, distribution, supply constraints, regulation, and customer budget cycle.
4. Analyze business model and unit economics: volume, price, mix, churn, retention, utilization, take rate, advertising yield, margin, content/product cost, or other company-specific drivers.
5. Identify moat sources:
   - network effects
   - brand
   - patents/IP
   - switching costs
   - scale economics
   - regulatory barriers
   - data or distribution advantage
6. Evaluate competitive position: market share trend, peer concentration, pricing power, product differentiation, cost position, distribution, and substitution risk.
7. Review strategic changes and catalysts: product launches, pricing tiers, content/product investment, capacity expansion, regulatory shifts, acquisitions, spin-offs, or hidden asset monetization.
8. Review management and capital allocation: CEO tenure, execution record, incentive alignment, buybacks, dilution, M&A, ROIC/ROE trend, ownership/control, and whether value accrues to common shareholders.
9. Size the opportunity with TAM/SAM/SOM only when supported by credible dated sources; otherwise explain uncertainty.
10. Translate fundamentals into financial lines: revenue, gross margin, operating margin, cash flow, reinvestment needs, and valuation assumptions.
11. Identify thesis breakers and risks: product cycle, regulation, litigation, customer concentration, supply chain, margin pressure, balance sheet constraints, and valuation risk.

## Scoring

Use a 1-5 score for each category and explain the driver:

| Category | Score driver |
|---|---|
| Growth durability | revenue runway, customer demand, market expansion |
| Moat strength | defensibility, pricing power, switching cost |
| Management quality | execution, capital allocation, incentives |
| Competitive position | share gains/losses, peer differentiation |
| Risk profile | concentration, cyclicality, regulatory and execution risk |

## Output Contract

Return a Markdown report or report section with:

- one-sentence fundamental verdict
- one-sentence investment question
- 5-category scorecard
- business and segment map
- industry structure and adoption context
- business model and unit-economics driver table
- moat and competitive position summary
- business model, revenue drivers, customer/segment/geography exposure, and cyclicality
- catalyst table with expected timing and evidence source
- financial translation table connecting thesis drivers to revenue, margin, cash flow, and valuation
- thesis breaker checklist
- variant view: what the market likely believes versus what this analysis argues
- top catalysts and top risks
- implication for valuation assumptions
- evidence gaps and source dates
- standalone disclaimer when called directly: `Not investment advice -- for your own research.`
