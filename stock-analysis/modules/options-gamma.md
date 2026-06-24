# Options Positioning & Dealer Gamma Module

> Internal module of the orchestrator. Loaded on demand when the report needs
> this section, or when the user invokes it directly. New in 2026-06.

## Overview

Estimate **dealer gamma positioning (GEX)** to read the volatility regime and the option-driven
price magnets. This is the structural counterpart to the *flow* metrics (IV / put-call / skew) in
`modules/sentiment.md` — those stay in sentiment as a signal; **GEX, gamma flip, walls, and max
pain live here.**

Dealer-sign convention (the standard naive GEX): dealers are **long call gamma, short put gamma**.
- **Net GEX > 0 (positive-gamma regime):** dealers buy dips / sell rips → **vol suppression, mean
  reversion, pinning** toward walls / max pain.
- **Net GEX < 0 (negative-gamma regime):** dealers sell dips / buy rips → **vol amplification,
  trending, wider ranges** → widen stops or size down.

## Data

Run `scripts/fetch_options_gamma.py <TICKER> --output-dir <out>` (no key; yfinance option chain,
prefetched fallback). It computes Black-Scholes gamma per contract (yfinance gives no greeks),
sums signed GEX, finds the gamma flip by scanning spot ±30%, and reports call/put walls and max
pain. Output: `{TICKER}_gamma_bundle.json`.

## Standalone Markdown Report Mode

When called directly, produce a self-contained Markdown report in the user's language. Structure:

1. `## Gamma Verdict` (regime + one-line implication)
2. `## Net GEX & Regime`
3. `## Gamma Flip (Zero-Gamma) Level` (and distance from spot)
4. `## Call Wall / Put Wall` (resistance / support)
5. `## Max Pain` (OPEX magnet)
6. `## Implication For Levels, Stops, And Event Risk`

## Interpretation

| Metric | Reading |
|---|---|
| Net GEX sign | `+` vol suppression / mean-revert; `−` vol amplification / trend |
| Gamma flip level | regime-switch price; above = stable, below = unstable — use as invalidation context |
| Call wall | largest call gamma·OI strike → resistance / upside pin |
| Put wall | largest put gamma·OI strike → support |
| Max pain | strike minimizing holder payout → magnet into OPEX week |

## Feeds

- **Technical Analysis** — walls / flip are price levels complementing support/resistance.
- **Risk & Position Sizing** — negative-gamma regime → widen stop or reduce size.
- **Event Risk Check** — OPEX week, negative-gamma into earnings IV.

## Data Failure and Low-Confidence Rules

- Not optionable / chain too thin (all strikes filtered for OI<=0 or IV<=0) → section is
  `n/a — not optionable / chain too thin`. Do not fabricate GEX.
- Disclose the dealer-sign heuristic, the assumed rate, and that the snapshot drifts intraday and
  around OPEX.
- yfinance IV noise: contracts with non-positive OI or IV are dropped before computation.

## Output Contract

Return a Markdown report or section with: one-sentence gamma verdict (regime); net GEX + regime;
gamma flip level + distance from spot; call/put walls; max pain; implication for technical levels,
stop width, and event risk; explicit `n/a — <reason>` when not optionable; caveats (dealer-sign
heuristic, assumed rate, snapshot drift); standalone disclaimer when called directly:
`Not investment advice -- for your own research.`

## Depth gating

`full SOP`: include when the name is liquidly optionable. `standard`: only when objective =
short-term trade or on explicit request. `basic`: skip unless asked. Non-optionable → `n/a`.
