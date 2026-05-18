# Backtest Skill — Design Document (v1)

**Status:** Draft for review. No files will be created until you approve.

**Scope of v1:**
- Mode 1 — **Indicator strategy backtest** (single ticker, rule-based entry/exit)
- Mode 2 — **Signal validation** (event study, no equity curve, just statistical edge)
- Mode 3 — **Persona backtest, partial** (only personas where price + EPS / revenue / FCF / dividends are sufficient: Lynch, Graham, Burry, Druckenmiller-lite). Buffett / Munger / Fisher / Wood return `"data_insufficient"` with a documented note pointing to v2.

**Deferred to v2:** multi-stock portfolio, walk-forward parameter optimization, full Buffett / Munger / Fisher / Wood (need richer fundamentals: owner earnings, ROIC time series, R&D intensity, TAM classification).

**Engine:** stdlib + pandas only. No vectorbt / backtrader.

**Placement:** New sibling folder `stock-backtest/` next to the existing 17 skills. When the superpower migration runs, this folder folds into `stock-analysis/modules/backtest.md` with the same edit rule used for the other modules — no rework.

---

## 1. Folder Layout

```
stock-backtest/
├── SKILL.md
├── agents/
│   └── openai.yaml
├── scripts/
│   └── backtest.py                 ← stdlib + pandas, imports sibling data_provider
└── references/
    ├── strategy-registry.md        ← every built-in strategy with its rules
    ├── persona-criteria-v1.md      ← v1 persona thresholds (Lynch/Graham/Burry/Druckenmiller)
    └── overfitting-checklist.md    ← reality-check rules the SKILL.md must apply
```

### Sibling data reuse — no duplication of `data_provider.py`

`backtest.py` imports `data_provider` from `stock-analysis/scripts/` via a sys.path shim:

```python
import sys
from pathlib import Path

_here = Path(__file__).resolve().parent
_sibling = _here.parent.parent / "stock-analysis" / "scripts"
if _sibling.exists() and str(_sibling) not in sys.path:
    sys.path.insert(0, str(_sibling))

from data_provider import (   # noqa: E402
    get_daily_ohlcv,
    get_weekly_ohlcv,
    get_quote,
    load_keys,
    get_output_dir,
)
```

This works on Claude Code / Desktop / Codex where both skills sit side-by-side under `~/.claude/skills/`. For Claude.ai web, the zip bundle bakes both folders into the upload, so the relative path still resolves.

### One additive function in `data_provider.py`

For persona mode we add **one** new function to the existing provider (does NOT change any existing function signatures):

```python
def get_fundamentals_history(
    ticker: str, keys: dict[str, str],
    start: str, end: str,
) -> dict[str, Any]:
    """Returns quarterly fundamentals time series:
       { 'as_of_dates': [...],         # report filing dates (with embargo applied)
         'period_end_dates': [...],
         'eps_diluted': [...],
         'revenue': [...],
         'fcf': [...],
         'debt_to_equity': [...],
         'current_ratio': [...],
         'dividend_per_share': [...],
         'book_value_per_share': [...],
         'source': 'finnhub' | 'prefetched' | 'yfinance' | 'unavailable',
         'data_quality': 'good' | 'partial' | 'unavailable',
         'missing_fields': [...]
       }
    """
```

Primary source: Finnhub `/stock/financials-reported` (annual + quarterly).
Fallback: yfinance `.quarterly_financials` and `.quarterly_balance_sheet`.
Prefetched path: same JSON shape under `${PREFETCH_DIR}/{ticker}_fundamentals.json`.

If everything fails: `data_quality: 'unavailable'`, persona backtest returns a documented null result rather than crashing.

---

## 2. `scripts/backtest.py` — CLI Spec

