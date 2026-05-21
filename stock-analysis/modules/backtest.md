# Backtest Module

> Internal module of the orchestrator. Loaded on demand by the
> orchestrator when the report needs this section, or when the user
> invokes it directly.
>
> Originally shipped as the standalone skill `stock-backtest` (pre-2026-05-merge).


## Overview

Backtest a single-ticker, rule-based strategy or an investor-persona allocation rule on historical daily bars. Run a statistical event-study on a signal. This skill always reports both in-sample and out-of-sample metrics, deducts transaction costs, and refuses to label a strategy "profitable" when out-of-sample evidence does not support it.

Single-ticker only. For multi-stock portfolio backtests, walk-forward parameter optimization, or strategies requiring complex fundamentals (Buffett owner earnings, Munger ROIC time series, Fisher scuttlebutt, Wood TAM models), state the limitation rather than producing a degraded result.

End user-facing reports with: `Not investment advice -- for your own research.`

## Request Gate

Before running, confirm:

`Please confirm ticker, mode (indicator strategy / signal validation / persona), strategy or persona name, backtest window (start and end), transaction-cost assumption (default 5bps commission + 5bps slippage per side), and benchmark (default SPY).`

For `mode = indicator`, also confirm which built-in strategy from `references/strategy-registry.md` and any non-default parameter values.

For `mode = signal`, confirm signal name and the primary forward holding horizon (default 20 trading days).

For `mode = persona`, confirm rebalance frequency (quarterly / annual) and which persona. If the user names a v1-unsupported persona (Buffett / Munger / Fisher / Wood), explain that v1 cannot honestly run that persona because the fundamentals layer is incomplete (see `references/persona-criteria-v1.md`) and offer the supported personas (Lynch / Graham / Burry / Druckenmiller-lite) as alternatives. Do not silently substitute.

If the user enters a bare ticker like `NVDA backtest`, ask the combined question rather than defaulting.

## Workflow

1. Resolve ticker, window, mode, parameters via the Request Gate.
2. Run the script:
   ```
   python scripts/backtest.py <TICKER> --mode <m> \
     --strategy/--signal/--persona <name> \
     --start <YYYY-MM-DD> --end <YYYY-MM-DD> \
     --key-file <path-to-key.txt> \
     --output-dir <path-or-"auto">
   ```
   Use `--output-dir auto` in Claude.ai web. Pass `--no-charts` if matplotlib isn't available.
3. Read the produced `{TICKER}_backtest_bundle.json`.
4. If `data_quality.data_health != "good"`, surface the gap in Data Health and downgrade verdict confidence. If `persona_meta.fundamentals_data_quality == "partial"`, list the missing fields.
5. Produce the Standalone Backtest Report (below).

## Standalone Backtest Report Structure

When invoked directly by a user, produce a self-contained Markdown report in the user's language with this structure:

1. **`## Backtest Setup`** — ticker, mode, strategy/persona/signal, window, parameters, costs assumption, benchmark, initial capital. Quote the exact `python` command run.
2. **`## Data Health`** — data sources for ticker and benchmark, missing bars, fundamentals coverage if persona, any data caveats from the provider attempts list.
3. **`## Headline Metrics`** — table with **three columns** (full / in-sample / out-of-sample) showing: total return, CAGR, Sharpe, Sortino, max drawdown, Calmar, trades, win rate, profit factor, avg holding days, exposure %. Add a separate row for Buy&Hold and Benchmark totals.
4. **`## Equity Curve`** — embed `{TICKER}_equity_curve.png` with a one-line caption naming the strategy and window.
5. For indicator + persona modes — **`## Trade Analysis`**: best 3 / worst 3 trades from the CSV, holding-period distribution summary, exit-reason breakdown (signal / stop_loss / take_profit / end_of_window), monthly returns commentary. Reference `{TICKER}_trades.csv` for the full list. Do NOT paste the entire CSV into the report.
   For signal mode — **`## Signal Statistics`**: forward returns by horizon (table), t-stats, comparison to baseline, embed `{TICKER}_signal_distribution.png`. Quote the `edge_vs_baseline.significant_at_p05` flag.
6. **`## Overfitting And Robustness`** — quote `overfitting_diagnostics.interpretation`, in-sample vs out-of-sample CAGR delta, degradation ratio, params_user_supplied flag. Apply the verdict rules from `references/overfitting-checklist.md` items 1, 2.
7. **`## Reality Check`** — single-ticker caveat, transaction costs in basis points (quoted explicitly), no slippage beyond model, no survivorship-bias modeling, no tax modeling, no margin / borrow. Apply checklist items 3-6.
8. **`## Verdict`** — one of these phrasings (NOT one Claude invents):
   - *Strategy showed positive edge in-sample AND out-of-sample, after realistic costs, on this single ticker in this window. Suggest re-test on N peers + a different window before sizing capital.*
   - *Strategy showed positive edge in-sample only; out-of-sample weak. Likely overfit or regime change.*
   - *Strategy outperformed Buy&Hold but underperformed the benchmark.*
   - *Strategy underperformed Buy&Hold.*
   - *Inconclusive — insufficient trades / signals too rare / fundamentals incomplete.*

   Verdict must quote: the cost assumption, the window, the out-of-sample CAGR.
9. **`## Next Tests`** — explicit "what to run next": same strategy on 3 sector peers; extend window through a different macro regime; try one parameter perturbation to test robustness.
10. **Final line:** `Not investment advice -- for your own research.`

## Hard Rules

