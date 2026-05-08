#!/usr/bin/env python3
"""
Fetch quote, daily/weekly/intraday OHLCV, technical indicators, and optional PNG charts.

Data sources are selected by scripts/data_provider.py:
- Direct API when network/API keys are available.
- Prefetched JSON written by Claude web tools in sandboxed environments.
- Optional yfinance fallback when installed.

This script avoids printing API keys. It writes:
- {TICKER}_technical_bundle.json
- {TICKER}_daily_chart.png when matplotlib is available
- {TICKER}_weekly_chart.png when matplotlib is available
- {TICKER}_intraday_{window}_{resolution}m_chart.png when requested and available
"""

from __future__ import annotations

import argparse
import json
import math
from datetime import datetime, timezone
from pathlib import Path

from data_provider import (
    get_daily_ohlcv,
    get_intraday_ohlcv,
    get_output_dir,
    get_quote,
    get_weekly_ohlcv,
    load_keys,
)


def sma(values: list[float], n: int) -> float | None:
    if len(values) < n:
        return None
    return sum(values[-n:]) / n


def ema(values: list[float], span: int) -> list[float]:
    alpha = 2 / (span + 1)
    out = []
    previous = None
    for value in values:
        previous = value if previous is None else alpha * value + (1 - alpha) * previous
        out.append(previous)
    return out


def rsi(closes: list[float], n: int = 14) -> float | None:
    if len(closes) < n + 1:
        return None
    gains = []
    losses = []
    for index in range(1, len(closes)):
        delta = closes[index] - closes[index - 1]
        gains.append(max(delta, 0))
        losses.append(max(-delta, 0))
    avg_gain = sum(gains[:n]) / n
    avg_loss = sum(losses[:n]) / n
    for index in range(n, len(gains)):
        avg_gain = (avg_gain * (n - 1) + gains[index]) / n
        avg_loss = (avg_loss * (n - 1) + losses[index]) / n
    if avg_loss == 0:
        return 100.0
    return 100 - 100 / (1 + avg_gain / avg_loss)


def kdj_series(
    highs: list[float],
    lows: list[float],
    closes: list[float],
    n: int = 9,
) -> list[tuple[float, float, float] | None]:
    values: list[tuple[float, float, float] | None] = [None] * len(closes)
    if len(closes) < n:
        return values
    k = 50.0
    d = 50.0
    for index in range(n - 1, len(closes)):
        low_n = min(lows[index - n + 1 : index + 1])
        high_n = max(highs[index - n + 1 : index + 1])
        rsv = 50.0 if high_n == low_n else (closes[index] - low_n) / (high_n - low_n) * 100
        k = (2 / 3) * k + (1 / 3) * rsv
        d = (2 / 3) * d + (1 / 3) * k
        values[index] = (k, d, 3 * k - 2 * d)
    return values


def kdj(highs: list[float], lows: list[float], closes: list[float], n: int = 9) -> tuple[float, float, float] | None:
    values = kdj_series(highs, lows, closes, n)
    return values[-1] if values else None


def kdj_crosses(rows: list[dict], max_items: int = 12) -> list[dict]:
    highs = [row["high"] for row in rows]
    lows = [row["low"] for row in rows]
    closes = [row["close"] for row in rows]
    values = kdj_series(highs, lows, closes, 9)
    crosses = []
    for index in range(1, len(values)):
        previous = values[index - 1]
        current = values[index]
        if previous is None or current is None:
            continue
        prev_k, prev_d, _ = previous
        k_value, d_value, j_value = current
        if prev_k <= prev_d and k_value > d_value:
            cross_type = "golden_cross"
        elif prev_k >= prev_d and k_value < d_value:
            cross_type = "death_cross"
        else:
            continue
        crosses.append(
            {
                "date": rows[index]["date"],
                "type": cross_type,
                "close": rounded(closes[index]),
                "k": rounded(k_value),
                "d": rounded(d_value),
                "j": rounded(j_value),
            }
        )
    return crosses[-max_items:]