```text
python backtest.py <TICKER> [options]

Required positional:
  TICKER                           e.g. NVDA

Mode selector (exactly one):
  --mode {indicator|signal|persona}

Mode-specific:
  --strategy <name>                Required for --mode indicator. See §3.1.
  --signal <name>                  Required for --mode signal. See §3.2.
  --persona <name>                 Required for --mode persona. See §3.3.
  --holding-days <int>             For --mode signal only. Default 20.
  --rebalance-frequency {quarterly|annual}   For --mode persona only. Default quarterly.
  --params '<json>'                Strategy-specific knobs. e.g. '{"stop_loss":0.05}'

Window:
  --start YYYY-MM-DD               Default = 5 years before --end
  --end YYYY-MM-DD                 Default = today

Trade economics:
  --initial-capital <float>        Default 100000
  --commission-bps <float>         Default 5  (per side, in basis points of trade value)
  --slippage-bps <float>           Default 5  (per side)
  --position-sizing {all-in|fixed-fraction}   Default all-in
  --fraction <float>               Required if --position-sizing fixed-fraction. e.g. 0.25

Benchmark / data:
  --benchmark <ticker>             Default SPY
  --key-file <path>                Same lookup as fetch_price_charts.py
  --output-dir <path|auto>         "auto" picks the cross-platform output dir

Quality controls:
  --in-sample-fraction <float>     Default 0.7. The first 70% of the window is treated
                                   as in-sample, last 30% as out-of-sample, and the
                                   metrics are reported separately. Use 0.0 to flag
                                   the entire window as out-of-sample (when the user
                                   has NOT optimized params on this ticker).

Output:
  --no-charts                      Skip PNG generation; still write JSON + CSV.
  --tag <string>                   Suffix added to all output filenames.
```

### Exit codes

```
0  success (even if metrics are bad — that's a result, not an error)
2  bad CLI args
3  data fetch failed for primary ticker
4  data fetch failed for benchmark
5  unknown strategy / signal / persona name
6  fundamentals unavailable for persona that requires them
```

Anything else: crash with traceback (real bug).

---

## 3. Built-In Registry

### 3.1 `--mode indicator` strategies (v1)

| Name | Entry | Exit | Params (defaults) |
|---|---|---|---|
| `kdj_golden_cross` | K crosses above D AND both K,D < 30 | death cross OR stop_loss OR take_profit | `stop_loss=0.05, take_profit=0.15` |
| `sma_50_200_cross` | SMA50 crosses above SMA200 | SMA50 crosses below SMA200 | none |
| `rsi_mean_reversion` | RSI(14) < 30 | RSI(14) > 70 OR stop_loss | `stop_loss=0.08` |
| `bb_lower_bounce` | close < lower Bollinger (20, 2σ) | close > middle band OR stop_loss | `stop_loss=0.05` |
| `macd_signal_cross` | MACD line crosses above signal line AND signal > 0 | MACD crosses below signal | none |

Decisions are made on **bar t** using data through **bar t-1** close. Execution price = **bar t open**, plus slippage_bps, plus commission_bps. Same logic on exit. This eliminates the most common look-ahead bug.

### 3.2 `--mode signal` signals (v1)

Same triggers as the entries above, plus:

| Name | Condition |
|---|---|
| `rsi_oversold` | RSI(14) < 30 |
| `bb_squeeze_breakout` | BB width contracted to 6-month low, then close breaks upper BB |
| `volume_spike_2x` | volume ≥ 2 × 20-day avg volume |
| `gap_up_3pct` | open ≥ 1.03 × previous close |
| `new_52w_high` | close = trailing 252-bar high |

Output: forward N-day returns at horizons +1, +5, +10, +20, +60 days (regardless of `--holding-days`; that arg only sets the primary horizon for the headline metric). Aggregated as mean / median / std / hit_rate / t_stat / max_gain / max_loss. Compared to a baseline distribution drawn from the same number of random dates in the same window.

No trades, no equity curve, no commissions. Pure statistical edge probe.

### 3.3 `--mode persona` personas (v1 supported)

