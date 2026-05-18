# Strategy Registry (v1)

Five built-in indicator strategies. All strategies trade single-ticker, all-in / all-out, decisions on bar `t` execute at bar `t+1` open, costs deducted on both sides.

---

## `kdj_golden_cross`

| Item | Value |
|---|---|
| Entry | `K > D` AND `K_prev <= D_prev` AND `K < 30` AND `D < 30` |
| Exit | Death cross (`K < D` AND `K_prev >= D_prev`) OR stop-loss OR take-profit |
| Tunable params | `stop_loss` (default 0.05), `take_profit` (default 0.15) |
| Typical # trades over 5y | 8-20 on a moderately trending name |
| Known failure mode | Underperforms in strong uptrends — exits early on minor death crosses; whipsaws in tight ranges. |
| Suggested out-of-sample | Run on a non-overlapping later window OR a sector peer of the original ticker. |

## `sma_50_200_cross`

| Item | Value |
|---|---|
| Entry | `SMA50 > SMA200` AND `SMA50_prev <= SMA200_prev` (golden cross) |
| Exit | `SMA50 < SMA200` AND `SMA50_prev >= SMA200_prev` (death cross) |
| Tunable params | none |
| Typical # trades over 5y | 2-6 |
| Known failure mode | Late entries and late exits; meaningful drawdowns from peak to death cross. Useless on mean-reverting tickers. |
| Suggested out-of-sample | Run on a flat/ranging ticker (e.g. an old industrial) vs a trending one. |

## `rsi_mean_reversion`

| Item | Value |
|---|---|
| Entry | `RSI(14) < 30` AND `RSI(14)_prev >= 30` |
| Exit | `RSI(14) > 70` AND `RSI(14)_prev <= 70` OR stop-loss |
| Tunable params | `stop_loss` (default 0.08) |
| Typical # trades over 5y | 10-30 |
| Known failure mode | Catches falling knives in strong downtrends. Stop-loss is the only thing preventing ruin. |
| Suggested out-of-sample | Tickers from different regimes — bull market and bear market portions. |

## `bb_lower_bounce`

| Item | Value |
|---|---|
| Entry | `close < bb_lower` AND `close_prev >= bb_lower_prev` |
| Exit | `close > bb_mid` OR stop-loss |
| Tunable params | `stop_loss` (default 0.05) |
| Typical # trades over 5y | 15-40 |
| Known failure mode | Similar to RSI mean reversion. BB bands widen during volatile periods, making the entry condition rare. |
| Suggested out-of-sample | Mean-reverting vs trending tickers; compare hit rates. |

## `macd_signal_cross`

| Item | Value |
|---|---|
| Entry | `MACD > signal` AND `MACD_prev <= signal_prev` AND `signal > 0` |
| Exit | `MACD < signal` AND `MACD_prev >= signal_prev` |
| Tunable params | none |
| Typical # trades over 5y | 6-15 |
| Known failure mode | Lag inherent to EMAs. Misses early-cycle entries; sometimes flags fakeouts in chop. |
| Suggested out-of-sample | Trending names (mega-cap tech) work; mean-reverting names fail. |

---

## Signal-only (`--mode signal`) additions

Beyond the entry conditions above, signal mode also supports:

| Signal | Condition |
|---|---|
| `rsi_oversold` | `RSI(14) < 30` (no requirement for prior bar >= 30) |
| `bb_squeeze_breakout` | BB width <= 6-month low for prior bar AND `close > bb_upper` today |
| `volume_spike_2x` | `volume >= 2 * vol_ma20` |
| `gap_up_3pct` | `open >= 1.03 * close_prev` |
| `new_52w_high` | `close >= max(close over trailing 252 bars)` |

Signal mode reports forward returns at +1d / +5d / +10d / +20d / +60d horizons. `--holding-days` sets the primary horizon used in the headline `edge_vs_baseline` block.

---

## How to add a new strategy

1. Write a function in `backtest.py`:
   ```python
   def strategy_my_new(df: pd.DataFrame, params: dict) -> tuple[pd.Series, pd.Series, dict]:
       enter = ...
       exit_ = ...
       return enter, exit_, {"stop_loss": float(params.get("stop_loss", 0.05))}
   ```
2. Register it in `STRATEGY_REGISTRY` at the top of the strategies section.
3. Add a row to this file with the entry / exit / params / failure mode.
4. Add a smoke test command to the SKILL.md examples.

For signal mode, register in `SIGNAL_REGISTRY` and add a row to the signal table above.
