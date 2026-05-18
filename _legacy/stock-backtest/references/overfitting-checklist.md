# Overfitting and Reality-Check Checklist

A backtest can pass every sanity check and still be useless. This checklist is what the SKILL.md applies to every Verdict before declaring a strategy worth pursuing. Apply all items, not the ones that happen to favor the conclusion.

---

## 1. In-sample vs out-of-sample

`backtest.py` always reports both metric sets (`summary_in_sample` and `summary_out_of_sample`). The script also computes a `degradation_ratio = out_of_sample_cagr / in_sample_cagr` and an interpretation string.

| degradation_ratio | Interpretation | What the SKILL.md verdict should say |
|---|---|---|
| ≥ 0.7 | Out-of-sample tracked in-sample | "Strategy generalized in this window. Confidence: moderate, single-ticker." |
| 0.4 to 0.7 | Moderate decay | "Some out-of-sample decay. Possible regime drift. Re-test on different ticker before pursuing." |
| 0 to 0.4 | Materially weaker | "Out-of-sample materially weaker. Likely overfit OR regime change. Do NOT label as working." |
| < 0 | OOS negative while IS positive | "High overfit risk. Strategy failed out-of-sample." |
| n/a | In-sample CAGR ≤ 0 | "Strategy did not work in-sample. Verdict: negative." |

The hard rule in SKILL.md: **never produce a "strategy works" verdict if `degradation_ratio < 0.4`**.

## 2. Parameter mining detection

If the user supplied params (`--params '{"stop_loss":0.04}'`), `bundle["overfitting_diagnostics"]["params_user_supplied"] = true`. The Verdict must acknowledge that user-supplied params might reflect prior optimization on the same ticker — i.e. the in-sample window is no longer truly out-of-sample to the user's prior beliefs.

If the user did NOT supply params (defaults used), this risk is lower but not zero — the defaults themselves were chosen by someone, somewhere.

v1 does NOT run automatic parameter sweeps. v2 may add `--param-grid` and `--walk-forward`, in which case `params_searched_count` becomes the relevant signal: more searches = higher overfit risk.

## 3. Single-ticker caveat

Mandatory. Always state. A strategy that works on NVDA in 2020-2025 says nothing about whether it works on AAPL, on bonds, in the 2000s, or post-2026. N=1 is not evidence.

## 4. Cherry-picked window caveat

Mandatory. The window `--start`..`--end` was chosen, not random. Verdict must quote start and end dates and note: "Different windows may flip the conclusion. Suggest re-running on a window covering at least one bear market."

## 5. Transaction cost honesty

The Verdict must quote the cost assumption (`commission_bps + slippage_bps`). If both are zero, the bundle gets `"costs.warning": "frictionless backtest — not realistic"` and the SKILL.md must call this out as the headline caveat, not a footnote.

5bps + 5bps = 10bps per side = 20bps round-trip is a reasonable retail assumption (Schwab/IBKR-tier; minimal price impact). For institutional-size positions or illiquid names, double or triple it.

## 6. Survivorship bias

For single-ticker backtests this is muted — by definition the ticker survives. But the verdict's Reality Check should note: "The backtested ticker exists today; this is not a screen of all tickers that started in 2020. A strategy that 'works' here might be selecting for survivors after the fact."

## 7. Persona-mode fundamentals coverage

For persona mode, check `persona_meta.fundamentals_data_quality`. If `partial`, list the missing fields and downgrade confidence — a Lynch persona without dividend data is materially weaker than one with it.

## 8. Persona-mode quarter count

If `quarters_available < 8`, the script returns `insufficient_fundamentals_history` and exits. SKILL.md should explain that 8 quarters is the minimum for TTM + YoY growth math.

## 9. Signal-mode statistical significance

For signal mode, look at `edge_vs_baseline.significant_at_p05`. If false, the signal does not have a statistically distinguishable edge over random dates in the same window. Frame as "interesting but not significant" rather than "edge found".

| t-stat (primary horizon) | Interpretation |
|---|---|
| > 2.58 | p < 0.01; meaningful in this window |
| 1.96 - 2.58 | p < 0.05; suggestive |
| 1.0 - 1.96 | weak; not significant |
| < 1.0 | no edge |

## 10. Strategy did better than Buy&Hold?

Always compare to `buy_and_hold.total_return` AND `benchmark.total_return`. A strategy with 15% CAGR is impressive only if Buy&Hold did 8%. If Buy&Hold did 25%, the strategy underperformed by being out of the market.

The `alpha.vs_buy_and_hold_total` field captures this. If negative, the verdict must say "underperformed Buy&Hold" regardless of how absolute returns look.

## 11. Exposure-adjusted comparison

If `exposure_pct < 0.5`, the strategy was out of the market half the time. Lower absolute returns are expected. Compare `return per unit of exposure` or note explicitly that the strategy reduced drawdown by reducing exposure.

## 12. Regime dependence

Did the window contain a 2022-style bear market, a 2020-style crash, or only the 2023-2024 melt-up? Strategies that only saw a melt-up are not validated for downturns.

## 13. Capacity

A persona backtest on a $50M micro-cap that hits $10M dollar volume on a typical day cannot be scaled up. v1 does not model market impact. Note in the verdict for illiquid names.

---

## Verdict template

When the SKILL.md writes the Verdict section, it should explicitly cover items 1, 3, 4, 5, 6, 10. If any of those checks fail or are concerning, the verdict cannot be "strategy works".

Acceptable verdict phrasings:

- *"Strategy showed positive edge in-sample AND out-of-sample, after realistic costs, on this single ticker in this window. Suggest re-test on N peers + a different window before sizing capital."*
- *"Strategy showed positive edge in-sample only; out-of-sample weak (degradation_ratio = X). Likely overfit or regime change."*
- *"Strategy outperformed Buy&Hold but underperformed the benchmark. Conclusion: stock-picking added value but only relative to itself."*
- *"Inconclusive — insufficient trades / signals too rare / fundamentals incomplete."*

Unacceptable:

- *"This strategy works."* (single-ticker; never)
- *"Sharpe of X.X proves the strategy."* (no, costs / window / OOS first)
- *"Backtested returns are X%."* (without quoting costs and window)