| Persona | Held when (rebalance check) | Notes |
|---|---|---|
| `lynch` | EPS growth (TTM) ≥ 15% AND PEG ≤ 1 AND debt/equity < 0.5 | PEG derived from trailing 4Q EPS growth |
| `graham` | P/E < 15 AND P/B < 1.5 AND dividend yield > 2% AND current ratio > 2 | Defensive screen, not Net-Net |
| `burry` | FCF yield ≥ 15% AND P/B < 1.5 AND debt/equity < 0.5 | FCF yield = TTM FCF / market cap |
| `druckenmiller_lite` | Price > SMA200 AND SMA50 > SMA200 AND SPY > SPY-SMA200 | Macro proxy only; no real macro data in v1 |

### 3.3a `--mode persona` personas — **v1 NOT supported** (returns `data_insufficient`)

| Persona | Why deferred |
|---|---|
| `buffett` | Needs owner earnings (EPS + D&A − maintenance capex) and 10-yr ROE history. Maintenance capex isn't a reported line. |
| `munger` | Needs ROIC time series, business predictability rating — no clean data source. |
| `fisher` | Needs R&D intensity rank and qualitative scuttlebutt. |
| `wood` | Needs disruptive-innovation classification and forward TAM model. |

When the user invokes one of these in v1, `backtest.py` exits with code 6 and writes a `{TICKER}_backtest_bundle.json` containing only the explanation. SKILL.md interprets this honestly and offers the supported personas as alternatives — does not silently substitute.

### 3.3b Persona mechanics

- Fundamentals are aligned to the rebalance schedule (quarterly by default).
- An **embargo of 60 calendar days** is applied to fundamentals before they become tradable — i.e., on rebalance date `t`, only fundamentals with `as_of_date ≤ t − 60d` are used. This prevents look-ahead via the filing lag.
- On each rebalance date, evaluate the persona's criteria. If passing → hold 100% in stock. If failing → 100% cash (zero return; risk-free is left as 0 in v1).
- Transitions are executed at next bar open with slippage + commission.
- Persona criteria are loaded from `references/persona-criteria-v1.md` so they can be edited without code changes.

---

## 4. Output Schema

Output files (all written to `--output-dir`, naming includes `--tag` suffix if provided):

```
{TICKER}_backtest_bundle.json        # top-level summary, consumed by SKILL.md
{TICKER}_equity_curve.png            # equity vs Buy&Hold vs benchmark
{TICKER}_trades.csv                  # one row per round-trip trade (indicator + persona only)
{TICKER}_signal_distribution.png     # signal mode only — return distribution histogram
```

### `{TICKER}_backtest_bundle.json` shape

```json
{
  "ticker": "NVDA",
  "mode": "indicator",
  "strategy": "kdj_golden_cross",
  "params": { "stop_loss": 0.05, "take_profit": 0.15 },
  "window": {
    "start": "2020-05-18",
    "end": "2026-05-18",
    "in_sample_end": "2024-04-15",
    "out_of_sample_start": "2024-04-16",
    "trading_days": 1510
  },
  "costs": {
    "commission_bps": 5,
    "slippage_bps": 5,
    "total_cost_drag_pct": 0.0142
  },
  "data_quality": {
    "ticker_source": "alpha_vantage",
    "benchmark_source": "alpha_vantage",
    "fundamentals_source": "n/a",
    "missing_bars": 0,
    "data_health": "good"
  },
  "summary_full": {
    "total_return": 1.34,
    "cagr": 0.187,
    "sharpe": 1.42,
    "sortino": 1.98,
    "max_drawdown": -0.234,
    "calmar": 0.799,
    "trades": 36,
    "win_rate": 0.583,
    "profit_factor": 1.78,
    "avg_holding_days": 18.4,
    "exposure_pct": 0.612
  },
  "summary_in_sample":  { "...": "same keys as summary_full" },
  "summary_out_of_sample": { "...": "same keys as summary_full" },
  "benchmark": {
    "ticker": "SPY",
    "total_return": 0.87,
    "cagr": 0.111,
    "max_drawdown": -0.246
  },
  "buy_and_hold": {
    "total_return": 2.18,
    "cagr": 0.245,
    "max_drawdown": -0.612
  },
  "alpha": {
    "vs_buy_and_hold_total": -0.84,
    "vs_benchmark_total":     0.47
  },
  "overfitting_diagnostics": {
    "in_sample_cagr": 0.224,
    "out_of_sample_cagr": 0.041,
    "degradation_ratio": 0.183,
    "interpretation": "out-of-sample materially weaker — likely overfit OR regime change",
    "params_user_supplied": false,
    "params_searched_count": 0
  },
  "trades_file": "outputs/.../NVDA_trades.csv",
  "equity_curve_file": "outputs/.../NVDA_equity_curve.png"
}
```