def macd(closes: list[float]) -> tuple[float, float, float, float] | None:
    if len(closes) < 35:
        return None
    ema12 = ema(closes, 12)
    ema26 = ema(closes, 26)
    dif = [short - long for short, long in zip(ema12, ema26)]
    dea = ema(dif, 9)
    hist = [(d - e) * 2 for d, e in zip(dif, dea)]
    return dif[-1], dea[-1], hist[-1], hist[-2]


def atr(highs: list[float], lows: list[float], closes: list[float], n: int = 14) -> float | None:
    if len(closes) < n + 1:
        return None
    true_ranges = []
    for index in range(1, len(closes)):
        true_ranges.append(
            max(
                highs[index] - lows[index],
                abs(highs[index] - closes[index - 1]),
                abs(lows[index] - closes[index - 1]),
            )
        )
    return sum(true_ranges[-n:]) / n


def bollinger(closes: list[float], n: int = 20) -> tuple[float, float, float] | None:
    if len(closes) < n:
        return None
    window = closes[-n:]
    mid = sum(window) / n
    stdev = math.sqrt(sum((value - mid) ** 2 for value in window) / n)
    return mid, mid + 2 * stdev, mid - 2 * stdev


def rounded(value):
    if value is None:
        return None
    if isinstance(value, tuple):
        return [rounded(item) for item in value]
    return round(value, 4)


def build_indicators(
    rows: list[dict],
    timeframe: str = "daily",
    resolution: str | None = None,
    realtime: bool = False,
    data_source: str | None = None,
) -> dict:
    highs = [row["high"] for row in rows]
    lows = [row["low"] for row in rows]
    closes = [row["close"] for row in rows]
    volumes = [row["volume"] for row in rows]
    recent_lows = lows[-20:] if len(lows) >= 20 else lows
    recent_highs = highs[-20:] if len(highs) >= 20 else highs
    sma50_value = sma(closes, 50)
    sma200_value = sma(closes, 200)
    close = closes[-1] if closes else None
    return {
        "timeframe": timeframe,
        "resolution": resolution,
        "source": data_source,
        "is_intraday": timeframe == "intraday",
        "is_realtime": realtime,
        "last_date": rows[-1]["date"] if rows else None,
        "latest_bar_time": rows[-1].get("timestamp_utc") or rows[-1].get("timestamp") or rows[-1]["date"] if rows else None,
        "latest_bar_timestamp_utc": rows[-1].get("timestamp_utc") if rows else None,
        "last_close": rounded(closes[-1]) if closes else None,
        "sma20": rounded(sma(closes, 20)),
        "sma50": rounded(sma50_value),
        "sma200": rounded(sma200_value),
        "distance_to_sma20_pct": rounded((close / sma(closes, 20) - 1) * 100) if close and sma(closes, 20) else None,
        "distance_to_sma50_pct": rounded((close / sma50_value - 1) * 100) if close and sma50_value else None,
        "distance_to_sma200_pct": rounded((close / sma200_value - 1) * 100) if close and sma200_value else None,
        "rsi14": rounded(rsi(closes, 14)),
        "kdj_9_3_3": rounded(kdj(highs, lows, closes, 9)),
        "macd_12_26_9": rounded(macd(closes)),
        "bollinger20": rounded(bollinger(closes, 20)),
        "atr14": rounded(atr(highs, lows, closes, 14)),
        "volume": rounded(volumes[-1]) if volumes else None,
        "avg_volume20": rounded(sma(volumes, 20)),
        "support20": rounded(min(recent_lows)) if recent_lows else None,
        "resistance20": rounded(max(recent_highs)) if recent_highs else None,
        "distance_to_support20_pct": rounded((close / min(recent_lows) - 1) * 100) if close and recent_lows and min(recent_lows) else None,
        "distance_to_resistance20_pct": rounded((close / max(recent_highs) - 1) * 100) if close and recent_highs and max(recent_highs) else None,
        "signal_events": {
            "kdj_crosses": kdj_crosses(rows),
        },
        "indicator_metadata": {
            "kdj_9_3_3": {
                "source": "computed_from_ohlcv",
                "formula": "RSV=(close-low_9)/(high_9-low_9)*100; K=2/3*Kprev+1/3*RSV; D=2/3*Dprev+1/3*K; J=3*K-2*D",
                "parameters": "9,3,3",
                "basis": "completed OHLCV bars using high, low, and close",
                "data_source": data_source,
                "is_realtime": realtime,
            }
        },
        "row_count": len(rows),
    }


