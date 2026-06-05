# Overnight Undervalued Tech-Growth Screen → Full SOP — Design Spec

**Date:** 2026-06-05
**Author:** Claude (brainstormed with user)
**Status:** Approved — execution authorized for unattended overnight run

## Goal

Find **undervalued US tech *growth* stocks (AMBA-style)** using yfinance data, run the
repo's `stock-analysis` **full SOP** on every name that clears a pre-screen gate, and leave
the user a ranked summary plus per-name reports to review in the morning. List every name
whose final SOP Conviction Score is **≥ 60**.

## Fixed parameters (confirmed with user)

| Parameter | Value |
|---|---|
| Data source | yfinance (primary, no key); web search only for universe expansion + non-price gaps, recency-gated |
| Depth | `full SOP` (institutional) |
| Objective | medium-term strategy (1–3 months) → daily + weekly charts, **no intraday** |
| Position & risk | budget **$1000**, **fresh entry** (no existing holding), risk tolerance **Aggressive** |
| Debate mode | **generic** Bull / Bear / Quant / Risk roles — **personas OFF** |
| Scoring column | **Aggressive** weights |
| Universe | **hybrid** — curated seed pool + web-screener expansion |
| Full-SOP coverage | **every name passing the pre-screen gate**, hard safety cap **12** |
| Winners list threshold | final Conviction Score **≥ 60** |
| Deliverable | one master ranking HTML + one full-SOP HTML per qualifier |
| Output location | `outputs/` (master) and `outputs/<TICKER>/<TICKER>_full_sop.html` (per name) |

## What "undervalued tech growth like AMBA" means (screen definition)

- **Scope:** US primary-listed common stock; Technology + tech-adjacent (semiconductors,
  semicap equipment, AI infrastructure / networking, SaaS / software, internet,
  cybersecurity).
- **Size:** small-to-mid cap — market cap **$300M – $20B** (AMBA ≈ $2-3B). Mega-caps
  excluded (not hidden/undervalued plays).
- **Growth floor (hard):** TTM **or** forward revenue growth **≥ 15%** (prefer ≥ 20%).
- **"Undervalued" (relative — growth names rarely cheap on raw P/E):** blended signal —
  PEG ≤ ~1.5 where earnings exist, EV/Sales low *relative to growth rate*, ≥ 20% upside to
  analyst median target, or ≥ 20% pullback off the 52-wk high on intact fundamentals.
- **Quality guards (hard filters):** positive gross margin; not balance-sheet-distressed
  (manageable debt / adequate cash); avg daily dollar volume **≥ ~$5M** (tradeable).

## The two distinct "60s" — do not conflate

1. **Screen Score (0–100, yfinance-only, cheap):** ranks the universe and **gates** which
   names earn a full SOP. Gate = **Screen Score ≥ 60 AND passes all hard guards**.
2. **Conviction Score (the real SOP /100, Aggressive column):** produced inside each full
   SOP. **The user's "list ≥ 60" winners are judged on THIS score**, not the Screen Score.

## Screen Score (Phase-1 ranking proxy, Aggressive-tilted)

Computed deterministically in JS from yfinance fields. Each sub-metric 0–100, weighted:

| Component | Weight | Source fields (yfinance) |
|---|---:|---|
| Growth (rev growth TTM/fwd, earnings growth) | 32 | `revenueGrowth`, `earningsGrowth`, `revenueQuarterlyGrowth` |
| Valuation vs growth (PEG, EV/Sales ÷ growth) | 25 | `pegRatio`, `forwardPE`, `enterpriseToRevenue`, `priceToSalesTrailing12Months` |
| Analyst upside (price vs median target) | 18 | `targetMedianPrice`, `currentPrice`, `numberOfAnalystOpinions` |
| Momentum / pullback quality (off 52w high, vs 200d) | 15 | `fiftyTwoWeekHigh`, `currentPrice`, `twoHundredDayAverage` |
| Quality (gross margin, debt/cash) | 10 | `grossMargins`, `totalDebt`, `totalCash`, `freeCashflow` |

