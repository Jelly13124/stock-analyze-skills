# Ownership & Shareholder Structure Module

> Internal module of the orchestrator. Loaded on demand when the report needs
> this section, or when the user invokes it directly. New in 2026-06.

## Overview

Map **who owns the stock and how control is distributed** — the structural counterpart to the
*flow* signals in `modules/sentiment.md`. Ownership structure drives squeeze/liquidity risk
(float, short interest) and governance quality (insider alignment, voting control), feeding both
`modules/risk-position.md` and `modules/company-fundamentals.md`.

**Boundary with `sentiment.md` (do not duplicate):** ownership = *structure / stock* (who holds
it, how much float, who controls votes). sentiment = *flow / signal* (Form-4 buys/sells as a
bull/bear signal; short-interest *change* as a squeeze signal). Short interest appears in both:
**this module owns the structural float / short % of float**; sentiment owns the **change and
signal**. Cross-reference, never restate.

## Data

Run `scripts/fetch_ownership.py <TICKER> --output-dir <out>` (no key needed; yfinance primary,
prefetched fallback). It writes `{TICKER}_ownership_bundle.json` with institutional / insider /
retail %, float vs. shares outstanding, top-10 institutional holders + concentration, short % of
float, days-to-cover. **Share classes / voting control and quarterly 13F deltas are not in the
bundle** — fill them via web search, recency-gated, and label them web-sourced.

## Standalone Markdown Report Mode

When called directly, produce a self-contained Markdown report in the user's language. Structure:

1. `## Ownership Verdict`
2. `## Ownership Composition` (institutional / insider / retail %, float vs. shares out)
3. `## Holder Concentration` (top-10 holders, single-holder dominance)
4. `## Share Classes & Voting Control` (dual-class, super-voting, founder control — governance)
5. `## Short Structure` (short % of float, days-to-cover — structural; cross-ref Sentiment)
6. `## Recent Ownership Changes` (notable 13F adds/trims, insider roster — web, dated)
7. `## Implication For Risk And Fundamentals`

## Interpretation

| Signal | Reading |
|---|---|
| High institutional % rising | Sponsorship/validation; but crowded, higher de-rating risk on misses |
| High insider % (founder-held) | Skin in the game; but watch governance/control concentration |
| Low float + high short % of float | Squeeze + liquidity risk → tighten long-stop logic, **lower the vol-adjusted single-stock cap** |
| Dual-class / super-voting | Common holders have limited control → governance discount; flag as thesis breaker if egregious |
| Top-1 holder dominance | Key-holder / overhang risk (lockups, forced selling) |

## Data Failure and Low-Confidence Rules

- If holder fields are missing for a small cap, report what exists and mark the rest unavailable.
- 13F snapshots lag (quarterly); state the report date and label as lagging.
- Voting structure is web-sourced — apply the recency gate and cite the filing.
- Verify percentage units (fraction vs. %) before display.

## Output Contract

Return a Markdown report or section with: one-sentence ownership verdict; composition table
(institutional / insider / retail %, float vs. shares out); top-10 concentration; share-class /
voting note; structural short % of float + days-to-cover (cross-ref Sentiment for the signal);
recent dated ownership changes; implication for **risk** (squeeze / liquidity → sizing caps) and
**fundamentals** (governance / alignment / thesis breakers); data gaps and source dates;
standalone disclaimer when called directly: `Not investment advice -- for your own research.`

## Depth gating

`standard` + `full SOP` include this section. `basic` includes it only when ownership materially
drives the thesis (e.g., a low-float / high-short name).