def pct_change(rows: list[dict], periods: int) -> float | None:
    if len(rows) <= periods:
        return None
    old = rows[-periods - 1]["close"]
    new = rows[-1]["close"]
    if old == 0:
        return None
    return (new / old - 1) * 100


def relative_strength(target_rows: list[dict], compare_rows: list[dict], periods: int = 20) -> dict:
    target_change = pct_change(target_rows, periods)
    compare_change = pct_change(compare_rows, periods)
    if target_change is None or compare_change is None:
        return {"status": "insufficient_data", "periods": periods}
    spread = target_change - compare_change
    if spread > 3:
        label = "outperforming"
    elif spread < -3:
        label = "underperforming"
    else:
        label = "neutral"
    return {
        "status": "ok",
        "periods": periods,
        "target_change_pct": rounded(target_change),
        "comparison_change_pct": rounded(compare_change),
        "spread_pct": rounded(spread),
        "classification": label,
    }


def technical_data_summary(
    rows: list[dict],
    benchmark_rows: list[dict] | None = None,
    sector_rows: list[dict] | None = None,
    timeframe: str = "daily",
    resolution: str | None = None,
    realtime: bool = False,
    data_source: str | None = None,
) -> dict:
    if not rows:
        return {"status": "no_data"}
    indicators = build_indicators(
        rows,
        timeframe=timeframe,
        resolution=resolution,
        realtime=realtime,
        data_source=data_source,
    )
    close = indicators["last_close"]
    sma50_value = indicators["sma50"]
    sma200_value = indicators["sma200"]
    support = indicators["support20"]
    resistance = indicators["resistance20"]
    volume = indicators["volume"]
    avg_volume20 = indicators["avg_volume20"]

    rs_items = {}
    if benchmark_rows:
        rs_items["benchmark"] = relative_strength(rows, benchmark_rows)
    if sector_rows:
        rs_items["sector"] = relative_strength(rows, sector_rows)

    if volume is not None and avg_volume20:
        volume_ratio = volume / avg_volume20
    else:
        volume_ratio = None

    if close is not None and support is not None and resistance is not None and close != support:
        upside = max(resistance - close, 0)
        downside = max(close - support, 0)
        reward_risk = None if downside == 0 else upside / downside
    else:
        upside = None
        downside = None
        reward_risk = None

    return {
        "status": "ok",
        "trend_structure_data": {
            "close": close,
            "sma50": sma50_value,
            "sma200": sma200_value,
            "close_above_sma50": close > sma50_value if close is not None and sma50_value is not None else None,
            "close_above_sma200": close > sma200_value if close is not None and sma200_value is not None else None,
            "change_20_period_pct": rounded(pct_change(rows, 20)),
        },
        "relative_strength_data": rs_items,
        "volume_data": {
            "volume": volume,
            "avg_volume20": avg_volume20,
            "volume_to_avg20_ratio": rounded(volume_ratio),
        },
        "support_resistance_data": {
            "support20": support,
            "resistance20": resistance,
            "distance_to_support20_pct": indicators["distance_to_support20_pct"],
            "distance_to_resistance20_pct": indicators["distance_to_resistance20_pct"],
            "upside_to_resistance": rounded(upside),
            "downside_to_support": rounded(downside),
            "raw_reward_risk_to_20_period_range": rounded(reward_risk),
        },
        "indicator_data": {
            "rsi14": indicators["rsi14"],
            "kdj_9_3_3": indicators["kdj_9_3_3"],
            "macd_12_26_9": indicators["macd_12_26_9"],
            "bollinger20": indicators["bollinger20"],
            "atr14": indicators["atr14"],
        },
        "signal_data": {
            "kdj_crosses": indicators["signal_events"]["kdj_crosses"],
        },
        "indicator_metadata": indicators["indicator_metadata"],
    }


