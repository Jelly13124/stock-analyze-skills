#!/usr/bin/env python3
"""Single-ticker backtest engine for the stock-backtest skill.

Supported modes:
  * indicator  -- rule-based entry/exit strategy on daily bars (KDJ, SMA, RSI, BB, MACD)
  * signal     -- event study; statistical edge of a signal across forward horizons
  * persona    -- investor-persona quarterly allocation rule using fundamentals history

Outputs (in --output-dir):
  {TICKER}_backtest_bundle.json    summary metrics + setup
  {TICKER}_equity_curve.png        equity vs Buy&Hold vs benchmark (indicator + persona)
  {TICKER}_trades.csv              round-trip trade log     (indicator + persona)
  {TICKER}_signal_distribution.png forward-return histogram (signal mode)

Integrity rules (hardcoded; not user-configurable):
  * Signal computed on bar t executes on bar t+1 open (no same-bar entry).
  * Costs (commission + slippage) deducted from each entry and exit price.
  * Persona mode applies a 60-day embargo on fundamentals reporting date.
  * In-sample / out-of-sample metrics always reported separately.
  * Costs of zero emit a "frictionless backtest" warning in the bundle.

This script imports data_provider from either:
  * the same scripts/ directory (post-superpower-migration layout), or
  * the sibling ../../stock-analysis/scripts/ folder (current sibling layout).
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

# --- data_provider import shim (works in both folder layouts) ---------------
_here = Path(__file__).resolve().parent
_candidates = [
    _here,                                          # post-migration: scripts/ next to data_provider.py
    _here.parent.parent / "stock-analysis" / "scripts",  # sibling layout (current)
]
for _candidate in _candidates:
    if (_candidate / "data_provider.py").exists() and str(_candidate) not in sys.path:
        sys.path.insert(0, str(_candidate))
        break

from data_provider import (  # noqa: E402
    ensure_yfinance,
    get_daily_ohlcv,
    get_fundamentals_history,
    get_output_dir,
    load_keys,
)

try:
    import pandas as pd
except ImportError:  # pragma: no cover
    print("ERROR: pandas is required. pip install pandas", file=sys.stderr)
    sys.exit(2)

# matplotlib is optional - we degrade to no-charts mode if it's missing
try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    _HAS_MPL = True
except ImportError:
    _HAS_MPL = False


# ===========================================================================
# Indicator helpers
# ===========================================================================


def sma(s: pd.Series, n: int) -> pd.Series:
    return s.rolling(n, min_periods=n).mean()


def ema(s: pd.Series, n: int) -> pd.Series:
    return s.ewm(span=n, adjust=False).mean()


def rsi(close: pd.Series, n: int = 14) -> pd.Series:
    delta = close.diff()
    gain = delta.clip(lower=0).rolling(n, min_periods=n).mean()
    loss = (-delta.clip(upper=0)).rolling(n, min_periods=n).mean()
    rs = gain / loss.replace(0, math.nan)
    return 100 - (100 / (1 + rs))


def kdj(high: pd.Series, low: pd.Series, close: pd.Series, n: int = 9, m1: int = 3, m2: int = 3) -> tuple[pd.Series, pd.Series, pd.Series]:
    low_n = low.rolling(n, min_periods=n).min()
    high_n = high.rolling(n, min_periods=n).max()
    rsv = (close - low_n) / (high_n - low_n).replace(0, math.nan) * 100
    k = rsv.ewm(alpha=1 / m1, adjust=False).mean()
    d = k.ewm(alpha=1 / m2, adjust=False).mean()
    j = 3 * k - 2 * d
    return k, d, j


def macd(close: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> tuple[pd.Series, pd.Series, pd.Series]:
    macd_line = ema(close, fast) - ema(close, slow)
    sig = ema(macd_line, signal)
    hist = macd_line - sig
    return macd_line, sig, hist


def bollinger(close: pd.Series, n: int = 20, k: float = 2.0) -> tuple[pd.Series, pd.Series, pd.Series]:
    mid = close.rolling(n, min_periods=n).mean()
    std = close.rolling(n, min_periods=n).std()
    upper = mid + k * std
    lower = mid - k * std
    return upper, mid, lower


# ===========================================================================
# Data loading
# ===========================================================================


def fetch_daily_df(ticker: str, keys: dict, start: str, end: str) -> tuple[pd.DataFrame, dict]:
    """Returns (DataFrame indexed by date, provider_meta_dict)."""
    start_dt = datetime.strptime(start, "%Y-%m-%d")
    end_dt = datetime.strptime(end, "%Y-%m-%d")
    days_needed = (end_dt - start_dt).days + 30
    bundle = get_daily_ohlcv(ticker, keys, days=days_needed)
    meta = {k: v for k, v in bundle.items() if k != "rows"}
    if bundle.get("status") != "ok":
        return pd.DataFrame(), meta
    df = pd.DataFrame(bundle["rows"])
    df["date"] = pd.to_datetime(df["date"].str[:10])
    df = df.set_index("date").sort_index()
    df = df.loc[(df.index >= start_dt) & (df.index <= end_dt)]
    return df, meta


def fetch_fundamentals(ticker: str, keys: dict) -> dict:
    return get_fundamentals_history(ticker, keys)


# ===========================================================================
# Trade simulator
# ===========================================================================


def simulate_trades(
    df: pd.DataFrame,
    entry_signal: pd.Series,
    exit_signal: pd.Series,
    initial_capital: float,
    commission_bps: float,
    slippage_bps: float,
    stop_loss: float | None = None,
    take_profit: float | None = None,
) -> tuple[pd.DataFrame, pd.Series, pd.Series]:
    """Run the all-in / all-out simulator. Decisions on bar t execute at bar t+1 open.

    Returns: (trades_df, equity_series, position_series).
    """
    cost_per_side = (commission_bps + slippage_bps) / 10000.0
    open_p = df["open"].values
    high_p = df["high"].values
    low_p = df["low"].values
    close_p = df["close"].values
    dates = df.index
    n = len(df)

    cash = initial_capital
    shares = 0.0
    entry_price = None
    entry_date = None
    trades: list[dict] = []
    equity_curve: list[float] = []
    position_curve: list[float] = []

    entry_arr = entry_signal.values
    exit_arr = exit_signal.values

    for t in range(n):
        # Same-bar stop/take check (intrabar) -- uses high/low of current bar
        # but only if a position was opened on a PRIOR bar (entry_date < dates[t]).
        if shares > 0 and entry_price is not None:
            if stop_loss is not None and low_p[t] <= entry_price * (1 - stop_loss):
                exit_price = entry_price * (1 - stop_loss) * (1 - cost_per_side)
                pnl = shares * exit_price - shares * entry_price * (1 + cost_per_side)
                trades.append({
                    "entry_date": entry_date.strftime("%Y-%m-%d"),
                    "exit_date":  dates[t].strftime("%Y-%m-%d"),
                    "entry_price": entry_price,
                    "exit_price":  exit_price,
                    "shares": shares,
                    "pnl": pnl,
                    "return_pct": (exit_price / entry_price - 1) - 2 * cost_per_side,
                    "holding_days": (dates[t] - entry_date).days,
                    "exit_reason": "stop_loss",
                })
                cash += shares * exit_price
                shares = 0.0
                entry_price = None
                entry_date = None
            elif take_profit is not None and high_p[t] >= entry_price * (1 + take_profit):
                exit_price = entry_price * (1 + take_profit) * (1 - cost_per_side)
                pnl = shares * exit_price - shares * entry_price * (1 + cost_per_side)
                trades.append({
                    "entry_date": entry_date.strftime("%Y-%m-%d"),
                    "exit_date":  dates[t].strftime("%Y-%m-%d"),
                    "entry_price": entry_price,
                    "exit_price":  exit_price,
                    "shares": shares,
                    "pnl": pnl,
                    "return_pct": (exit_price / entry_price - 1) - 2 * cost_per_side,
                    "holding_days": (dates[t] - entry_date).days,
                    "exit_reason": "take_profit",
                })
                cash += shares * exit_price
                shares = 0.0
                entry_price = None
                entry_date = None

        # Standard signal exit (decided on prior bar, executed at today's open).
        if shares > 0 and t >= 1 and bool(exit_arr[t - 1]) and entry_price is not None:
            exit_price = open_p[t] * (1 - cost_per_side)
            pnl = shares * exit_price - shares * entry_price * (1 + cost_per_side)
            trades.append({
                "entry_date": entry_date.strftime("%Y-%m-%d"),
                "exit_date":  dates[t].strftime("%Y-%m-%d"),
                "entry_price": entry_price,
                "exit_price":  exit_price,
                "shares": shares,
                "pnl": pnl,
                "return_pct": (exit_price / entry_price - 1) - 2 * cost_per_side,
                "holding_days": (dates[t] - entry_date).days,
                "exit_reason": "signal",
            })
            cash += shares * exit_price
            shares = 0.0
            entry_price = None
            entry_date = None

        # Standard signal entry (decided on prior bar, executed at today's open).
        if shares == 0 and t >= 1 and bool(entry_arr[t - 1]):
            entry_price = open_p[t] * (1 + cost_per_side)
            shares = cash / entry_price
            cash = 0.0
            entry_date = dates[t]

        mark_value = shares * close_p[t] if shares > 0 else 0
        equity_curve.append(cash + mark_value)
        position_curve.append(1.0 if shares > 0 else 0.0)

    # Close any open position at the last bar's close.
    if shares > 0 and entry_price is not None:
        exit_price = close_p[-1] * (1 - cost_per_side)
        pnl = shares * exit_price - shares * entry_price * (1 + cost_per_side)
        trades.append({
            "entry_date": entry_date.strftime("%Y-%m-%d"),
            "exit_date":  dates[-1].strftime("%Y-%m-%d"),
            "entry_price": entry_price,
            "exit_price":  exit_price,
            "shares": shares,
            "pnl": pnl,
            "return_pct": (exit_price / entry_price - 1) - 2 * cost_per_side,
            "holding_days": (dates[-1] - entry_date).days,
            "exit_reason": "end_of_window",
        })
        equity_curve[-1] = cash + shares * exit_price

    trades_df = pd.DataFrame(trades)
    equity = pd.Series(equity_curve, index=df.index, name="equity")
    position = pd.Series(position_curve, index=df.index, name="position")
    return trades_df, equity, position


# ===========================================================================
# Metrics
# ===========================================================================


def annualization_factor(daily_returns: pd.Series) -> float:
    if len(daily_returns) < 2:
        return 0.0
    days = (daily_returns.index[-1] - daily_returns.index[0]).days
    if days <= 0:
        return 0.0
    return 252.0 / max(len(daily_returns), 1) * (len(daily_returns) / max(days / 365.25, 1e-9))


def compute_metrics(equity: pd.Series, trades: pd.DataFrame, position: pd.Series | None = None) -> dict:
    if len(equity) < 2 or equity.iloc[0] == 0:
        return {"error": "insufficient_data"}
    returns = equity.pct_change().dropna()
    total_return = float(equity.iloc[-1] / equity.iloc[0] - 1)
    years = max((equity.index[-1] - equity.index[0]).days / 365.25, 1e-9)
    cagr = float((equity.iloc[-1] / equity.iloc[0]) ** (1 / years) - 1) if equity.iloc[0] > 0 else None

    sharpe = None
    sortino = None
    if returns.std() and returns.std() > 0:
        sharpe = float(returns.mean() / returns.std() * math.sqrt(252))
        downside = returns[returns < 0]
        if downside.std() and downside.std() > 0:
            sortino = float(returns.mean() / downside.std() * math.sqrt(252))

    rolling_max = equity.cummax()
    drawdown = equity / rolling_max - 1
    max_dd = float(drawdown.min()) if len(drawdown) else None
    calmar = float(cagr / abs(max_dd)) if cagr is not None and max_dd not in (None, 0) else None

    trades_count = int(len(trades))
    win_rate = None
    profit_factor = None
    avg_holding = None
    if trades_count > 0:
        wins = trades[trades["return_pct"] > 0]
        losses = trades[trades["return_pct"] <= 0]
        win_rate = float(len(wins) / trades_count)
        gross_win = float(wins["pnl"].sum()) if not wins.empty else 0.0
        gross_loss = float(abs(losses["pnl"].sum())) if not losses.empty else 0.0
        profit_factor = float(gross_win / gross_loss) if gross_loss > 0 else None
        avg_holding = float(trades["holding_days"].mean())

    exposure_pct = float(position.mean()) if position is not None and len(position) else None

    return {
        "total_return": total_return,
        "cagr": cagr,
        "sharpe": sharpe,
        "sortino": sortino,
        "max_drawdown": max_dd,
        "calmar": calmar,
        "trades": trades_count,
        "win_rate": win_rate,
        "profit_factor": profit_factor,
        "avg_holding_days": avg_holding,
        "exposure_pct": exposure_pct,
    }


def split_in_out(equity: pd.Series, trades: pd.DataFrame, position: pd.Series, in_sample_fraction: float) -> dict:
    if in_sample_fraction <= 0 or in_sample_fraction >= 1:
        return {
            "full":           compute_metrics(equity, trades, position),
            "in_sample":      None,
            "out_of_sample":  compute_metrics(equity, trades, position),
        }
    n = len(equity)
    cut = int(n * in_sample_fraction)
    cut_date = equity.index[cut]
    in_eq = equity.iloc[:cut + 1]
    out_eq = equity.iloc[cut:]
    # rebase the out-of-sample equity curve so its compounding starts at 1.
    if out_eq.iloc[0] != 0:
        out_eq = out_eq / out_eq.iloc[0] * equity.iloc[0]
    in_trades = trades[pd.to_datetime(trades["entry_date"]) < cut_date] if not trades.empty else trades
    out_trades = trades[pd.to_datetime(trades["entry_date"]) >= cut_date] if not trades.empty else trades
    in_pos = position.iloc[:cut + 1] if position is not None else None
    out_pos = position.iloc[cut:] if position is not None else None
    return {
        "full":           compute_metrics(equity, trades, position),
        "in_sample":      compute_metrics(in_eq, in_trades, in_pos),
        "out_of_sample":  compute_metrics(out_eq, out_trades, out_pos),
        "split_date": cut_date.strftime("%Y-%m-%d"),
    }


def overfitting_diagnostics(splits: dict, params_user_supplied: bool) -> dict:
    in_cagr = (splits.get("in_sample") or {}).get("cagr")
    out_cagr = (splits.get("out_of_sample") or {}).get("cagr")
    ratio = None
    interpretation = "insufficient data"
    if in_cagr is not None and out_cagr is not None and in_cagr != 0:
        ratio = out_cagr / in_cagr if in_cagr > 0 else None
        if ratio is None:
            interpretation = "in-sample CAGR <= 0; cannot compute degradation ratio"
        elif ratio >= 0.7:
            interpretation = "out-of-sample tracked in-sample; low overfit signal"
        elif ratio >= 0.4:
            interpretation = "moderate out-of-sample decay; possible regime drift"
        elif ratio >= 0:
            interpretation = "out-of-sample materially weaker; likely overfit or regime change"
        else:
            interpretation = "out-of-sample is negative while in-sample was positive; high overfit risk"
    return {
        "in_sample_cagr": in_cagr,
        "out_of_sample_cagr": out_cagr,
        "degradation_ratio": ratio,
        "interpretation": interpretation,
        "params_user_supplied": bool(params_user_supplied),
        "params_searched_count": 0,
    }


# ===========================================================================
# Indicator strategies
# ===========================================================================


def build_indicators(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["sma50"] = sma(out["close"], 50)
    out["sma200"] = sma(out["close"], 200)
    out["rsi14"] = rsi(out["close"], 14)
    k, d, j = kdj(out["high"], out["low"], out["close"])
    out["k"], out["d"], out["j"] = k, d, j
    m, s, h = macd(out["close"])
    out["macd"], out["macd_signal"], out["macd_hist"] = m, s, h
    upper, mid, lower = bollinger(out["close"])
    out["bb_upper"], out["bb_mid"], out["bb_lower"] = upper, mid, lower
    out["bb_width"] = (upper - lower) / mid
    out["vol_ma20"] = out["volume"].rolling(20, min_periods=20).mean()
    return out


def strategy_kdj_golden_cross(df: pd.DataFrame, params: dict) -> tuple[pd.Series, pd.Series, dict]:
    """Entry: K crosses above D AND both < 30. Exit: death cross OR stop/take."""
    enter = (df["k"] > df["d"]) & (df["k"].shift(1) <= df["d"].shift(1)) & (df["k"] < 30) & (df["d"] < 30)
    exit_ = (df["k"] < df["d"]) & (df["k"].shift(1) >= df["d"].shift(1))
    return enter.fillna(False), exit_.fillna(False), {
        "stop_loss": float(params.get("stop_loss", 0.05)),
        "take_profit": float(params.get("take_profit", 0.15)),
    }


def strategy_sma_50_200_cross(df: pd.DataFrame, params: dict) -> tuple[pd.Series, pd.Series, dict]:
    enter = (df["sma50"] > df["sma200"]) & (df["sma50"].shift(1) <= df["sma200"].shift(1))
    exit_ = (df["sma50"] < df["sma200"]) & (df["sma50"].shift(1) >= df["sma200"].shift(1))
    return enter.fillna(False), exit_.fillna(False), {}


def strategy_rsi_mean_reversion(df: pd.DataFrame, params: dict) -> tuple[pd.Series, pd.Series, dict]:
    enter = (df["rsi14"] < 30) & (df["rsi14"].shift(1) >= 30)
    exit_ = (df["rsi14"] > 70) & (df["rsi14"].shift(1) <= 70)
    return enter.fillna(False), exit_.fillna(False), {"stop_loss": float(params.get("stop_loss", 0.08))}


def strategy_bb_lower_bounce(df: pd.DataFrame, params: dict) -> tuple[pd.Series, pd.Series, dict]:
    enter = (df["close"] < df["bb_lower"]) & (df["close"].shift(1) >= df["bb_lower"].shift(1))
    exit_ = df["close"] > df["bb_mid"]
    return enter.fillna(False), exit_.fillna(False), {"stop_loss": float(params.get("stop_loss", 0.05))}


def strategy_macd_signal_cross(df: pd.DataFrame, params: dict) -> tuple[pd.Series, pd.Series, dict]:
    enter = (df["macd"] > df["macd_signal"]) & (df["macd"].shift(1) <= df["macd_signal"].shift(1)) & (df["macd_signal"] > 0)
    exit_ = (df["macd"] < df["macd_signal"]) & (df["macd"].shift(1) >= df["macd_signal"].shift(1))
    return enter.fillna(False), exit_.fillna(False), {}


STRATEGY_REGISTRY: dict[str, Callable] = {
    "kdj_golden_cross":    strategy_kdj_golden_cross,
    "sma_50_200_cross":    strategy_sma_50_200_cross,
    "rsi_mean_reversion":  strategy_rsi_mean_reversion,
    "bb_lower_bounce":     strategy_bb_lower_bounce,
    "macd_signal_cross":   strategy_macd_signal_cross,
}


# ===========================================================================
# Signal definitions
# ===========================================================================


def signal_kdj_golden_cross(df: pd.DataFrame) -> pd.Series:
    return ((df["k"] > df["d"]) & (df["k"].shift(1) <= df["d"].shift(1)) & (df["k"] < 30) & (df["d"] < 30)).fillna(False)


def signal_sma_50_200_cross(df: pd.DataFrame) -> pd.Series:
    return ((df["sma50"] > df["sma200"]) & (df["sma50"].shift(1) <= df["sma200"].shift(1))).fillna(False)


def signal_rsi_oversold(df: pd.DataFrame) -> pd.Series:
    return ((df["rsi14"] < 30) & (df["rsi14"].shift(1) >= 30)).fillna(False)


def signal_bb_squeeze_breakout(df: pd.DataFrame) -> pd.Series:
    width = df["bb_width"]
    width_6mo_min = width.rolling(126, min_periods=60).min()
    squeezed = width <= width_6mo_min * 1.02
    breakout = df["close"] > df["bb_upper"]
    return (squeezed.shift(1).fillna(False) & breakout).fillna(False)


def signal_volume_spike_2x(df: pd.DataFrame) -> pd.Series:
    return (df["volume"] >= 2 * df["vol_ma20"]).fillna(False)


def signal_gap_up_3pct(df: pd.DataFrame) -> pd.Series:
    return (df["open"] >= 1.03 * df["close"].shift(1)).fillna(False)


def signal_new_52w_high(df: pd.DataFrame) -> pd.Series:
    high_252 = df["close"].rolling(252, min_periods=200).max()
    return (df["close"] >= high_252).fillna(False)


def signal_macd_signal_cross(df: pd.DataFrame) -> pd.Series:
    return ((df["macd"] > df["macd_signal"]) & (df["macd"].shift(1) <= df["macd_signal"].shift(1)) & (df["macd_signal"] > 0)).fillna(False)


SIGNAL_REGISTRY: dict[str, Callable] = {
    "kdj_golden_cross":      signal_kdj_golden_cross,
    "sma_50_200_cross":      signal_sma_50_200_cross,
    "rsi_oversold":          signal_rsi_oversold,
    "bb_squeeze_breakout":   signal_bb_squeeze_breakout,
    "volume_spike_2x":       signal_volume_spike_2x,
    "gap_up_3pct":           signal_gap_up_3pct,
    "new_52w_high":          signal_new_52w_high,
    "macd_signal_cross":     signal_macd_signal_cross,
}


# ===========================================================================
# Personas (v1 partial fundamentals)
# ===========================================================================


def _ttm(quarters: list[dict], idx: int, field: str) -> float | None:
    """Trailing-12-month sum of `field` ending at quarter index idx (inclusive)."""
    if idx < 3:
        return None
    vals = [quarters[i].get(field) for i in range(idx - 3, idx + 1)]
    if any(v is None for v in vals):
        return None
    return float(sum(vals))


def _ttm_growth(quarters: list[dict], idx: int, field: str) -> float | None:
    cur = _ttm(quarters, idx, field)
    prior = _ttm(quarters, idx - 4, field) if idx >= 7 else None
    if cur is None or prior is None or prior == 0:
        return None
    return (cur - prior) / abs(prior)


def _book_value_per_share(q: dict) -> float | None:
    eq = q.get("total_equity")
    sh = q.get("shares_diluted")
    if eq is None or sh is None or sh == 0:
        return None
    return float(eq / sh)


def _debt_to_equity(q: dict) -> float | None:
    debt = q.get("total_debt")
    eq = q.get("total_equity")
    if debt is None or eq is None or eq == 0:
        return None
    return float(debt / eq)


def _current_ratio(q: dict) -> float | None:
    ca = q.get("current_assets")
    cl = q.get("current_liabilities")
    if ca is None or cl is None or cl == 0:
        return None
    return float(ca / cl)


def persona_lynch(q: dict, idx: int, quarters: list[dict], price: float) -> tuple[bool, dict]:
    """Lynch GARP: EPS growth >= 15%, PEG <= 1, debt/equity < 0.5."""
    ttm_eps = _ttm(quarters, idx, "eps_diluted")
    eps_growth = _ttm_growth(quarters, idx, "eps_diluted")
    de = _debt_to_equity(q)
    pe = price / ttm_eps if ttm_eps and ttm_eps > 0 else None
    peg = pe / (eps_growth * 100) if pe and eps_growth and eps_growth > 0 else None
    pass_eps_growth = eps_growth is not None and eps_growth >= 0.15
    pass_peg = peg is not None and peg <= 1.0
    pass_debt = de is not None and de < 0.5
    return (pass_eps_growth and pass_peg and pass_debt), {
        "ttm_eps": ttm_eps, "eps_growth_yoy": eps_growth, "pe": pe, "peg": peg, "debt_to_equity": de,
        "pass_eps_growth": pass_eps_growth, "pass_peg": pass_peg, "pass_debt": pass_debt,
    }


def persona_graham(q: dict, idx: int, quarters: list[dict], price: float) -> tuple[bool, dict]:
    """Graham defensive: P/E < 15, P/B < 1.5, dividend yield > 2%, current ratio > 2."""
    ttm_eps = _ttm(quarters, idx, "eps_diluted")
    ttm_dps = _ttm(quarters, idx, "dividend_per_share")
    bvps = _book_value_per_share(q)
    cr = _current_ratio(q)
    pe = price / ttm_eps if ttm_eps and ttm_eps > 0 else None
    pb = price / bvps if bvps and bvps > 0 else None
    div_yield = ttm_dps / price if ttm_dps and price > 0 else None
    pass_pe = pe is not None and pe < 15
    pass_pb = pb is not None and pb < 1.5
    pass_div = div_yield is not None and div_yield > 0.02
    pass_cr = cr is not None and cr > 2
    return (pass_pe and pass_pb and pass_div and pass_cr), {
        "ttm_eps": ttm_eps, "ttm_dps": ttm_dps, "bvps": bvps, "current_ratio": cr,
        "pe": pe, "pb": pb, "dividend_yield": div_yield,
        "pass_pe": pass_pe, "pass_pb": pass_pb, "pass_div": pass_div, "pass_cr": pass_cr,
    }


def persona_burry(q: dict, idx: int, quarters: list[dict], price: float) -> tuple[bool, dict]:
    """Burry deep value: FCF yield >= 15%, P/B < 1.5, debt/equity < 0.5."""
    ttm_fcf = _ttm(quarters, idx, "fcf")
    bvps = _book_value_per_share(q)
    sh = q.get("shares_diluted")
    market_cap = price * sh if sh else None
    fcf_yield = ttm_fcf / market_cap if ttm_fcf and market_cap and market_cap > 0 else None
    pb = price / bvps if bvps and bvps > 0 else None
    de = _debt_to_equity(q)
    pass_fcf = fcf_yield is not None and fcf_yield >= 0.15
    pass_pb = pb is not None and pb < 1.5
    pass_debt = de is not None and de < 0.5
    return (pass_fcf and pass_pb and pass_debt), {
        "ttm_fcf": ttm_fcf, "market_cap": market_cap, "fcf_yield": fcf_yield,
        "bvps": bvps, "pb": pb, "debt_to_equity": de,
        "pass_fcf": pass_fcf, "pass_pb": pass_pb, "pass_debt": pass_debt,
    }


def persona_druckenmiller_lite(q: dict, idx: int, quarters: list[dict], price: float, df_row: pd.Series, spy_row: pd.Series | None) -> tuple[bool, dict]:
    """Momentum + macro proxy: price>SMA200, SMA50>SMA200, SPY>SPY-SMA200."""
    price_above_sma200 = bool(df_row.get("close", 0) > (df_row.get("sma200") or float("inf")))
    sma50_above_sma200 = bool((df_row.get("sma50") or 0) > (df_row.get("sma200") or float("inf")))
    spy_above_sma200 = True
    if spy_row is not None:
        spy_close = spy_row.get("close")
        spy_sma200 = spy_row.get("sma200")
        spy_above_sma200 = bool(spy_close is not None and spy_sma200 is not None and spy_close > spy_sma200)
    return (price_above_sma200 and sma50_above_sma200 and spy_above_sma200), {
        "price_above_sma200": price_above_sma200,
        "sma50_above_sma200": sma50_above_sma200,
        "spy_above_sma200": spy_above_sma200,
        "macro_proxy": "SPY trend filter",
    }


PERSONA_REGISTRY = {
    "lynch":               persona_lynch,
    "graham":              persona_graham,
    "burry":               persona_burry,
    "druckenmiller_lite":  persona_druckenmiller_lite,
}


PERSONA_DEFERRED = {
    "buffett":             "Requires owner earnings (EPS + D&A - maintenance capex) and 10-yr ROE history. Maintenance capex isn't a reported line. Deferred to v2.",
    "munger":              "Requires ROIC time series and business predictability rating. No clean data source. Deferred to v2.",
    "fisher":              "Requires R&D intensity rank and qualitative scuttlebutt. Deferred to v2.",
    "wood":                "Requires disruptive-innovation classification and forward TAM model. Deferred to v2.",
}


# ===========================================================================
# Mode executors
# ===========================================================================


def run_indicator(df: pd.DataFrame, df_bench: pd.DataFrame, strategy: str, params: dict, args) -> dict:
    if strategy not in STRATEGY_REGISTRY:
        return {"error": "unknown_strategy", "available": list(STRATEGY_REGISTRY.keys())}
    df_i = build_indicators(df)
    entry, exit_, stops = STRATEGY_REGISTRY[strategy](df_i, params)
    trades, equity, position = simulate_trades(
        df_i, entry, exit_,
        initial_capital=args.initial_capital,
        commission_bps=args.commission_bps,
        slippage_bps=args.slippage_bps,
        stop_loss=stops.get("stop_loss"),
        take_profit=stops.get("take_profit"),
    )
    splits = split_in_out(equity, trades, position, args.in_sample_fraction)
    buy_hold = compute_buy_hold(df_i, args.initial_capital)
    bench = compute_buy_hold(df_bench, args.initial_capital) if not df_bench.empty else None
    return {
        "mode": "indicator", "strategy": strategy, "params": {**params, **stops},
        "trades_df": trades, "equity": equity, "position": position,
        "splits": splits, "buy_hold": buy_hold, "benchmark_equity": bench,
        "overfit": overfitting_diagnostics(splits, params_user_supplied=bool(params)),
    }


def run_signal(df: pd.DataFrame, signal: str, args) -> dict:
    if signal not in SIGNAL_REGISTRY:
        return {"error": "unknown_signal", "available": list(SIGNAL_REGISTRY.keys())}
    df_i = build_indicators(df)
    sig = SIGNAL_REGISTRY[signal](df_i)
    event_dates = df_i.index[sig]
    horizons = [1, 5, 10, 20, 60]
    closes = df_i["close"]
    stats: dict[str, dict] = {}
    forward_returns_for_chart: dict[int, list[float]] = {h: [] for h in horizons}
    for h in horizons:
        rets: list[float] = []
        for d in event_dates:
            try:
                pos = closes.index.get_loc(d)
            except KeyError:
                continue
            if pos + h >= len(closes):
                continue
            r = closes.iloc[pos + h] / closes.iloc[pos] - 1
            rets.append(float(r))
            forward_returns_for_chart[h].append(float(r))
        if rets:
            arr = pd.Series(rets)
            mean = float(arr.mean())
            median = float(arr.median())
            std = float(arr.std()) if len(arr) > 1 else 0.0
            t_stat = float(mean / (std / math.sqrt(len(arr)))) if std > 0 else None
            stats[f"{h}d"] = {
                "events": len(arr), "mean_return": mean, "median": median, "std": std,
                "hit_rate": float((arr > 0).sum() / len(arr)), "t_stat": t_stat,
                "max_gain": float(arr.max()), "max_loss": float(arr.min()),
            }
        else:
            stats[f"{h}d"] = {"events": 0}

    # Baseline: random N-day forward returns from the same window.
    import random
    rng = random.Random(42)
    baseline_count = max(1000, len(event_dates) * 20)
    all_positions = list(range(len(closes) - 60))
    baseline_stats: dict[str, dict] = {}
    for h in horizons:
        rets: list[float] = []
        if all_positions:
            for _ in range(baseline_count):
                pos = rng.choice(all_positions)
                if pos + h < len(closes):
                    rets.append(float(closes.iloc[pos + h] / closes.iloc[pos] - 1))
        if rets:
            arr = pd.Series(rets)
            baseline_stats[f"{h}d"] = {
                "mean_return": float(arr.mean()),
                "hit_rate":    float((arr > 0).sum() / len(arr)),
            }

    primary = f"{args.holding_days}d" if f"{args.holding_days}d" in stats else f"{horizons[3]}d"
    edge_at_primary: dict[str, Any] = {}
    if primary in stats and stats[primary].get("events") and primary in baseline_stats:
        edge_at_primary = {
            "horizon": primary,
            "mean_return_diff": stats[primary]["mean_return"] - baseline_stats[primary]["mean_return"],
            "hit_rate_diff":    stats[primary]["hit_rate"] - baseline_stats[primary]["hit_rate"],
            "edge_t_stat":      stats[primary].get("t_stat"),
            "significant_at_p05": (stats[primary].get("t_stat") is not None and abs(stats[primary]["t_stat"]) > 1.96),
        }
    return {
        "mode": "signal", "signal": signal,
        "events": int(sig.sum()),
        "horizons": stats,
        "baseline": {"method": f"{baseline_count}_random_dates_same_window", "horizons": baseline_stats},
        "edge_vs_baseline": edge_at_primary,
        "forward_returns_for_chart": forward_returns_for_chart,
    }


def run_persona(df: pd.DataFrame, df_bench: pd.DataFrame, fundamentals: dict, persona: str, args) -> dict:
    if persona in PERSONA_DEFERRED:
        return {"error": "data_insufficient", "persona": persona, "explanation": PERSONA_DEFERRED[persona], "supported_personas": list(PERSONA_REGISTRY.keys())}
    if persona not in PERSONA_REGISTRY:
        return {"error": "unknown_persona", "available": list(PERSONA_REGISTRY.keys()) + list(PERSONA_DEFERRED.keys())}
    if fundamentals.get("status") != "ok":
        return {"error": "fundamentals_unavailable", "fundamentals_status": fundamentals.get("status"), "fallback_from": fundamentals.get("fallback_from")}

    quarters = fundamentals.get("quarters", [])
    if len(quarters) < 8:
        return {"error": "insufficient_fundamentals_history", "quarters_available": len(quarters),
                "required": 8, "note": "Need at least 8 quarters for TTM + YoY growth calculations."}

    df_i = build_indicators(df)
    bench_i = build_indicators(df_bench) if not df_bench.empty else pd.DataFrame()
    persona_fn = PERSONA_REGISTRY[persona]

    # Rebalance schedule: every N months
    months_step = 3 if args.rebalance_frequency == "quarterly" else 12
    rebalance_dates: list[pd.Timestamp] = []
    cursor = df_i.index[0]
    while cursor <= df_i.index[-1]:
        rebalance_dates.append(cursor)
        cursor = cursor + pd.DateOffset(months=months_step)

    # Determine hold/cash for each rebalance using the latest embargoed quarter.
    decisions: list[dict] = []
    for rb in rebalance_dates:
        usable = [(i, q) for i, q in enumerate(quarters)
                  if datetime.strptime(q["as_of_date"], "%Y-%m-%d") <= rb.to_pydatetime()]
        if not usable:
            decisions.append({"date": rb, "hold": False, "reason": "no_embargoed_fundamentals"})
            continue
        idx, latest_q = usable[-1]
        try:
            price_row_loc = df_i.index.get_indexer([rb], method="nearest")[0]
        except Exception:
            decisions.append({"date": rb, "hold": False, "reason": "no_price_row"})
            continue
        price = float(df_i["close"].iloc[price_row_loc])
        df_row = df_i.iloc[price_row_loc]
        spy_row = bench_i.iloc[bench_i.index.get_indexer([rb], method="nearest")[0]] if not bench_i.empty else None
        if persona == "druckenmiller_lite":
            hold, detail = persona_druckenmiller_lite(latest_q, idx, quarters, price, df_row, spy_row)
        else:
            hold, detail = persona_fn(latest_q, idx, quarters, price)
        decisions.append({"date": rb, "hold": bool(hold), "criteria": detail,
                           "fundamentals_period_end": latest_q.get("period_end_date")})

    # Build entry/exit signals from the decision list, executed at next bar open.
    entry_dates: set[pd.Timestamp] = set()
    exit_dates: set[pd.Timestamp] = set()
    prev_hold = False
    for dec in decisions:
        if dec["hold"] and not prev_hold:
            entry_dates.add(dec["date"])
        elif not dec["hold"] and prev_hold:
            exit_dates.add(dec["date"])
        prev_hold = dec["hold"]
    entry = pd.Series(False, index=df_i.index)
    exit_ = pd.Series(False, index=df_i.index)
    for d in entry_dates:
        snapped = df_i.index[df_i.index.get_indexer([d], method="nearest")[0]]
        entry.loc[snapped] = True
    for d in exit_dates:
        snapped = df_i.index[df_i.index.get_indexer([d], method="nearest")[0]]
        exit_.loc[snapped] = True

    trades, equity, position = simulate_trades(
        df_i, entry, exit_,
        initial_capital=args.initial_capital,
        commission_bps=args.commission_bps,
        slippage_bps=args.slippage_bps,
    )
    splits = split_in_out(equity, trades, position, args.in_sample_fraction)
    buy_hold = compute_buy_hold(df_i, args.initial_capital)
    bench = compute_buy_hold(df_bench, args.initial_capital) if not df_bench.empty else None
    return {
        "mode": "persona", "persona": persona,
        "rebalances": len(decisions),
        "periods_held": sum(1 for d in decisions if d["hold"]),
        "periods_cash": sum(1 for d in decisions if not d["hold"]),
        "trades_df": trades, "equity": equity, "position": position,
        "splits": splits, "buy_hold": buy_hold, "benchmark_equity": bench,
        "fundamentals_data_quality": fundamentals.get("data_quality"),
        "fundamentals_missing_fields": fundamentals.get("missing_fields", []),
        "overfit": overfitting_diagnostics(splits, params_user_supplied=False),
        "decisions": [{"date": d["date"].strftime("%Y-%m-%d"), "hold": d["hold"],
                       "fundamentals_period_end": d.get("fundamentals_period_end")} for d in decisions],
    }


def compute_buy_hold(df: pd.DataFrame, initial_capital: float) -> pd.Series:
    if df.empty:
        return pd.Series(dtype=float)
    return (df["close"] / df["close"].iloc[0] * initial_capital).rename("buy_hold")


# ===========================================================================
# Charts
# ===========================================================================


def plot_equity_curve(equity: pd.Series, buy_hold: pd.Series, benchmark: pd.Series | None, ticker: str, mode: str, out_path: Path) -> None:
    if not _HAS_MPL:
        return
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(equity.index, equity.values, label=f"Strategy ({mode})", linewidth=1.6)
    if buy_hold is not None and not buy_hold.empty:
        ax.plot(buy_hold.index, buy_hold.values, label=f"{ticker} Buy & Hold", linewidth=1.2, linestyle="--")
    if benchmark is not None and not benchmark.empty:
        ax.plot(benchmark.index, benchmark.values, label="Benchmark Buy & Hold", linewidth=1.2, linestyle=":")
    ax.set_title(f"{ticker} equity curve — {mode}")
    ax.set_ylabel("Equity (USD)")
    ax.set_xlabel("Date")
    ax.legend()
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(out_path, dpi=110)
    plt.close(fig)


def plot_signal_distribution(forward_returns: dict[int, list[float]], ticker: str, signal: str, out_path: Path) -> None:
    if not _HAS_MPL:
        return
    horizons = sorted(forward_returns.keys())
    n = len(horizons)
    fig, axes = plt.subplots(1, n, figsize=(4 * n, 4), sharey=True)
    if n == 1:
        axes = [axes]
    for ax, h in zip(axes, horizons):
        data = forward_returns[h]
        if data:
            ax.hist([x * 100 for x in data], bins=30, edgecolor="black", alpha=0.7)
            ax.axvline(0, color="red", linestyle="--", alpha=0.7)
            ax.axvline(float(pd.Series(data).mean()) * 100, color="green", linestyle="-", alpha=0.7, label="mean")
            ax.legend()
        ax.set_title(f"+{h}d forward returns")
        ax.set_xlabel("Return (%)")
    fig.suptitle(f"{ticker} — {signal} signal forward-return distribution")
    fig.tight_layout()
    fig.savefig(out_path, dpi=110)
    plt.close(fig)


# ===========================================================================
# Output writers
# ===========================================================================


def write_trades_csv(trades: pd.DataFrame, out_path: Path) -> None:
    if trades.empty:
        out_path.write_text("entry_date,exit_date,entry_price,exit_price,shares,pnl,return_pct,holding_days,exit_reason\n", encoding="utf-8")
        return
    trades.to_csv(out_path, index=False, quoting=csv.QUOTE_NONNUMERIC)


def write_bundle(bundle: dict, out_path: Path) -> None:
    def default(o):
        if isinstance(o, (pd.Timestamp, datetime)):
            return o.strftime("%Y-%m-%d")
        if hasattr(o, "item"):
            return o.item()
        return str(o)
    out_path.write_text(json.dumps(bundle, indent=2, default=default), encoding="utf-8")


# ===========================================================================
# Main
# ===========================================================================


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0] if __doc__ else "stock backtest")
    p.add_argument("ticker", help="e.g. NVDA")
    p.add_argument("--mode", choices=["indicator", "signal", "persona"], required=True)
    p.add_argument("--strategy", help="for --mode indicator")
    p.add_argument("--signal", help="for --mode signal")
    p.add_argument("--persona", help="for --mode persona")
    p.add_argument("--holding-days", type=int, default=20, help="primary forward horizon for signal mode")
    p.add_argument("--rebalance-frequency", choices=["quarterly", "annual"], default="quarterly")
    p.add_argument("--params", default="{}", help='JSON for strategy-specific knobs, e.g. \'{"stop_loss":0.05}\'')
    p.add_argument("--start", default=None, help="YYYY-MM-DD (default = 5y before --end)")
    p.add_argument("--end", default=None, help="YYYY-MM-DD (default = today)")
    p.add_argument("--initial-capital", type=float, default=100000)
    p.add_argument("--commission-bps", type=float, default=5)
    p.add_argument("--slippage-bps", type=float, default=5)
    p.add_argument("--position-sizing", choices=["all-in", "fixed-fraction"], default="all-in")
    p.add_argument("--fraction", type=float, default=1.0)
    p.add_argument("--benchmark", default="SPY")
    p.add_argument("--key-file", default=None)
    p.add_argument("--output-dir", default=None)
    p.add_argument("--in-sample-fraction", type=float, default=0.7)
    p.add_argument("--no-charts", action="store_true")
    p.add_argument("--tag", default=None)
    return p.parse_args()


def main() -> int:
    args = parse_args()
    ticker = args.ticker.upper()
    end_dt = datetime.strptime(args.end, "%Y-%m-%d") if args.end else datetime.now(timezone.utc).replace(tzinfo=None)
    start_dt = datetime.strptime(args.start, "%Y-%m-%d") if args.start else end_dt.replace(year=end_dt.year - 5)
    start, end = start_dt.strftime("%Y-%m-%d"), end_dt.strftime("%Y-%m-%d")
    keys = load_keys(args.key_file)

    out_dir = Path(args.output_dir) if args.output_dir and args.output_dir != "auto" else get_output_dir()
    out_dir.mkdir(parents=True, exist_ok=True)
    tag_suffix = f"_{args.tag}" if args.tag else ""

    try:
        params = json.loads(args.params or "{}")
    except json.JSONDecodeError as exc:
        print(f"ERROR: --params is not valid JSON: {exc}", file=sys.stderr)
        return 2

    print(f"[backtest] {ticker} mode={args.mode} window={start}..{end}", file=sys.stderr)

    # Ensure the no-API-key fallback (yfinance) is available before fetching.
    ensure_yfinance()

    df, ticker_meta = fetch_daily_df(ticker, keys, start, end)
    if df.empty:
        bundle = {"ticker": ticker, "error": "ticker_data_unavailable", "data_provider": ticker_meta}
        write_bundle(bundle, out_dir / f"{ticker}{tag_suffix}_backtest_bundle.json")
        print(f"ERROR: could not fetch daily data for {ticker}. status={ticker_meta.get('status')}", file=sys.stderr)
        return 3
    print(f"[backtest] loaded {len(df)} daily bars for {ticker}", file=sys.stderr)

    df_bench, bench_meta = fetch_daily_df(args.benchmark, keys, start, end) if args.benchmark else (pd.DataFrame(), {})
    if args.benchmark and df_bench.empty:
        print(f"WARN: benchmark {args.benchmark} unavailable; continuing with Buy&Hold comparison only.", file=sys.stderr)

    if args.mode == "indicator":
        if not args.strategy:
            print("ERROR: --strategy is required for --mode indicator", file=sys.stderr)
            return 2
        result = run_indicator(df, df_bench, args.strategy, params, args)
    elif args.mode == "signal":
        if not args.signal:
            print("ERROR: --signal is required for --mode signal", file=sys.stderr)
            return 2
        result = run_signal(df, args.signal, args)
    elif args.mode == "persona":
        if not args.persona:
            print("ERROR: --persona is required for --mode persona", file=sys.stderr)
            return 2
        fundamentals = fetch_fundamentals(ticker, keys)
        print(f"[backtest] fundamentals status={fundamentals.get('status')} source={fundamentals.get('source')}", file=sys.stderr)
        result = run_persona(df, df_bench, fundamentals, args.persona, args)
        result["fundamentals_provider"] = {"status": fundamentals.get("status"), "source": fundamentals.get("source"), "data_quality": fundamentals.get("data_quality")}
    else:
        return 2

    if result.get("error"):
        bundle = {"ticker": ticker, "mode": args.mode, **result, "window": {"start": start, "end": end}}
        write_bundle(bundle, out_dir / f"{ticker}{tag_suffix}_backtest_bundle.json")
        if result["error"] == "unknown_strategy" or result["error"] == "unknown_signal" or result["error"] == "unknown_persona":
            return 5
        if result["error"] in {"data_insufficient", "fundamentals_unavailable", "insufficient_fundamentals_history"}:
            return 6
        return 1

    bundle: dict[str, Any] = {
        "ticker": ticker, "mode": args.mode,
        "window": {"start": start, "end": end, "trading_days": len(df),
                    "in_sample_end": result.get("splits", {}).get("split_date"),
                    "out_of_sample_start": result.get("splits", {}).get("split_date")},
        "costs": {"commission_bps": args.commission_bps, "slippage_bps": args.slippage_bps,
                   "total_cost_drag_per_round_trip_pct": 2 * (args.commission_bps + args.slippage_bps) / 10000.0},
        "data_quality": {
            "ticker_source": ticker_meta.get("source"),
            "benchmark_source": bench_meta.get("source"),
            "data_health": "good" if not df.empty and (df_bench is None or not df_bench.empty) else "partial",
        },
    }
    if args.commission_bps == 0 and args.slippage_bps == 0:
        bundle["costs"]["warning"] = "frictionless backtest — not realistic"

    # Build the equity-curve PNG and trades.csv only when relevant.
    equity_curve_path = None
    trades_csv_path = None
    signal_chart_path = None
    if args.mode in {"indicator", "persona"}:
        equity = result["equity"]
        buy_hold = result.get("buy_hold", pd.Series(dtype=float))
        benchmark_equity = result.get("benchmark_equity")
        if not args.no_charts and _HAS_MPL:
            equity_curve_path = out_dir / f"{ticker}{tag_suffix}_equity_curve.png"
            plot_equity_curve(equity, buy_hold, benchmark_equity, ticker, args.mode, equity_curve_path)
        trades_csv_path = out_dir / f"{ticker}{tag_suffix}_trades.csv"
        write_trades_csv(result["trades_df"], trades_csv_path)
        bundle.update({
            "strategy" if args.mode == "indicator" else "persona": result.get("strategy") or result.get("persona"),
            "params": result.get("params"),
            "summary_full": result["splits"]["full"],
            "summary_in_sample": result["splits"]["in_sample"],
            "summary_out_of_sample": result["splits"]["out_of_sample"],
            "buy_and_hold": compute_metrics(buy_hold, pd.DataFrame()) if not buy_hold.empty else None,
            "benchmark": ({
                "ticker": args.benchmark,
                **compute_metrics(benchmark_equity, pd.DataFrame()),
            }) if benchmark_equity is not None and not benchmark_equity.empty else None,
            "alpha": {
                "vs_buy_and_hold_total": (
                    (result["splits"]["full"].get("total_return") or 0) -
                    ((compute_metrics(buy_hold, pd.DataFrame()).get("total_return") if not buy_hold.empty else 0) or 0)
                ),
                "vs_benchmark_total": (
                    (result["splits"]["full"].get("total_return") or 0) -
                    ((compute_metrics(benchmark_equity, pd.DataFrame()).get("total_return") if benchmark_equity is not None and not benchmark_equity.empty else 0) or 0)
                ),
            } if benchmark_equity is not None and not benchmark_equity.empty else None,
            "overfitting_diagnostics": result["overfit"],
            "trades_file": str(trades_csv_path),
            "equity_curve_file": str(equity_curve_path) if equity_curve_path else None,
        })
        if args.mode == "persona":
            bundle["persona_meta"] = {
                "rebalances": result["rebalances"],
                "periods_held": result["periods_held"],
                "periods_cash": result["periods_cash"],
                "rebalance_frequency": args.rebalance_frequency,
                "fundamentals_data_quality": result["fundamentals_data_quality"],
                "fundamentals_missing_fields": result["fundamentals_missing_fields"],
                "fundamentals_provider": result.get("fundamentals_provider"),
                "decisions": result["decisions"],
            }

    elif args.mode == "signal":
        if not args.no_charts and _HAS_MPL:
            signal_chart_path = out_dir / f"{ticker}{tag_suffix}_signal_distribution.png"
            plot_signal_distribution(result["forward_returns_for_chart"], ticker, args.signal, signal_chart_path)
        # Drop the heavy histogram payload before serializing.
        result_for_bundle = {k: v for k, v in result.items() if k != "forward_returns_for_chart"}
        bundle.update({
            "signal_stats": result_for_bundle,
            "signal_distribution_file": str(signal_chart_path) if signal_chart_path else None,
        })

    bundle_path = out_dir / f"{ticker}{tag_suffix}_backtest_bundle.json"
    write_bundle(bundle, bundle_path)

    print(f"[backtest] wrote {bundle_path}", file=sys.stderr)
    if trades_csv_path:
        print(f"[backtest] wrote {trades_csv_path}", file=sys.stderr)
    if equity_curve_path:
        print(f"[backtest] wrote {equity_curve_path}", file=sys.stderr)
    if signal_chart_path:
        print(f"[backtest] wrote {signal_chart_path}", file=sys.stderr)
    print(json.dumps({"bundle": str(bundle_path)}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