For `mode: "signal"`, the bundle replaces `summary_*` / `trades` blocks with:

```json
"signal_stats": {
  "signal": "kdj_golden_cross",
  "events": 47,
  "horizons": {
    "1d":  { "mean_return": 0.004, "median": 0.002, "hit_rate": 0.553, "t_stat": 0.92,  "max_gain": 0.087, "max_loss": -0.061 },
    "5d":  { "...": "..." },
    "10d": { "...": "..." },
    "20d": { "mean_return": 0.031, "median": 0.018, "hit_rate": 0.617, "t_stat": 2.14, "...": "..." },
    "60d": { "...": "..." }
  },
  "baseline": {
    "method": "1000_random_dates_same_window",
    "mean_return_20d": 0.012,
    "hit_rate_20d": 0.548
  },
  "edge_vs_baseline": {
    "20d_mean_return_diff": 0.019,
    "20d_hit_rate_diff": 0.069,
    "edge_t_stat_20d": 1.87,
    "significant_at_p05": false
  }
}
```

For `mode: "persona"`, the bundle adds:

```json
"persona": {
  "name": "lynch",
  "rebalances": 24,
  "periods_held": 17,
  "periods_cash": 7,
  "exposure_pct": 0.708,
  "fundamentals_data_quality": "good",
  "fundamentals_missing_quarters": 0,
  "criteria_pass_summary": { "...": "per-quarter pass/fail trace, abbreviated" }
}
```

---

## 5. Integrity Rules (Baked Into Both Script and SKILL.md)

Look-ahead, survivorship, and cost honesty are the things backtests get wrong most often. The script enforces these at execution time:

1. **No same-bar entry**: signals computed on bar `t` execute on bar `t+1` open. Hardcoded; not user-configurable.
2. **No future fundamentals**: persona mode applies a 60-day embargo on the fundamentals reporting date.
3. **No zero-cost trades**: minimum commission_bps + slippage_bps = 0 is allowed but emits a warning in the bundle (`"costs.warning": "frictionless backtest — not realistic"`).
4. **No dividend-adjusted-only data without disclosure**: bundle records whether prices are adjusted (Alpha Vantage adjusted vs. raw) and SKILL.md must mention it.
5. **Out-of-sample reported separately**: even if no parameter optimization happened, the in-sample / out-of-sample split is always reported. Lets the reader see regime change.

SKILL.md additional honesty rules:
- Always report `summary_in_sample` AND `summary_out_of_sample` in the headline table.
- If `degradation_ratio < 0.4`, the verdict section must say "strategy did not generalize" or equivalent — not "strategy works".
- Single-ticker caveats are mandatory: state explicitly that one ticker is N=1, not statistical evidence.
- Cherry-picked window caveats are mandatory: state the start/end dates and acknowledge regime dependence.
- Costs assumption must be quoted in the verdict.

---

## 6. SKILL.md Draft

````markdown
---
name: stock-backtest
description: Use when backtesting a stock or ETF — indicator-rule strategy (KDJ golden cross, SMA crossover, RSI mean reversion, Bollinger Bands, MACD), signal validation / event study (does signal X actually predict positive forward returns), or investor-persona backtest (Lynch / Graham / Burry / Druckenmiller-lite with quarterly fundamentals). Outputs equity curve, Sharpe, CAGR, max drawdown, Calmar, win rate, profit factor, trade list, and Markdown verdict. Single ticker, daily bars. Not for multi-stock portfolio backtests.
---