def moving_average_series(values: list[float], period: int) -> list[float | None]:
    series: list[float | None] = [None] * len(values)
    for index in range(len(values)):
        if index + 1 >= period:
            series[index] = sum(values[index - period + 1 : index + 1]) / period
    return series


def make_chart(symbol: str, rows: list[dict], output_path: Path, title: str) -> str | None:
    try:
        import matplotlib.dates as mdates
        import matplotlib.pyplot as plt
        from matplotlib.patches import Rectangle
    except Exception:
        return None
    if len(rows) < 5:
        return None
    dates = [datetime.fromisoformat(row["date"]) for row in rows]
    opens = [row["open"] for row in rows]
    highs = [row["high"] for row in rows]
    lows = [row["low"] for row in rows]
    closes = [row["close"] for row in rows]
    volumes = [row["volume"] for row in rows]
    sma20_values = moving_average_series(closes, 20)
    sma50_values = moving_average_series(closes, 50)
    kdj_values = kdj_series(highs, lows, closes, 9)
    k_values = [value[0] if value else None for value in kdj_values]
    d_values = [value[1] if value else None for value in kdj_values]
    j_values = [value[2] if value else None for value in kdj_values]
    recent_lows = lows[-20:] if len(lows) >= 20 else lows
    recent_highs = highs[-20:] if len(highs) >= 20 else highs
    support = min(recent_lows) if recent_lows else None
    resistance = max(recent_highs) if recent_highs else None
    crosses = kdj_crosses(rows, max_items=50)

    date_numbers = mdates.date2num(dates)
    if len(date_numbers) > 1:
        gaps = sorted(date_numbers[index] - date_numbers[index - 1] for index in range(1, len(date_numbers)))
        candle_width = max(min(gaps[len(gaps) // 2] * 0.7, 0.8), 0.002)
    else:
        candle_width = 0.6

    fig, (ax_price, ax_volume, ax_kdj) = plt.subplots(
        3,
        1,
        figsize=(13, 8.5),
        sharex=True,
        gridspec_kw={"height_ratios": [3.0, 0.9, 1.2]},
    )

    for date_number, open_, high, low, close in zip(date_numbers, opens, highs, lows, closes):
        color = "#16a34a" if close >= open_ else "#dc2626"
        ax_price.vlines(date_number, low, high, color=color, linewidth=0.9, alpha=0.9)
        body_bottom = min(open_, close)
        body_height = max(abs(close - open_), 0.01)
        ax_price.add_patch(
            Rectangle(
                (date_number - candle_width / 2, body_bottom),
                candle_width,
                body_height,
                facecolor=color,
                edgecolor=color,
                alpha=0.75,
            )
        )

    ax_price.plot(dates, sma20_values, label="SMA20", linewidth=1.2, color="#2563eb")
    ax_price.plot(dates, sma50_values, label="SMA50", linewidth=1.2, color="#9333ea")
    if support is not None:
        ax_price.axhline(support, color="#16a34a", linestyle="--", linewidth=1.1, alpha=0.75, label="Support20")
        ax_price.text(date_numbers[-1], support, f" Support {support:.2f}", color="#166534", va="bottom", fontsize=8)
    if resistance is not None:
        ax_price.axhline(resistance, color="#dc2626", linestyle="--", linewidth=1.1, alpha=0.75, label="Resistance20")
        ax_price.text(date_numbers[-1], resistance, f" Resistance {resistance:.2f}", color="#991b1b", va="top", fontsize=8)
    for event in crosses:
        index = next((i for i, row in enumerate(rows) if row["date"] == event["date"]), None)
        if index is None:
            continue
        if event["type"] == "golden_cross":
            ax_price.scatter(date_numbers[index], closes[index], marker="^", s=46, color="#16a34a", zorder=5)
            ax_kdj.scatter(date_numbers[index], event["k"], marker="^", s=36, color="#16a34a", zorder=5)
        else:
            ax_price.scatter(date_numbers[index], closes[index], marker="v", s=46, color="#dc2626", zorder=5)
            ax_kdj.scatter(date_numbers[index], event["k"], marker="v", s=36, color="#dc2626", zorder=5)

    ax_price.set_title(f"{symbol} {title}")
    ax_price.set_ylabel("Price")
    ax_price.grid(True, alpha=0.25)
    ax_price.legend(loc="upper left")
    bar_colors = ["#16a34a" if close >= open_ else "#dc2626" for open_, close in zip(opens, closes)]
    ax_volume.bar(dates, volumes, width=candle_width, alpha=0.35, color=bar_colors)
    ax_volume.set_ylabel("Volume")
    ax_volume.grid(True, alpha=0.2)
    ax_kdj.plot(dates, k_values, label="K", linewidth=1.2, color="#2563eb")
    ax_kdj.plot(dates, d_values, label="D", linewidth=1.2, color="#f97316")
    ax_kdj.plot(dates, j_values, label="J", linewidth=1.0, color="#6b7280")
    ax_kdj.axhline(80, color="#dc2626", linestyle="--", linewidth=0.8, alpha=0.55)
    ax_kdj.axhline(20, color="#16a34a", linestyle="--", linewidth=0.8, alpha=0.55)
    ax_kdj.set_ylabel("KDJ")
    ax_kdj.set_ylim(-20, 120)
    ax_kdj.grid(True, alpha=0.25)
    ax_kdj.legend(loc="upper left", ncol=3)
    formatter = "%m-%d %H:%M" if any("T" in row["date"] or " " in row["date"] for row in rows) else "%Y-%m-%d"
    ax_kdj.xaxis.set_major_formatter(mdates.DateFormatter(formatter))
    fig.autofmt_xdate()
    fig.tight_layout()
    fig.savefig(output_path, dpi=160)
    plt.close(fig)
    return str(output_path)


def parse_row_datetime(row: dict) -> datetime | None:
    value = row.get("timestamp_utc") or row.get("timestamp") or row.get("date")
    if value is None:
        return None
    text = str(value).replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(text)
    except ValueError:
        try:
            return datetime.strptime(text[:10], "%Y-%m-%d")
        except ValueError:
            return None


def intraday_coverage(rows: list[dict]) -> dict:
    if not rows:
        return {
            "row_count": 0,
            "latest_bar_time": None,
            "latest_bar_timestamp_utc": None,
            "has_intraday_today": False,
            "usable_for_report": False,
        }
    latest = rows[-1]
    latest_time = latest.get("timestamp_utc") or latest.get("timestamp") or latest.get("date")
    latest_dt = parse_row_datetime(latest)
    today_utc = datetime.now(timezone.utc).date()
    return {
        "row_count": len(rows),
        "latest_bar_time": latest_time,
        "latest_bar_timestamp_utc": latest.get("timestamp_utc"),
        "has_intraday_today": bool(latest_dt and latest_dt.date() == today_utc),
        "usable_for_report": True,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("ticker")
    parser.add_argument("--key-file")
    parser.add_argument("--output-dir", default="outputs")
    parser.add_argument("--benchmark", default="SPY")
    parser.add_argument("--sector")
    parser.add_argument(
        "--intraday-window",
        help="Optional intraday candle window: today, 1d, 2d, 5d, 1w, 2w, 1m, 3m, or custom like 10d.",
    )
    parser.add_argument("--intraday-resolution", default="5", choices=["1", "5", "15", "30", "60"])
    parser.add_argument(
        "--intraday-source",
        default="yahoo",
        choices=["yahoo", "auto", "finnhub", "alpha_vantage"],
        help=(
            "Intraday data source. Default yahoo returns current-session bars for report analysis. "
            "Use auto/finnhub only when a realtime-capable candle source is explicitly required."
        ),
    )
    parser.add_argument("--no-charts", action="store_true")
    args = parser.parse_args()

    ticker = args.ticker.upper()
    output_dir = get_output_dir() if args.output_dir == "auto" else Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    keys = load_keys(args.key_file)

    daily = get_daily_ohlcv(ticker, keys)
    weekly = get_weekly_ohlcv(ticker, keys)
    quote = get_quote(ticker, keys)
    intraday = {"status": "skipped", "rows": []}
    intraday_realtime = False
    if args.intraday_window:
        intraday = get_intraday_ohlcv(ticker, keys, args.intraday_resolution, args.intraday_window, args.intraday_source)
        intraday_realtime = bool(intraday.get("is_realtime"))
    benchmark_daily = {"status": "skipped", "rows": []}
    sector_daily = {"status": "skipped", "rows": []}
    if args.benchmark:
        benchmark_daily = get_daily_ohlcv(args.benchmark.upper(), keys)
    if args.sector:
        sector_daily = get_daily_ohlcv(args.sector.upper(), keys)

    charts = {}
    if not args.no_charts:
        if daily["status"] == "ok":
            charts["daily"] = make_chart(ticker, daily["rows"][-100:], output_dir / f"{ticker}_daily_chart.png", "Daily")
        if weekly["status"] == "ok":
            charts["weekly"] = make_chart(ticker, weekly["rows"][-156:], output_dir / f"{ticker}_weekly_chart.png", "Weekly")
        if intraday["status"] == "ok":
            charts["intraday"] = make_chart(
                ticker,
                intraday["rows"][-240:],
                output_dir / f"{ticker}_intraday_{args.intraday_window}_{args.intraday_resolution}m_chart.png",
                f"Intraday {args.intraday_resolution}m {args.intraday_window}",
            )

    intraday_coverage_data = intraday_coverage(intraday["rows"]) if intraday["status"] == "ok" else intraday_coverage([])
    intraday_provider = intraday.get("provider")
    intraday_data_quality = (
        "realtime_candles"
        if intraday_realtime
        else "prefetched_web_bars"
        if intraday_provider == "prefetched_web"
        else "yfinance_bars"
        if intraday_provider == "yfinance"
        else "current_session_bars"
        if intraday_coverage_data["has_intraday_today"]
        else "delayed_or_historical_bars"
    )

    bundle = {
        "ticker": ticker,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "analysis_window": {
            "daily": daily.get("source"),
            "weekly": weekly.get("source"),
            "intraday_window": args.intraday_window,
            "intraday_resolution": args.intraday_resolution if args.intraday_window else None,
            "intraday_source_requested": args.intraday_source if args.intraday_window else None,
        },
        "quote": quote,
        "daily": {
            "status": daily["status"],
            "notice": daily.get("notice"),
            "source": daily.get("source"),
            "provider": daily.get("provider"),
            "indicators": build_indicators(
                daily["rows"],
                timeframe="daily",
                realtime=False,
                data_source=daily.get("source"),
            )
            if daily["status"] == "ok"
            else None,
        },
        "weekly": {
            "status": weekly["status"],
            "notice": weekly.get("notice"),
            "source": weekly.get("source"),
            "provider": weekly.get("provider"),
            "indicators": build_indicators(
                weekly["rows"],
                timeframe="weekly",
                realtime=False,
                data_source=weekly.get("source"),
            )
            if weekly["status"] == "ok"
            else None,
        },
        "intraday": {
            "status": intraday["status"],
            "notice": intraday.get("notice"),
            "source": intraday.get("source"),
            "provider": intraday.get("provider"),
            "is_realtime": intraday_realtime,
            "data_quality": intraday_data_quality,
            "has_intraday_today": intraday_coverage_data["has_intraday_today"],
            "usable_for_report": intraday_coverage_data["usable_for_report"],
            "row_count": intraday_coverage_data["row_count"],
            "latest_bar_time": intraday_coverage_data["latest_bar_time"],
            "latest_bar_timestamp_utc": intraday_coverage_data["latest_bar_timestamp_utc"],
            "fallback_from": intraday.get("fallback_from"),
            "fallback": intraday.get("fallback"),
            "resolution": intraday.get("resolution") or (args.intraday_resolution if args.intraday_window else None),
            "interval": intraday.get("interval"),
            "window": args.intraday_window,
            "from_utc": intraday.get("from_utc"),
            "to_utc": intraday.get("to_utc"),
            "timestamp_note": intraday.get("timestamp_note"),
            "indicators": build_indicators(
                intraday["rows"],
                timeframe="intraday",
                resolution=args.intraday_resolution,
                realtime=intraday_realtime,
                data_source=intraday.get("source"),
            )
            if intraday["status"] == "ok"
            else None,
            "technical_data_summary": technical_data_summary(
                intraday["rows"],
                timeframe="intraday",
                resolution=args.intraday_resolution,
                realtime=intraday_realtime,
                data_source=intraday.get("source"),
            )
            if intraday["status"] == "ok"
            else None,
        },
        "charts": {name: path for name, path in charts.items() if path},
        "technical_data_summary": technical_data_summary(
            daily["rows"] if daily["status"] == "ok" else [],
            benchmark_daily["rows"] if benchmark_daily["status"] == "ok" else None,
            sector_daily["rows"] if sector_daily["status"] == "ok" else None,
            timeframe="daily",
            realtime=False,
            data_source=daily.get("source") if daily["status"] == "ok" else None,
        ),
        "comparisons": {
            "benchmark": {"symbol": args.benchmark.upper() if args.benchmark else None, "status": benchmark_daily["status"]},
            "sector": {"symbol": args.sector.upper() if args.sector else None, "status": sector_daily["status"]},
        },
        "data_health": {
            "quote_status": quote.get("status"),
            "quote_source": quote.get("source"),
            "quote_provider": quote.get("provider"),
            "daily_status": daily["status"],
            "daily_source": daily.get("source"),
            "daily_provider": daily.get("provider"),
            "weekly_status": weekly["status"],
            "weekly_source": weekly.get("source"),
            "weekly_provider": weekly.get("provider"),
            "intraday_status": intraday["status"],
            "intraday_source": intraday.get("source"),
            "intraday_provider": intraday.get("provider"),
            "intraday_data_quality": intraday_data_quality,
            "intraday_has_current_day_bars": intraday_coverage_data["has_intraday_today"],
            "intraday_usable_for_report": intraday_coverage_data["usable_for_report"],
            "benchmark_status": benchmark_daily["status"],
            "benchmark_source": benchmark_daily.get("source"),
            "benchmark_provider": benchmark_daily.get("provider"),
            "sector_status": sector_daily["status"],
            "sector_source": sector_daily.get("source"),
            "sector_provider": sector_daily.get("provider"),
            "chart_status": "ok" if charts else "not_generated",
        },
    }
    bundle_path = output_dir / f"{ticker}_technical_bundle.json"
    bundle_path.write_text(json.dumps(bundle, indent=2), encoding="utf-8")
    print(json.dumps({"bundle": str(bundle_path), "charts": bundle["charts"], "data_health": bundle["data_health"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
