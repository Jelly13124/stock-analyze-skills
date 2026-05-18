# Valuation Module

> Internal module of the orchestrator. Loaded on demand by the
> orchestrator when the report needs this section, or when the user
> invokes it directly.
>
> Originally shipped as the standalone skill `stock-valuation-analysis` (pre-2026-05-merge).


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

## WACC Reference Table

When discount rate must be set without a company-specific cost-of-capital study, use these US-market defaults and disclose them as defaults rather than computed values. Override when better evidence exists.

| Input | Default | Source |
|---|---|---|
| Risk-free rate (rf) | 10Y US Treasury yield, currently around 4.5% | quote the live yield with date |
| Equity risk premium (ERP) | 5.5% - 6.0% | long-term US ERP (Damodaran-style) |
| Beta (β) | levered β from regression or sector proxy; default 1.0 if missing | financial data provider |
| Cost of equity (Ke) | `rf + β × ERP` | computed |
| Pre-tax cost of debt (Kd) | 5.45% (interest coverage > 8x) to 10.5% (coverage < 2x) | implied from rating or coverage |
| Corporate tax rate (t) | 21% statutory + state ≈ 25% effective | actual when available |
| WACC | `(E/V) × Ke + (D/V) × Kd × (1 - t)` | computed |
| WACC sanity band | 6% (low risk, low growth) to 20% (high risk, high growth) | clamp outside this range |

If `WACC < 6%` or `WACC > 20%`, state which inputs drove the outlier and either accept with justification or clamp to the band.

## Intrinsic Valuation Methods

When data supports, run more than one method and weight them. No single method is reliable in isolation.

### Method 1: Enhanced DCF (suggested weight 35%)

Use a three-stage growth model:

- Years 1-3 (high growth): use evidence-based revenue/FCF growth, cap at 10% for large-cap mature companies unless catalysts justify higher
- Years 4-7 (transition): linearly decay growth to terminal rate
- Years 8+ (terminal): 2.5% - 3.0% perpetual growth

FCF quality adjustment: multiply projected FCF by `max(0.7, 1 - CoV × 0.5)` where `CoV = stdev(historical FCF) / mean(historical FCF)`. This penalizes volatile cash flow streams.

Discount with the WACC computed above. Apply sensitivity for WACC ±1% and terminal growth ±0.5%.

### Method 2: Owner Earnings (suggested weight 35%)

Buffett-style intrinsic value built on owner-distributable cash, not accounting earnings:

```
Owner Earnings = Net Income + Depreciation & Amortization
                  - Maintenance CapEx
                  - Change in Working Capital
```

Key assumptions:

- Required return: 15% (sets the demanded yield; higher than WACC because it embeds a margin-of-safety premium)
- Growth rate: based on sustainable earnings growth, capped at 5% unless evidence supports more
- Terminal growth: min(growth rate, 3.0%)
- Safety margin: discount the resulting value by 25%

`Intrinsic value = Owner Earnings × (1 + g) / (required return - g) × (1 - 0.25)` for a simple Gordon form; use multi-stage for higher-growth names.

Use Owner Earnings when FCF and net income diverge, when CapEx is lumpy, or when the user wants a Buffett/Munger-style read.

### Method 3: EV/EBITDA Relative (suggested weight 20%)

```
Implied equity value = median peer EV/EBITDA × current EBITDA - net debt
Per-share value = implied equity value / diluted shares
```

Use trailing or forward EBITDA, state which. Peers must be a clean set (same sector, similar margin and growth profile). If the target's growth or margin meaningfully differs from peers, justify a premium or discount band.

### Method 4: Residual Income Model (suggested weight 10%)

Useful when FCF is unreliable but earnings and book value are stable (financials, REITs, certain industrials):

```
Residual Income (RI) = Net Income - Cost of Equity × Book Value
Intrinsic value = Book Value + PV(RI over 5-10 years) + PV(terminal RI) × 0.8
```

Key assumptions: cost of equity ≈ 10% as default, book value growth ≈ 3%, safety margin 20%. The 0.8 terminal coefficient is a competition-decay adjustment.

## Aggregating The Methods

For each method that ran successfully, compute the **value gap**:

```
method_gap = (method_value - current_price) / current_price
```

Compute the weighted gap using only methods that produced a valid value > 0:

```
weighted_gap = Σ (method_gap × method_weight) / Σ (used_method_weights)
```

Map weighted gap to a signal:

| Weighted gap | Valuation signal |
|---:|---|
| > +30% | Strongly undervalued |
| +15% to +30% | Undervalued |
| -15% to +15% | Fairly valued |
| -30% to -15% | Overvalued |
| < -30% | Strongly overvalued |

Confidence = min(\|weighted gap\| / 30% × 100, 100).

## Scenario Probability Weighting

After building bear/base/bull cases, compute a probability-weighted expected intrinsic value to make the central estimate explicit:

| Scenario | Default probability | Suggested adjustment |
|---|---:|---|
| Bear | 20% | growth × 0.5, WACC + 1-2 ppt, multiple compression |
| Base | 60% | consensus-like, adjusted for evidence |
| Bull | 20% | growth × 1.5, WACC - 1 ppt, sustainable multiple |

```
Expected value = bear_value × 0.20 + base_value × 0.60 + bull_value × 0.20
Expected gap = (expected_value - current_price) / current_price
```

Adjust the 20/60/20 split when evidence is asymmetric (e.g., binary FDA/regulation/M&A event); always state the adjusted probabilities and why.

Use the expected gap as the central margin-of-safety number, with the bear/base/bull range as the dispersion.

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