# Stock Backtest

## Overview

Backtest a single-ticker, rule-based strategy or an investor-persona allocation
rule on historical daily bars. Run a statistical event-study on a signal.
This skill always reports both in-sample and out-of-sample metrics, deducts
transaction costs, and refuses to label a strategy "profitable" when out-of-
sample evidence does not support it.

This skill is single-ticker only. For multi-stock portfolio backtests, walk-
forward parameter optimization, or strategies requiring complex fundamentals
(Buffett owner earnings, Munger ROIC time series, Fisher scuttlebutt, Wood
TAM models), state the limitation rather than producing a degraded result.

End user-facing reports with: `Not investment advice -- for your own research.`

## Request Gate

Before running, confirm:

`Please confirm ticker, mode (indicator strategy / signal validation / persona), strategy or persona name, backtest window (start and end), transaction-cost assumption (default 5bps commission + 5bps slippage per side), and benchmark (default SPY).`

For mode = indicator strategy, also confirm which built-in strategy and any
non-default parameter values. For mode = signal, confirm signal name and
primary holding horizon. For mode = persona, confirm rebalance frequency
(quarterly / annual).

If the user names a persona not supported in v1 (Buffett / Munger / Fisher /
Wood), explain that v1 cannot honestly run that persona because the
fundamentals layer is incomplete, and offer the supported personas (Lynch /
Graham / Burry / Druckenmiller-lite) as alternatives or offer to run the
strategy in indicator mode using a price-based proxy with a clear disclaimer.

## Workflow

1. Resolve ticker, window, mode, parameters.
2. Run the script:
   `python scripts/backtest.py <TICKER> --mode <m> --strategy/--signal/--persona <name> --start <YYYY-MM-DD> --end <YYYY-MM-DD> --key-file <path> --output-dir <path>`
   Use `--output-dir auto` on Claude.ai web.
3. Read the produced `{TICKER}_backtest_bundle.json`.
4. If `data_quality.data_health != "good"`, surface the data gap in the
   report's Data Health section and downgrade verdict confidence.
5. Produce the Standalone Backtest Report below.

## Standalone Backtest Report Structure

1. `## Backtest Setup` — ticker, mode, strategy/persona/signal, window,
   parameters, costs assumption, benchmark.
2. `## Data Health` — data sources, missing bars, fundamentals coverage if
   relevant, any data caveats.
3. `## Headline Metrics` — table with full / in-sample / out-of-sample
   columns for CAGR, Sharpe, Sortino, MDD, Calmar, win rate, profit factor,
   trades, exposure %.
4. `## Equity Curve` — embed the PNG.
5. `## Trade Analysis` (indicator + persona modes) — best 3 / worst 3 trades,
   holding-period distribution, hit-rate by year, monthly returns heatmap
   discussion.
   `## Signal Statistics` (signal mode) — forward return by horizon,
   t-stat, comparison to baseline, embed signal-distribution PNG.
6. `## Overfitting And Robustness` — in-sample vs out-of-sample degradation,
   parameter sensitivity if reported, regime dependence, sample-size caveat.
7. `## Reality Check` — single-ticker caveat, transaction costs, no slippage
   beyond model, no survivorship bias modeled (n/a for single ticker but
   state explicitly), no tax modeling, no margin/borrow modeling.
8. `## Verdict` — one of:
   - *Strategy showed positive edge in-sample AND out-of-sample with realistic costs* (highest confidence)
   - *Strategy showed positive edge but only in-sample* (likely overfit or regime change)
   - *Strategy underperformed Buy&Hold* (regardless of absolute return)
   - *Inconclusive — insufficient data or signal too rare*
   Verdict must quote the cost assumption and out-of-sample metric.
