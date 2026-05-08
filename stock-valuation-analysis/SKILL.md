---
name: stock-valuation-analysis
description: Use when stock analysis needs valuation, target price, intrinsic value, DCF, relative multiples, margin of safety, bear/base/bull cases, or upside/downside.
---

# Stock Valuation Analysis

## Overview

Estimate valuation with transparent assumptions. Do not present a target price unless the basis, horizon, sensitivity, and confidence are explicit.

## Standalone Markdown Report Mode

When called directly by a user, produce a self-contained Markdown valuation report in the user's language. If ticker, valuation horizon, output depth, or objective is unclear, ask one concise clarification first.

Use this structure:

1. `## Valuation Verdict`
2. `## Current Market Inputs`
3. `## Relative Valuation`
4. `## Intrinsic Valuation Or Scenario Math`
5. `## Bear/Base/Bull Target Price`
6. `## Sensitivity And Margin Of Safety`
7. `## What The Market Is Pricing In`
8. `## Valuation Risks And What Would Change The View`

For full-depth requests, include assumptions tables, sensitivity, share-count logic, net cash/debt, and separate tactical levels from fundamental target price.

## Data Failure and Low-Confidence Rules

- If analyst estimates are unavailable, omit estimate-based target price logic or mark it low confidence.
- If share count, market cap, enterprise value, net cash/debt, or diluted-share data conflicts, show the competing values and identify the valuation denominator used.
- If peers or historical multiples are unavailable, use scenario math with lower confidence rather than arbitrary multiples.
- If FCF, EPS, or margin data is missing, do not present a false-precision DCF; use range-based scenario valuation and disclose the gap.

## Required Output Elements

Every standalone report or main-report section must include a conclusion, source dates, at least one key table when evidence exists, bullish interpretation, bearish interpretation, uncertain/missing evidence, implications for valuation/strategy/risk, and missing data.

## Procedure

1. Define valuation horizon: short-term tactical, 6-12 month medium-term, or multi-year intrinsic value.
2. Collect current market inputs: price, shares, market cap, enterprise value, net cash/debt, analyst estimates, and peer multiples.
3. Relative valuation:
   - forward P/E for profitable companies
   - PEG for growth with credible EPS growth
   - EV/EBITDA for capital-intensive or EBITDA-focused peers
   - P/S for unprofitable growth companies
   - P/FCF and FCF yield for cash-generative companies
4. Intrinsic valuation when data supports it:
   - normalize revenue, margin, tax, CapEx, working capital, SBC, and FCF
   - choose WACC or discount rate and terminal growth/exit multiple
   - run sensitivity for WACC +/-1% and terminal growth +/-0.5% or multiple bands
5. Build bear/base/bull cases:
   - bear: lower growth/margin, multiple compression, adverse macro
   - base: consensus-like assumptions adjusted for evidence
   - bull: upside catalysts and sustainable multiple support
6. Calculate margin of safety versus current price and explain why the market may disagree.

## Rules

- Use ranges rather than false precision.
- Separate near-term technical levels from fundamental target price.
- If estimates are stale or unavailable, say so and use scenario math with lower confidence.
- Never use an arbitrary multiple without peer or historical justification.

## Output Contract

Return a Markdown report or report section with:

- bear/base/bull target range and horizon
- assumptions table
- current price, market cap/EV, share count, net cash/debt, and data dates when available
- relative valuation conclusion
- intrinsic valuation conclusion if applicable
- sensitivity table or clear sensitivity discussion
- what is already priced in versus what would create upside/downside
- margin of safety and confidence
- main valuation risks
- standalone disclaimer when called directly: `Not investment advice -- for your own research.`
