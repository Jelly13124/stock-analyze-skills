# Dealer Gamma + Ownership Structure + Total-Capital Kelly Sizing — Design Spec

**Date:** 2026-06-24
**Author:** Claude (brainstormed with user)
**Status:** Approved (design) — pending spec review, then writing-plans

## Goal

Close two analytical gaps in the `stock-analysis` skill and upgrade its position-sizing model:

1. **Dealer gamma (GEX)** — a new module covering options dealer gamma exposure, the
   gamma-flip level, call/put walls, and max pain. Today the skill has no gamma at all;
   options content is four metrics buried in `sentiment.md` (IV, put/call OI, skew, unusual
   activity).
2. **Ownership / shareholder structure (股权结构)** — a new module covering institutional /
   insider ownership, float, top holders, share-class & voting control, and structural
   short interest. Today this is one bullet in the fundamentals schema plus Form-4 *flow* in
   `sentiment.md`; there is no structural treatment.
3. **Total-capital Kelly sizing** — Request Gate item (3a) changes from "budget" to **total
   investable capital (总仓位)**, and the risk module computes the **Kelly-optimal allocation**
   for the name (fractional Kelly, scaled by risk tolerance, capped by existing limits). A
   user-supplied fixed dollar amount is still honored (backward compatible).

All three keep the **no-API-key invariant**: data comes from the existing
`direct API → yfinance → prefetched` chain, with yfinance as the no-key primary.

## Decisions confirmed with user

| Decision | Choice |
|---|---|
| Gamma placement | **New dedicated module** `modules/options-gamma.md` (not folded into sentiment) |
| Gamma meaning | Options **dealer gamma exposure (GEX)** — net GEX, gamma flip, call/put walls, max pain |
| Ownership placement | **New dedicated module** `modules/ownership-structure.md` (not just an expanded fundamentals bullet) |
| Kelly aggressiveness | **Fractional Kelly, scaled by risk tolerance** (conservative ¼ / balanced ½ / aggressive ¾), never full Kelly |
| Manual budget | **Keep both** — default ask = total capital → Kelly; a user-given fixed amount overrides and skips Kelly |
| Scoring categories | **No new categories** — new modules feed existing categories; /100 stays stable |
| Build order | ① Kelly → ② Ownership → ③ Gamma (each lands independently) |

## Feature 1 — Options-Gamma module (`modules/options-gamma.md`)

### Data & feasibility
- **Source:** yfinance `Ticker.options` (expiry list) + `Ticker.option_chain(expiry)` (calls /
  puts DataFrames: `strike`, `openInterest`, `impliedVolatility`, `volume`, `inTheMoney`).
- yfinance does **not** return greeks → compute **gamma via Black-Scholes**:
  `gamma = N'(d1) / (S·σ·√T)`, with `d1 = [ln(S/K) + (r + σ²/2)T] / (σ√T)`.
  Inputs: `S` = spot (from existing quote path), `K` = strike, `σ` = chain IV, `T` = calendar
  time-to-expiry in years, `r` = assumed short risk-free rate (default constant, disclosed).
- New script `scripts/fetch_options_gamma.py <TICKER>` → JSON bundle (and optional
  GEX-by-strike PNG). Reuses `data_provider.py` for spot; option-chain fetch added there as a
  shared helper honoring `direct API → yfinance → prefetched` + `ensure_yfinance()`.

### Computed metrics (JSON contract)
`spot`, `as_of`, `expiries_used[]`, `r_assumed`, `dealer_sign_assumption`,
`net_gex`, `net_gex_per_1pct`, `gamma_flip_level`, `distance_to_flip_pct`,
`regime` ("positive" | "negative"), `call_wall_strike`, `put_wall_strike`,
`max_pain_strike`, `by_strike_profile[]`, `by_expiry[]`, `data_quality`, `caveats[]`.

- **Net GEX** under the standard dealer assumption (long call gamma / short put gamma):
  `Σ gamma·OI·100·S²·0.01` for calls minus puts. `>0` = positive-gamma regime (vol
  suppression, mean reversion, pinning); `<0` = negative-gamma regime (vol amplification,
  trending, wider ranges).
- **Gamma flip (zero-gamma level):** spot at which net GEX crosses zero, found by recomputing
  net GEX across a hypothetical spot range. Regime-switch line; feeds stop / invalidation
  context.
- **Call wall / put wall:** strikes with the largest call / put gamma → resistance(pin) /
  support.
- **Max pain:** strike minimizing total option-holder value → OPEX-week magnet.

### Report placement & feeds
- New report section **"Options Positioning & Dealer Gamma"** placed **after Technical
  Analysis** (walls/flip are price levels complementing support/resistance).
- Feeds **Event Risk** (OPEX, negative-gamma regime), **Risk & Position Sizing** (negative
  gamma → widen stop or size down), and scoring categories *Technical setup* + *Risk and event
  profile*.

