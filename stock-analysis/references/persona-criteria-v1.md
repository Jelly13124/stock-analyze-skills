# Persona Criteria — v1

v1 supports four personas that can be evaluated using quarterly EPS, revenue, FCF, debt, equity, current assets/liabilities, shares, and dividends. Buffett / Munger / Fisher / Wood require richer fundamentals and are documented at the bottom as deferred to v2.

All persona evaluations apply a **60-day filing embargo** — on rebalance date `t`, only fundamentals with `period_end_date + 60d <= t` are considered.

Rebalance frequency: `quarterly` (default) or `annual`. Transitions are executed at the next bar open with slippage + commission.

Criteria are also encoded in `persona-criteria-v1.yaml` for execution. Keep the two files in sync when editing.

---

## `lynch` — Peter Lynch GARP

**Hold if all of:**

| Criterion | Threshold | Field |
|---|---|---|
| TTM EPS growth (YoY) | ≥ 15% | `eps_diluted` rolled to TTM, compared to TTM four quarters prior |
| PEG ratio | ≤ 1.0 | `(price / TTM EPS) / (EPS growth %)` |
| Debt / Equity | < 0.5 | `total_debt / total_equity` |

**Otherwise:** sit in cash until next rebalance.

**Cite:** Lynch *One Up On Wall Street*, GARP framework; `stock-investor-lynch/SKILL.md` for the original lens.

**Known failure mode:** Catches early-stage growth slowdowns AFTER the price has already cracked — the EPS revision shows up in the filing 6-8 weeks after the stock reacts.

---

## `graham` — Benjamin Graham defensive

**Hold if all of:**

| Criterion | Threshold | Field |
|---|---|---|
| P/E | < 15 | `price / TTM EPS` |
| P/B | < 1.5 | `price / book_value_per_share` (BVPS = `total_equity / shares_diluted`) |
| Dividend yield | > 2% | `TTM dividend_per_share / price` |
| Current ratio | > 2 | `current_assets / current_liabilities` |

**Otherwise:** cash.

**Cite:** Graham *The Intelligent Investor* defensive criteria; `stock-investor-graham/SKILL.md`.

**Known failure mode:** Almost never triggers a hold on modern megacap tech (P/E and P/B fail). Triggers more reliably on utilities, financials, value names. Will hold value traps that look statistically cheap.

---

## `burry` — Michael Burry deep value

**Hold if all of:**

| Criterion | Threshold | Field |
|---|---|---|
| FCF yield | ≥ 15% | `TTM FCF / market cap`, where market cap = `price * shares_diluted` |
| P/B | < 1.5 | as above |
| Debt / Equity | < 0.5 | as above |

**Otherwise:** cash.

**Cite:** Burry's letters; `stock-investor-burry/SKILL.md`. FCF yield 15% is the deep-value threshold.

**Known failure mode:** Extraordinarily rare trigger on growth names. Will hold deeply distressed companies that meet the screen but are heading to zero — relies on subsequent qualitative judgment that a backtest cannot model.

---

## `druckenmiller_lite` — Druckenmiller momentum + macro proxy

**Hold if all of:**

| Criterion | Threshold | Field |
|---|---|---|
| Price > 200-day SMA | true | `close > sma200` |
| 50-day SMA > 200-day SMA | true | `sma50 > sma200` |
| Benchmark trend filter | SPY > SPY-SMA200 | uses benchmark passed via `--benchmark` |

**Otherwise:** cash.

**Note:** This is a `*_lite` version — true Druckenmiller looks at macro regime (rates, dollar, commodity cycle), which v1 does not have. The SPY trend filter is a coarse proxy for risk-on/risk-off.

**Cite:** Druckenmiller interviews; `stock-investor-druckenmiller/SKILL.md`.

**Known failure mode:** Whipsaws around SMA crosses; misses sharp reversals before SMAs roll over.

---

## Deferred to v2 (returns `data_insufficient`)

When the user requests one of these, the script exits with code 6 and writes a bundle containing only the explanation. SKILL.md must NOT silently substitute a different persona.

| Persona | Why deferred |
|---|---|
| `buffett` | Needs owner earnings (EPS + D&A − maintenance capex) and 10-yr ROE history. Maintenance capex isn't a separately reported line; mainstream approximations like "CapEx − reported CapEx for growth" are too rough for a backtest threshold. |
| `munger` | Needs ROIC time series and a business predictability rating. ROIC requires careful treatment of operating leases, goodwill, and intangibles that vary by sector. |
| `fisher` | Needs R&D intensity rank and scuttlebutt-style qualitative checks (management depth, sales force quality). |
| `wood` | Needs disruptive-innovation classification and forward TAM model — both are research outputs, not retrievable from filings. |

v2 plan for these: add `get_owner_earnings_history()` (uses Finnhub financials-reported XBRL parsing for D&A and CapEx) and a `references/business-classification.yaml` for the qualitative inputs that a human must fill in.

---

## How to add a new persona to v1

1. Add a function `persona_<name>(q, idx, quarters, price)` to `backtest.py` that returns `(bool, dict_of_details)`. Use only fields available in the v1 quarters schema.
2. Register in `PERSONA_REGISTRY`.
3. Add the rules to `persona-criteria-v1.yaml`.
4. Document the row in this file (criteria table + known failure mode).
5. Add a smoke test command to SKILL.md.

If the new persona needs fields not in the v1 quarters schema, add them to `data_provider.get_fundamentals_history()` first.