9. `## Next Tests` — explicit "what to run next" suggestions: e.g. test the
   same strategy on 3 other tickers in the same sector; try a different
   parameter range; extend window to include a different macro regime.
10. Final line: `Not investment advice -- for your own research.`

## Hard Rules

- Always report in-sample AND out-of-sample metrics in the headline table.
- Never produce a `Strategy works` verdict if `degradation_ratio < 0.4`.
- Always state the transaction cost assumption in the Verdict section,
  not buried in a footnote.
- Always compare to BOTH Buy&Hold and the benchmark.
- Always state the data window in the Verdict.
- Never extrapolate single-ticker results to "this strategy is good" or
  "this persona is good".
- If `--position-sizing all-in` was used (default), state that the equity
  curve assumes 100% concentration when in-trade, which is unrealistic for
  a real portfolio.
- If persona mode and `fundamentals_data_quality != "good"`, downgrade the
  verdict and explain what fundamentals were missing.

## Data Failure And Fallback Rules

- If ticker OHLCV fetch fails, abort and report. Do not run the backtest.
- If benchmark fetch fails, run the backtest with only Buy&Hold comparison
  and disclose the missing benchmark.
- If persona fundamentals fetch fails for ALL quarters, return the
  `data_insufficient` bundle and refuse to produce numeric metrics.
- If persona fundamentals fetch fails for SOME quarters, document the
  missing quarters and treat them as cash periods (do not interpolate).

## Output Rules

- Match the user's language.
- Provide the Markdown report inline AND link to the equity curve PNG,
  trades CSV, and bundle JSON paths.
- Do not paste the entire trades CSV into the report — show top 3 / bottom 3
  trades and reference the CSV path.
- For DOCX output, embed the equity curve PNG and the headline-metrics
  table; reference the trades CSV but do not embed it.
````

---

## 7. `references/strategy-registry.md` (Outline)

For each built-in strategy: name, pseudocode of entry rule, pseudocode of exit
rule, list of tunable params with defaults, known failure mode (e.g. KDJ
golden cross fails in strong trends), suggested out-of-sample test.

## 8. `references/persona-criteria-v1.md` (Outline)

For each supported persona: data fields required, exact threshold rules,
embargo policy, what happens when a field is missing, citation back to the
original `stock-investor-<persona>/SKILL.md` so the criteria stay aligned.

## 9. `references/overfitting-checklist.md` (Outline)

Reusable checklist the SKILL.md applies: in-sample / out-of-sample degradation
threshold, parameter-mining detection, single-ticker caveat, regime dependence
test (split by VIX regime if available), monte carlo trade shuffle for
statistical significance of trade-level edge.

---

## 10. Testing Plan

After implementation, smoke tests to run before declaring v1 done:

1. `python backtest.py NVDA --mode indicator --strategy kdj_golden_cross --start 2020-01-01 --end 2025-12-31 --key-file ./key.txt --output-dir ./outputs/backtest-smoke-nvda-kdj`
   → expect: bundle.json + equity_curve.png + trades.csv. Manually inspect the trades CSV for look-ahead (entry date should be one bar after signal date).

2. Same as #1 but `--strategy sma_50_200_cross` → fewer trades, lower win rate, higher avg holding days.

3. `python backtest.py NVDA --mode signal --signal kdj_golden_cross --holding-days 20 --start 2020-01-01 --end 2025-12-31` → expect: no trades.csv (signal mode), signal_distribution.png + bundle with `signal_stats`. Manually verify event count matches a hand-count from the technical bundle.

4. `python backtest.py MSFT --mode persona --persona lynch --rebalance-frequency quarterly --start 2018-01-01 --end 2025-12-31 --key-file ./key.txt` → expect: bundle includes persona block with rebalances ≈ 32 quarters.

5. `python backtest.py NVDA --mode persona --persona buffett` → expect: exit code 6, bundle.json contains `data_insufficient` block with explanation.