### Depth gating
- `full SOP`: default when the name is liquidly optionable.
- `standard`: only when objective = short-term trade, or on explicit request.
- `basic`: skip unless asked.
- Non-optionable / thin chain (OI below threshold) → section marked `n/a — <reason>`.

### Caveats (must be disclosed in-section)
Dealer-sign is a heuristic (true dealer positioning is unobservable); yfinance IV is noisy on
illiquid strikes (filter by OI); `r` and calendar-`T` are approximations; snapshot drifts
intraday and around OPEX.

## Feature 2 — Ownership-Structure module (`modules/ownership-structure.md`)

### Data & feasibility
- **Source (yfinance):** `major_holders`, `institutional_holders`, `mutualfund_holders`,
  `insider_roster_holders`; `info` fields `heldPercentInsiders`, `heldPercentInstitutions`,
  `floatShares`, `sharesOutstanding`, `sharesShort`, `sharesShortPriorMonth`,
  `shortPercentOfFloat`, `shortRatio`.
- **Web (recency-gated):** dual-class / super-voting structure and voting control (from
  proxy / 10-K); notable quarter-over-quarter 13F moves. yfinance does not cover these cleanly.
- New script `scripts/fetch_ownership.py <TICKER>` → JSON. Shared yfinance holders helper added
  to `data_provider.py`.

### Content (JSON contract)
`shares_outstanding`, `float_shares`, `pct_held_institutions`, `pct_held_insiders`,
`pct_held_retail` (residual), `top_institutional_holders[]`, `top_fund_holders[]`,
`top10_concentration_pct`, `short_pct_float`, `short_ratio_days_to_cover`, `shares_short`,
`shares_short_prior`, `share_classes` (web), `voting_control` (web), `recent_13f_notes` (web),
`insider_roster[]`, per-field `as_of` dates, `data_quality`.

Reads: institutional sponsorship trend; insider alignment (high insider % = skin in the game;
founder-controlled = governance flag); float vs. shares outstanding + short % → squeeze &
liquidity; dual-class → governance discount.

### Boundary with `sentiment.md` (explicit, to avoid duplication)
- **ownership = structure / stock** (who holds it, how much float, who controls votes).
- **sentiment = flow / signal** (Form-4 buys/sells as a bull/bear signal; short-interest
  *change* as a squeeze signal).
- Short interest appears in both: **ownership owns the structural float / short %**; **sentiment
  owns the change & signal**. Cross-reference, do not restate.

### Report placement & feeds
- New report section **"Ownership & Shareholder Structure (股权结构)"** placed **after Company
  Fundamentals**.
- Feeds **Company Fundamentals** (governance / alignment / thesis-breakers), **Risk & Position
  Sizing** (low float + high short → squeeze & liquidity → affects vol-adjusted cap and
  single-stock cap), and scoring categories *Company fundamentals* + *Risk and event profile*.

### Depth gating
- `standard` + `full SOP`: include.
- `basic`: only when it materially drives the thesis (e.g., low-float / high-short name).

### Caveats
13F snapshots lag (quarterly); voting structure is web-sourced (recency-gate); some small caps
miss holder fields — degrade gracefully and flag the gap.

## Feature 3 — Total capital (总仓位) + Kelly sizing

### Request Gate change (`SKILL.md` item 3a)
> **Old:** "(a) budget: a dollar amount or % of portfolio"
> **New:** "(a) total investable capital (总仓位) — your whole account / investable pot, so I can
> compute the Kelly-optimal allocation for this name; OR give a fixed dollar amount or % if you
> want to size it yourself, and I'll use that directly."

Default = total capital → Kelly. A user-given fixed amount overrides and skips Kelly.

### Kelly method (`risk-position.md` new section "Kelly Position Sizing")
Multi-outcome Kelly over the existing bear/base/bull scenarios:

```
r_i      = (T_i − E)/E                              # scenario returns; E = entry
r_bear   = max((T_bear − E)/E, −|E − S|/E)          # stop S caps the downside
f*       = argmax_f  Σ p_i · ln(1 + f·r_i)          # full Kelly (numeric, f∈[0,1])
                                                    # binary sanity check: f=(p·b−q)/b
k        = 0.25 conservative | 0.50 balanced | 0.75 aggressive   # fractional Kelly
f_kelly  = max(0, k · f*)                           # negative edge → 0 (avoid / short candidate)
f_final  = min(f_kelly, single_stock_cap, vol_adjusted_cap)      # Kelly never exceeds caps
f_stop   = risk_per_trade ÷ (|E − S|/E)             # existing stop-based sizing
position = min(f_final, f_stop) × 总仓位             # most conservative binds; output $ + shares
```