Hard guards (binary, must all pass to be gate-eligible regardless of score): market cap in
band, growth ≥ 15%, positive gross margin, avg $ volume ≥ $5M, not distressed.

## Pipeline (parallel agents)

- **Phase 0 — Universe.** Seed pool (below) + web-screener expansion (Finviz-style growth /
  small-mid-cap tech screens), deduped → ~60–100 candidates. Web figures recency-gated.
- **Phase 1 — Screen (parallel).** Universe chunked; each agent pulls yfinance metrics for
  its chunk via a small Python helper (uses `scripts/data_provider.py` / yfinance), returns
  structured rows. Orchestrator computes Screen Scores → ranked screen table.
- **Phase 2 — Gate.** Keep Screen Score ≥ 60 + all hard guards. If > 12 qualify, take **top
  12 by Screen Score** for full SOP; list overflow in summary as "screened-in, SOP deferred".
- **Phase 3 — Full SOP (one parallel agent per qualifier).** Each runs the `stock-analysis`
  full SOP: Aggressive, medium-term, $1000 fresh entry, generic debate (no personas),
  backtest signal-validation, incremental HTML → `outputs/<TICKER>/<TICKER>_full_sop.html`.
  Returns: Conviction Score (Aggressive), verdict, bear/base/bull targets, one-line thesis,
  $1000 sizing, file path.
- **Phase 4 — Master summary.** One ranking HTML sorted by Conviction Score; **≥ 60 winners
  flagged at top** with verdict, score, targets, $1000 sizing; each linked to its per-name
  report; full screen table appended (incl. screened-out and SOP-deferred names).

## Seed universe (Phase 0 starting pool — AMBA-like names)

**Semiconductors / semicap:** AMBA, LSCC, MTSI, SITM, POWI, CRDO, ALGM, RMBS, SLAB, SMTC,
INDI, NVTS, FORM, ONTO, ACLS, CAMT, UCTT, ICHR, NVMI, AMKR, ALAB.
**SaaS / software / data:** BRZE, GTLB, FROG, PATH, ASAN, MNDY, DOCN, FSLY, PD, ESTC, CFLT,
AMPL, PCOR, APPN, SEMR, DV, GLBE, BILL.
**Cybersecurity:** S, TENB, RPD, QLYS, VRNS, CYBR.
**Internet / connected hardware:** DUOL, IOT, OUST, RBLX, YELP, CARG.

(Web expansion may add/replace; final inclusion is decided by yfinance metrics + guards.)

## Execution vehicle

**Workflow tool** (deterministic fan-out, concurrency caps, resumable). User explicitly
opted into multi-agent parallel orchestration ("派多个 agent 并行" / "你自动派 agent 运行"),
satisfying the Workflow opt-in. Falls back to background Agent tasks only if Workflow proves
unsuitable.

## Known limitations (disclosed, not bugs)

- **Nested debate.** Inside a subagent the SOP's debate cannot spawn *nested* parallel
  persona subagents, so it runs the skill's documented **single-LLM-labeled generic debate**.
  Personas are off anyway — no behavior loss.
- **Cost.** Full SOP on up to 12 names overnight is token-intensive — the scale the user
  opted into with "run all that pass" + parallel agents.
- **yfinance field gaps.** Some small caps miss `pegRatio` / `targetMedianPrice`; the Screen
  Score degrades gracefully (component dropped, weights renormalized) and the gap is flagged.

## Success criteria (morning acceptance)

1. `outputs/screen_summary.html` exists: ranked master table, ≥ 60 winners flagged, links work.
2. One `outputs/<TICKER>/<TICKER>_full_sop.html` per qualifier (≤ 12), each a complete full
   SOP per the skill's QA gate, ending with `Not investment advice -- for your own research.`
3. Every SOP uses Aggressive scoring, medium-term, $1000 sizing, generic debate.
4. Screen table documents the full funnel (universe → guards → gate → SOP'd → deferred).
5. Disclaimers and data dates present; no fabricated figures.