6. Out-of-sample sanity: run #1 with `--in-sample-fraction 0.5` and confirm `summary_in_sample` and `summary_out_of_sample` are both present and computed correctly (sum of in-sample + out-of-sample returns approximately equals full).

7. Cost sanity: re-run #1 with `--commission-bps 0 --slippage-bps 0` and confirm bundle gets `"costs.warning"`. Returns should improve modestly.

8. SKILL.md walkthrough: read the new SKILL.md end-to-end with the bundle from #1 in hand, generate a Markdown verdict on paper, and verify all "Hard Rules" are satisfied.

---

## 11. Open Questions

1. **Risk-free rate in cash periods (persona mode)** — v1 assumes 0%. Real
   answer is 3-month T-bill (~4-5% in 2024). Cleanest fix: pull `^IRX` from
   yfinance or FRED's `DGS3MO` and accrue daily during cash periods.
   Include in v1 or defer to v2?

2. **Survivorship bias** — single-ticker backtests don't really have this,
   but the Verdict's "Reality Check" should still note that the backtested
   ticker is one that exists today (didn't go to zero). Want me to phrase
   this proactively in SKILL.md, or leave it to the user?

3. **Slippage model** — v1 uses a flat bps. More realistic: half-spread +
   square-root of volume model. Defer to v2?

4. **Charts library** — `fetch_price_charts.py` already uses matplotlib. The
   backtest equity curve will use the same. Confirmed?

5. **Persona criteria editability** — `references/persona-criteria-v1.md`
   stores the thresholds as Markdown for human review; the script reads them
   from a parallel `persona-criteria-v1.yaml` for actual execution. Two files
   stay in sync via review. OK with this split, or do you want criteria
   hardcoded in Python only?

6. **Naming** — `stock-backtest/` or `stock-backtest-analysis/` to match the
   `*-analysis` naming convention used by 7 of the existing skills? I went
   with `stock-backtest/` because "backtest analysis" is awkward; happy to
   change.

7. **README + CROSS_PLATFORM.md updates** — add backtest to the skill map
   and install instructions now, or wait until backtest skill is built and
   tested?

8. **Migration interaction** — when the superpower migration runs, this
   becomes `modules/backtest.md` and the script moves to
   `stock-analysis/scripts/backtest.py`. The `sys.path` shim in
   `backtest.py` becomes unnecessary (script is in the same folder as
   `data_provider.py`). Want me to write the script so it works in BOTH
   layouts from day one (try local import first, fall back to sibling
   import)? That makes the migration zero-edit on the Python side.

---

## 12. Execution Order (When You Approve)

1. Add `get_fundamentals_history()` to `stock-analysis/scripts/data_provider.py`. Smoke test against MSFT (known good fundamentals coverage).
2. Create `stock-backtest/` folder with the layout in §1.
3. Write `scripts/backtest.py` — common framework, then indicator mode, signal mode, persona mode in that order.
4. Write `references/strategy-registry.md`, `persona-criteria-v1.md` (+ YAML), `overfitting-checklist.md`.
5. Write `SKILL.md` using the §6 draft.
6. Write `agents/openai.yaml`.
7. Run smoke tests §10 #1–#7.
8. Walk through SKILL.md with bundle from #1 (smoke test #8).
9. Update `README.md` + `README.zh-CN.md` skill map (skill count 18 → 19, add Backtesting row to the differences table — "Now supported").
10. Update `tools/build_claude_zips.ps1` — no change needed; it auto-iterates `stock-*` folders. Verify the new folder gets zipped.
11. Update `docs/CROSS_PLATFORM.md` install commands if needed.
12. Mark v2 backlog: full Buffett/Munger/Fisher/Wood, multi-stock portfolio, walk-forward parameter search, risk-free rate accrual, square-root slippage.

Estimated work: data_provider extension ≈ 1 file. backtest.py ≈ 1 file, ~600-800 LOC. SKILL.md ≈ 1 file. 3 references files. agents/openai.yaml ≈ 1 file. README touch-ups ≈ 2 files. Smoke tests ≈ 8 invocations.