- Always report in-sample AND out-of-sample metrics in the headline table.
- Never produce a "strategy works" verdict if `degradation_ratio < 0.4`.
- Always quote the transaction cost assumption in the Verdict, not in a footnote.
- Always compare to BOTH Buy&Hold and the benchmark.
- Always state the data window in the Verdict.
- Never extrapolate single-ticker results to "this strategy is good" or "this persona is good".
- If `--position-sizing all-in` (default), state that the equity curve assumes 100% concentration when in-trade, which is unrealistic for a real portfolio.
- If persona mode and `fundamentals_data_quality != "good"`, downgrade the verdict and explain what fundamentals were missing.
- If costs are zero, the headline Reality Check must call out `frictionless backtest — not realistic`.
- If signal mode and `edge_vs_baseline.significant_at_p05` is false, frame as "interesting but not statistically significant" not "edge found".
- Survivorship caveat is mandatory in Reality Check even for single-ticker (the ticker exists today; selection by survival).

## Data Failure And Fallback Rules

- If ticker OHLCV fetch fails (exit code 3), abort and report the data gap. Do not run the backtest.
- If benchmark fetch fails, run with Buy&Hold-only comparison and disclose the missing benchmark in Data Health.
- If persona fundamentals fetch fails for ALL quarters (exit code 6), return the `data_insufficient` bundle and refuse to produce numeric metrics. Offer to switch to indicator mode.
- If persona fundamentals are partial (some quarters missing), document the missing quarters; the script treats them as cash periods automatically.
- If exit code is 5 (unknown strategy / signal / persona), list the available registry entries from `references/strategy-registry.md` or `persona-criteria-v1.md` and ask the user to pick.
- If the persona is in `PERSONA_DEFERRED` (Buffett / Munger / Fisher / Wood), the bundle's explanation block must be reproduced in the report verbatim with no numeric verdict.

## Output Rules

- Match the user's language.
- Provide the report inline AND link to the equity curve PNG, trades CSV, and bundle JSON paths.
- Show top 3 / bottom 3 trades; reference the CSV path for the rest.
- For full SOP integration: the `stock-analysis` orchestrator may invoke this skill to validate a strategy idea surfaced in technical analysis. In that case, follow the SOP Integration Mode below — not the full Standalone Report. The validation result is embedded into the HTML report as the Backtest Validation sub-section under Technical.

## SOP Integration Mode

When the orchestrator calls this module as **step 6 of the full SOP workflow**, behave differently from the Standalone Backtest Report:

**Trigger** — the Technical section identified a strongest actionable signal (e.g., KDJ golden cross, SMA50-200 cross, RSI oversold). The orchestrator invokes the script in **signal mode only** with a 5-year window:

```
scripts/backtest.py <TICKER> --mode signal --signal <identified_signal> \
  --start <today-minus-5y> --end <today> \
  --key-file <key> --output-dir <out> --no-charts
```

**Output shape** — produce a compact **Backtest Validation** sub-section that lives inside the Technical chapter (not a standalone backtest report). Required content:

1. One paragraph: which signal was tested, over what window, with what assumptions.
2. One table with rows for +5d, +20d, +60d forward horizons; columns for the signal's hit rate, mean return, t-stat, and the same metrics from the baseline (random dates in the same window).
3. One sentence on the `significant_at_p05` flag and what it implies for the technical thesis.
4. One sentence on what the result says about the technical setup — does the signal historically work on this ticker, or is the current setup a low-base-rate bet?
5. Link to the bundle JSON path (the orchestrator passes the output dir).

**Do NOT** in SOP integration mode:
- Produce the 10-section Standalone Backtest Report
- Run indicator or persona mode (those are explicit user requests, not SOP defaults)
- Run more than one signal validation per report unless the user asks
- Block the report if signal validation fails — note the failure and continue

**If no registered signal matches the technical thesis** (e.g., technical analysis says "watching for a break above $X resistance"; no such signal in the registry), skip step 6 and write one line in the report: "No registered signal matches the current technical thesis; backtest validation not run."

## Example Commands

Indicator strategy:
```powershell
python scripts/backtest.py NVDA --mode indicator --strategy kdj_golden_cross `
  --start 2020-01-01 --end 2025-12-31 `
  --key-file .\key.txt --output-dir .\outputs\NVDA_backtest_kdj
```

Signal validation:
```powershell
python scripts/backtest.py NVDA --mode signal --signal kdj_golden_cross `
  --holding-days 20 --start 2020-01-01 --end 2025-12-31 `
  --key-file .\key.txt --output-dir .\outputs\NVDA_signal_kdj
```

Persona backtest (Lynch on MSFT):
```powershell
python scripts/backtest.py MSFT --mode persona --persona lynch `
  --rebalance-frequency quarterly `
  --start 2018-01-01 --end 2025-12-31 `
  --key-file .\key.txt --output-dir .\outputs\MSFT_persona_lynch
```

Deferred persona (returns data_insufficient with explanation):
```powershell
python scripts/backtest.py NVDA --mode persona --persona buffett
# exit code 6; bundle contains explanation and supported_personas list
```

## v2 Backlog

- Multi-stock portfolio backtest (`--tickers AAPL,MSFT,GOOG`)
- Walk-forward parameter search (`--param-grid` + holdout split)
- Risk-free rate accrual during cash periods (3-month T-bill from FRED `DGS3MO`)
- Square-root-impact slippage model (`--slippage-model sqrt`)
- Full Buffett / Munger / Fisher / Wood personas (requires owner-earnings extension to `data_provider.get_owner_earnings_history()`)
- Monte Carlo trade-shuffle for trade-level statistical significance
- Regime-conditional metrics (split metrics by VIX regime or yield-curve regime)