- **Held position:** target $ = `position`; delta = target − current value → **add / trim** to
  reach optimal.
- **Probability sourcing:** prefer the bear/base/bull confidences already in the report; when
  absent, map from the conviction score via a default table (connects scoring → Kelly):

  | Conviction score | (p_bear, p_base, p_bull) |
  |---|---|
  | 75–100 | 0.15 / 0.45 / 0.40 |
  | 65–74  | 0.20 / 0.50 / 0.30 |
  | 50–64  | 0.30 / 0.50 / 0.20 |
  | <50    | 0.45 / 0.45 / 0.10 |

### Caveats (must be disclosed)
Kelly is highly sensitive to `p` and `b` estimation error (hence fractional); single-analysis
estimates are uncertain; Kelly assumes repeatable independent bets, so for a one-off
concentrated position treat the output as an **upper bound** and lean toward the
capped / stop-based smaller value.

## Scoring interaction

No new scoring categories — the /100 stays stable. Gamma feeds *Technical setup* + *Risk and
event profile*; ownership feeds *Company fundamentals* + *Risk and event profile*. The
conviction score feeds Kelly **one-directionally** (score → probabilities → sizing), so there
is no circularity.

## File-by-file changes (consistency rule per CLAUDE.md)

### New
- `stock-analysis/modules/options-gamma.md`
- `stock-analysis/modules/ownership-structure.md`
- `stock-analysis/scripts/fetch_options_gamma.py`
- `stock-analysis/scripts/fetch_ownership.py`
- shared yfinance helpers (option chain + holders) added to `stock-analysis/scripts/data_provider.py`

### Modified
- `stock-analysis/SKILL.md` — Module Routing (+2 rows); Gate item 3a (总仓位 + Kelly);
  Position & Risk Profile Use (Kelly path + manual-amount fallback); Workflow (add fetch steps +
  module reads); Overview module count 18 → 20 (9 → 11 analytical); Event Risk (gamma regime /
  OPEX); Output Rules
  QA gate (+2 expected sections); `description:` keywords (gamma, ownership, Kelly).
- `stock-analysis/modules/risk-position.md` — "Kelly Position Sizing" section; total-capital
  input; reconcile-with-caps rule; held-position Kelly delta.
- `stock-analysis/modules/sentiment.md` — point options depth to the gamma module; state the
  short-interest boundary with ownership.
- `stock-analysis/modules/company-fundamentals.md` — point the ownership-structure portion to
  the new module.
- `stock-analysis/references/report-template.md` — add 2 schema sections; add Kelly to the Risk
  section; Section Length Budget (+2 rows); Full SOP Minimum Gate + QA expected sections.
- `stock-analysis/references/report-template.html` — matching HTML structure for the 2 new
  sections + a Kelly sizing block.
- `stock-analysis/references/depth-framework.md` — depth gating for the 2 modules.
- `stock-analysis/modules/debate-panel.md` — quant / risk roles may cite gamma regime +
  float/short (light touch).
- `stock-analysis/CLAUDE.md` — invariants (Gate item 3 wording, module count, consistency-rule
  file list +2 modules); layout note (10 → 12 analytical modules).
- `README.md` / `README.zh-CN.md` — feature list (gamma, ownership, Kelly sizing), module count,
  gate description; keep the two in sync.

## Build / landing order

Each ships independently:
1. **Kelly** — gate-level, no new data dependency, smallest blast radius.
2. **Ownership** — yfinance holders fetch, medium.
3. **Gamma** — most script / algorithm-heavy (BS gamma + GEX + flip search).

## Non-goals

- No new scoring categories; no change to the /100 weights.
- No real-time / paid options feed; yfinance snapshot only (+ prefetched fallback).
- No tax advice in the held-position Kelly delta (consistent with current holding-period note).
- No attempt to model true dealer inventory beyond the standard long-call / short-put heuristic.
- Persona roster, debate mechanics, and backtest are untouched.

## Success criteria

1. A bare ticker at `full SOP` produces a report that includes **Options Positioning & Dealer
   Gamma** (or `n/a — <reason>` when not optionable) and **Ownership & Shareholder Structure**.
2. The Request Gate asks for **总仓位 (total capital)**; a total-capital answer yields a
   **Kelly-recommended** position (% + $ + shares) showing `f*`, `k`, caps, `f_stop`, and which
   binds; a fixed-amount answer skips Kelly and sizes to that amount.
3. Held-position answers produce an **add / trim** delta to the Kelly target.
4. Both new scripts run on the no-key path (`python ... <TICKER>`), emit JSON, and degrade
   gracefully with disclosed gaps; `python -m py_compile` passes for all scripts.
5. All consistency-rule files agree (gate wording, module count, section list); README.md and
   README.zh-CN.md stay in sync; every report still ends with
   `Not investment advice -- for your own research.`
