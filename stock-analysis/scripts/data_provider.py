#!/usr/bin/env python3
"""Cross-platform market data provider for stock-analysis skills.

Provider order:
1. Direct network data sources (Finnhub, Alpha Vantage, Yahoo chart).
2. Pre-fetched JSON files written by Claude web tools.
3. Optional yfinance fallback when installed and network is available.

This module never prints API keys. Callers should disclose `provider` and
`source` fields in report Data Health sections.
"""

from __future__ import annotations

import json
import os
import re
import socket
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any


PREFETCHED_DIR = Path(os.environ.get("PREFETCH_DIR", "/tmp/prefetched_data"))


def direct_disabled() -> bool:
    return os.environ.get("STOCK_ANALYSIS_DISABLE_DIRECT", "").strip().lower() in {"1", "true", "yes", "on"}


def network_ok(host: str, timeout: float = 3.0) -> bool:
    if direct_disabled():
        return False
    try:
        socket.create_connection((host, 443), timeout=timeout).close()
        return True
    except OSError:
        return False


def get_output_dir() -> Path:
    candidates = [
        Path("/mnt/user-data/outputs"),
        Path("/mnt/data"),
        Path("./outputs"),
    ]
    for candidate in candidates:
        if candidate.parent.exists():
            candidate.mkdir(parents=True, exist_ok=True)
            return candidate
    output_dir = Path("./outputs")
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir


def load_keys(path: str | None) -> dict[str, str]:
    keys: dict[str, str] = {}
    for name in ("FINNHUB_API_KEY", "ALPHA_VANTAGE_API_KEY", "FRED_API_KEY"):
        if os.environ.get(name):
            keys[name] = os.environ[name].strip()

    candidates: list[Path] = []
    if path:
        candidates.append(Path(path))
    else:
        candidates.extend(
            [
                Path("key.txt"),
                Path("/mnt/user-data/uploads/key.txt"),
                Path("/mnt/data/key.txt"),
            ]
        )

    for candidate in candidates:
        if not candidate.exists():
            continue
        text = candidate.read_text(encoding="utf-8")
        for line in text.splitlines():
            match = re.match(
                r"\s*([A-Z0-9_]+|finnhub|av|alpha[_ -]?vantage|fred)\s*[:=]\s*(.+?)\s*$",
                line,
                re.I,
            )
            if not match:
                continue
            name = match.group(1).upper()
            if name == "FINNHUB":
                name = "FINNHUB_API_KEY"
            if name == "AV" or name.startswith("ALPHA"):
                name = "ALPHA_VANTAGE_API_KEY"
            if name == "FRED":
                name = "FRED_API_KEY"
            keys[name] = match.group(2).strip().strip("\"'")
    return keys


def sanitize_text(text: str | None, secrets: list[str] | tuple[str, ...] = ()) -> str | None:
    if text is None:
        return None
    safe = str(text)
    for secret in secrets:
        if secret:
            safe = safe.replace(secret, "[REDACTED]")
    safe = re.sub(r"(API key as )([A-Za-z0-9_-]+)", r"\1[REDACTED]", safe, flags=re.I)
    safe = re.sub(r"((?:apikey|token)=)[^&\s]+", r"\1[REDACTED]", safe, flags=re.I)
    return safe


def get_json(url: str, timeout: int = 30) -> dict:
    request = urllib.request.Request(url, headers={"User-Agent": "stock-analysis-skill/1.1"})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def provider_result(status: str, rows: list[dict] | None = None, **extra: Any) -> dict:
    out = {"status": status, "rows": rows or []}
    out.update(extra)
    return out


def prefetched_path(ticker: str, suffix: str) -> Path:
    return PREFETCHED_DIR / f"{ticker.upper()}_{suffix}.json"


def read_prefetched_json(ticker: str, suffix: str) -> Any | None:
    path = prefetched_path(ticker, suffix)
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def as_float(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(str(value).replace(",", ""))
    except (TypeError, ValueError):
        return None


def normalize_ohlcv_rows(data: Any, source_name: str) -> list[dict]:
    if isinstance(data, dict):
        if isinstance(data.get("rows"), list):
            data = data["rows"]
        elif isinstance(data.get("data"), list):
            data = data["data"]
        elif isinstance(data.get("prices"), list):
            data = data["prices"]
    if not isinstance(data, list):
        return []

    rows: list[dict] = []
    for item in data:
        if not isinstance(item, dict):
            continue
        date = item.get("date") or item.get("timestamp_utc") or item.get("timestamp") or item.get("time")
        close = as_float(item.get("close") or item.get("c") or item.get("Close"))
        high = as_float(item.get("high") or item.get("h") or item.get("High"))
        low = as_float(item.get("low") or item.get("l") or item.get("Low"))
        open_ = as_float(item.get("open") or item.get("o") or item.get("Open"))
        volume = as_float(item.get("volume") or item.get("v") or item.get("Volume")) or 0.0
        if not date or close is None or high is None or low is None or open_ is None:
            continue
        row = {
            "date": str(date),
            "open": open_,
            "high": high,
            "low": low,
            "close": close,
            "volume": volume,
        }
        if item.get("timestamp_utc"):
            row["timestamp_utc"] = str(item["timestamp_utc"])
        elif "T" in str(date):
            row["timestamp_utc"] = str(date)
        rows.append(row)
    rows.sort(key=lambda row: row["date"])
    return rows


def get_prefetched_quote(ticker: str) -> dict:
    data = read_prefetched_json(ticker, "quote")
    if not isinstance(data, dict):
        return {"status": "missing_prefetch", "source": "none", "provider": "none"}
    quote = {
        "status": "ok",
        "source": data.get("source_name") or "prefetched_web",
        "provider": "prefetched_web",
        "source_url": data.get("source_url"),
        "c": as_float(data.get("c") or data.get("current") or data.get("price")),
        "h": as_float(data.get("h") or data.get("high")),
        "l": as_float(data.get("l") or data.get("low")),
        "o": as_float(data.get("o") or data.get("open")),
        "pc": as_float(data.get("pc") or data.get("previous_close") or data.get("prev_close")),
    }
    if data.get("t"):
        quote["t"] = data["t"]
    if data.get("timestamp_utc"):
        quote["timestamp_utc"] = data["timestamp_utc"]
    elif data.get("date"):
        quote["timestamp_utc"] = str(data["date"])
    if quote["c"] is None:
        return {"status": "invalid_prefetch", "source": "prefetched_web", "provider": "prefetched_web"}
    return quote


def get_prefetched_ohlcv(ticker: str, suffix: str, source_name: str) -> dict:
    data = read_prefetched_json(ticker, suffix)
    if data is None:
        return provider_result("missing_prefetch", source="none", provider="none")
    rows = normalize_ohlcv_rows(data, source_name)
    return provider_result(
        "ok" if rows else "invalid_prefetch",
        rows,
        source=source_name,
        provider="prefetched_web",
        timestamp_note="Prefetched web data written by Claude web tools; intraday precision may be lower.",
    )


def finnhub_quote(ticker: str, key: str | None) -> dict:
    if not key:
        return {"status": "missing_key", "source": "finnhub", "provider": "none"}
    if not network_ok("finnhub.io"):
        return {"status": "network_blocked", "source": "finnhub", "provider": "none"}
    url = "https://finnhub.io/api/v1/quote?" + urllib.parse.urlencode({"symbol": ticker, "token": key})
    try:
        quote = get_json(url)
        if quote.get("t"):
            quote["timestamp_utc"] = datetime.fromtimestamp(int(quote["t"]), tz=timezone.utc).isoformat()
        quote["status"] = "ok"
        quote["source"] = "finnhub"
        quote["provider"] = "direct_api"
        return quote
    except Exception as exc:  # noqa: BLE001
        return {"status": "error", "error": type(exc).__name__, "source": "finnhub", "provider": "none"}


def finnhub_candles(ticker: str, key: str | None, resolution: str, from_ts: int, to_ts: int) -> dict:
    if not key:
        return provider_result("missing_key", source="finnhub", provider="none")
    if not network_ok("finnhub.io"):
        return provider_result("network_blocked", source="finnhub", provider="none")
    url = "https://finnhub.io/api/v1/stock/candle?" + urllib.parse.urlencode(
        {"symbol": ticker, "resolution": resolution, "from": from_ts, "to": to_ts, "token": key}
    )
    try:
        data = get_json(url)
    except Exception as exc:  # noqa: BLE001
        return provider_result("error", source="finnhub", provider="none", error=type(exc).__name__)

    if data.get("s") != "ok":
        return provider_result(
            data.get("s") or "notice",
            source="finnhub",
            provider="none",
            notice=sanitize_text(data.get("error") or data.get("s") or "no intraday candle data", [key]),
            resolution=resolution,
            from_utc=datetime.fromtimestamp(from_ts, tz=timezone.utc).isoformat(),
            to_utc=datetime.fromtimestamp(to_ts, tz=timezone.utc).isoformat(),
        )

    rows = []
    for open_, high, low, close, volume, timestamp in zip(
        data.get("o", []), data.get("h", []), data.get("l", []), data.get("c", []), data.get("v", []), data.get("t", [])
    ):
        timestamp_utc = datetime.fromtimestamp(int(timestamp), tz=timezone.utc).isoformat()
        rows.append(
            {
                "date": timestamp_utc,
                "timestamp_utc": timestamp_utc,
                "open": float(open_),
                "high": float(high),
                "low": float(low),
                "close": float(close),
                "volume": float(volume),
            }
        )
    rows.sort(key=lambda row: row["date"])
    return provider_result(
        "ok",
        rows,
        source="finnhub",
        provider="direct_api",
        resolution=resolution,
        from_utc=datetime.fromtimestamp(from_ts, tz=timezone.utc).isoformat(),
        to_utc=datetime.fromtimestamp(to_ts, tz=timezone.utc).isoformat(),
    )


def alpha_vantage_series(ticker: str, function: str, key: str | None, outputsize: str = "compact") -> dict:
    if not key:
        return provider_result("missing_key", source="alpha_vantage", provider="none")
    if not network_ok("www.alphavantage.co"):
        return provider_result("network_blocked", source="alpha_vantage", provider="none")
    url = "https://www.alphavantage.co/query?" + urllib.parse.urlencode(
        {"function": function, "symbol": ticker, "outputsize": outputsize, "apikey": key}
    )
    try:
        data = get_json(url)
    except Exception as exc:  # noqa: BLE001
        return provider_result("error", source="alpha_vantage", provider="none", error=type(exc).__name__)
    if data.get("Note") or data.get("Information") or data.get("Error Message"):
        return provider_result(
            "notice",
            source="alpha_vantage",
            provider="none",
            notice=sanitize_text(data.get("Note") or data.get("Information") or data.get("Error Message"), [key]),
        )
    key_name = "Time Series (Daily)" if "DAILY" in function else "Weekly Time Series"
    series = data.get(key_name, {})
    rows = []
    for date, values in series.items():
        rows.append(
            {
                "date": date,
                "open": float(values["1. open"]),
                "high": float(values["2. high"]),
                "low": float(values["3. low"]),
                "close": float(values["4. close"]),
                "volume": float(values.get("5. volume", 0)),
            }
        )
    rows.sort(key=lambda row: row["date"])
    return provider_result("ok" if rows else "no_data", rows, source="alpha_vantage", provider="direct_api")


def alpha_vantage_intraday_series(ticker: str, interval: str, key: str | None, window_seconds: int | None = None) -> dict:
    if not key:
        return provider_result("missing_key", source="alpha_vantage", provider="none")
    if not network_ok("www.alphavantage.co"):
        return provider_result("network_blocked", source="alpha_vantage", provider="none")
    outputsize = "full" if window_seconds and window_seconds > 2 * 24 * 60 * 60 else "compact"
    url = "https://www.alphavantage.co/query?" + urllib.parse.urlencode(
        {
            "function": "TIME_SERIES_INTRADAY",
            "symbol": ticker,
            "interval": interval,
            "outputsize": outputsize,
            "apikey": key,
        }
    )
    try:
        data = get_json(url)
    except Exception as exc:  # noqa: BLE001
        return provider_result("error", source="alpha_vantage", provider="none", error=type(exc).__name__)
    if data.get("Note") or data.get("Information") or data.get("Error Message"):
        return provider_result(
            "notice",
            source="alpha_vantage",
            provider="none",
            notice=sanitize_text(data.get("Note") or data.get("Information") or data.get("Error Message"), [key]),
        )
    key_name = f"Time Series ({interval})"
    series = data.get(key_name, {})
    rows = []
    cutoff = datetime.now() - timedelta(seconds=window_seconds) if window_seconds else None
    for timestamp, values in series.items():
        parsed_timestamp = datetime.fromisoformat(timestamp)
        if cutoff and parsed_timestamp < cutoff:
            continue
        rows.append(
            {
                "date": timestamp,
                "timestamp": timestamp,
                "open": float(values["1. open"]),
                "high": float(values["2. high"]),
                "low": float(values["3. low"]),
                "close": float(values["4. close"]),
                "volume": float(values.get("5. volume", 0)),
            }
        )
    rows.sort(key=lambda row: row["date"])
    return provider_result(
        "ok" if rows else "no_data",
        rows,
        source="alpha_vantage",
        provider="direct_api",
        interval=interval,
        outputsize=outputsize,
        timestamp_note="Alpha Vantage intraday timestamps are returned as exchange-local strings.",
    )


def yahoo_range_for_window(window: str) -> str:
    normalized = window.strip().lower()
    if normalized in {"today", "1d"}:
        return "1d"
    if normalized in {"2d", "5d", "1w"}:
        return "5d"
    if normalized in {"2w", "1m"}:
        return "1mo"
    return "3mo"


def yahoo_chart_series(ticker: str, interval: str, window: str) -> dict:
    if not network_ok("query1.finance.yahoo.com"):
        return provider_result("network_blocked", source="yahoo_chart", provider="none")
    range_value = yahoo_range_for_window(window)
    url = "https://query1.finance.yahoo.com/v8/finance/chart/" + urllib.parse.quote(ticker) + "?" + urllib.parse.urlencode(
        {"range": range_value, "interval": interval, "includePrePost": "false"}
    )
    try:
        data = get_json(url)
    except Exception as exc:  # noqa: BLE001
        return provider_result("error", source="yahoo_chart", provider="none", error=type(exc).__name__)
    chart = data.get("chart", {})
    if chart.get("error"):
        return provider_result("error", source="yahoo_chart", provider="none", notice=sanitize_text(str(chart["error"])))
    results = chart.get("result") or []
    if not results:
        return provider_result("no_data", source="yahoo_chart", provider="none")
    result = results[0]
    timestamps = result.get("timestamp") or []
    quote_items = (result.get("indicators", {}).get("quote") or [{}])[0]
    rows = []
    for timestamp, open_, high, low, close, volume in zip(
        timestamps,
        quote_items.get("open") or [],
        quote_items.get("high") or [],
        quote_items.get("low") or [],
        quote_items.get("close") or [],
        quote_items.get("volume") or [],
    ):
        if None in (open_, high, low, close):
            continue
        timestamp_utc = datetime.fromtimestamp(int(timestamp), tz=timezone.utc).isoformat()
        rows.append(
            {
                "date": timestamp_utc,
                "timestamp_utc": timestamp_utc,
                "open": float(open_),
                "high": float(high),
                "low": float(low),
                "close": float(close),
                "volume": float(volume or 0),
            }
        )
    rows.sort(key=lambda row: row["date"])
    return provider_result(
        "ok" if rows else "no_data",
        rows,
        source="yahoo_chart",
        provider="direct_api",
        range=range_value,
        interval=interval,
        timestamp_note="Yahoo chart timestamps are UTC and may be delayed.",
    )


def yfinance_quote(ticker: str) -> dict:
    if direct_disabled():
        return {"status": "network_blocked", "source": "yfinance", "provider": "none"}
    try:
        import yfinance as yf  # type: ignore

        info = yf.Ticker(ticker).fast_info
        return {
            "status": "ok",
            "source": "yfinance",
            "provider": "yfinance",
            "c": as_float(getattr(info, "last_price", None) or info.get("last_price")),
            "h": as_float(getattr(info, "day_high", None) or info.get("day_high")),
            "l": as_float(getattr(info, "day_low", None) or info.get("day_low")),
            "o": as_float(getattr(info, "open", None) or info.get("open")),
            "pc": as_float(getattr(info, "previous_close", None) or info.get("previous_close")),
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        }
    except ImportError:
        return {"status": "missing_dependency", "source": "yfinance", "provider": "none"}
    except Exception as exc:  # noqa: BLE001
        return {"status": "error", "error": type(exc).__name__, "source": "yfinance", "provider": "none"}


def yfinance_history(ticker: str, period: str, interval: str, source_name: str) -> dict:
    if direct_disabled():
        return provider_result("network_blocked", source=source_name, provider="none")
    try:
        import yfinance as yf  # type: ignore

        df = yf.Ticker(ticker).history(period=period, interval=interval)
    except ImportError:
        return provider_result("missing_dependency", source=source_name, provider="none")
    except Exception as exc:  # noqa: BLE001
        return provider_result("error", source=source_name, provider="none", error=type(exc).__name__)

    rows = []
    for idx, row in df.iterrows():
        timestamp = idx.to_pydatetime()
        date_value = timestamp.astimezone(timezone.utc).isoformat() if timestamp.tzinfo else timestamp.isoformat()
        rows.append(
            {
                "date": date_value[:10] if interval == "1d" or interval == "1wk" else date_value,
                "timestamp_utc": date_value if interval not in {"1d", "1wk"} else None,
                "open": float(row["Open"]),
                "high": float(row["High"]),
                "low": float(row["Low"]),
                "close": float(row["Close"]),
                "volume": float(row.get("Volume", 0)),
            }
        )
    rows = [{k: v for k, v in item.items() if v is not None} for item in rows]
    rows.sort(key=lambda row: row["date"])
    return provider_result("ok" if rows else "no_data", rows, source=source_name, provider="yfinance")


def get_quote(ticker: str, keys: dict[str, str]) -> dict:
    attempts = []
    direct = finnhub_quote(ticker, keys.get("FINNHUB_API_KEY"))
    if direct.get("status") == "ok":
        return direct
    attempts.append({"source": "finnhub", "status": direct.get("status"), "notice": direct.get("notice") or direct.get("error")})

    prefetched = get_prefetched_quote(ticker)
    if prefetched.get("status") == "ok":
        prefetched["fallback_from"] = attempts
        return prefetched
    attempts.append({"source": "prefetched_web", "status": prefetched.get("status")})

    yf_quote = yfinance_quote(ticker)
    if yf_quote.get("status") == "ok":
        yf_quote["fallback_from"] = attempts
        return yf_quote
    attempts.append({"source": "yfinance", "status": yf_quote.get("status"), "notice": yf_quote.get("error")})

    return {"status": "all_providers_failed", "source": "none", "provider": "none", "fallback": attempts}


def get_daily_ohlcv(ticker: str, keys: dict[str, str], days: int = 252) -> dict:
    attempts = []
    # AlphaVantage "compact" returns 100 bars; "full" returns ~20 years. Auto-bump when caller wants more.
    av_outputsize = "full" if days > 100 else "compact"
    direct = alpha_vantage_series(ticker, "TIME_SERIES_DAILY", keys.get("ALPHA_VANTAGE_API_KEY"), outputsize=av_outputsize)
    if direct.get("status") == "ok":
        direct["rows"] = direct["rows"][-days:]
        return direct
    attempts.append({"source": "alpha_vantage", "status": direct.get("status"), "notice": direct.get("notice") or direct.get("error")})

    prefetched = get_prefetched_ohlcv(ticker, "daily", "prefetched_daily")
    if prefetched.get("status") == "ok":
        prefetched["rows"] = prefetched["rows"][-days:]
        prefetched["fallback_from"] = attempts
        return prefetched
    attempts.append({"source": "prefetched_daily", "status": prefetched.get("status")})

    # yfinance period syntax: use year units for long windows.
    if days <= 30:
        yf_period = f"{days}d"
    elif days <= 365:
        yf_period = "1y"
    elif days <= 365 * 2:
        yf_period = "2y"
    elif days <= 365 * 5:
        yf_period = "5y"
    elif days <= 365 * 10:
        yf_period = "10y"
    else:
        yf_period = "max"
    yf_daily = yfinance_history(ticker, yf_period, "1d", "yfinance_daily")
    if yf_daily.get("status") == "ok":
        yf_daily["rows"] = yf_daily["rows"][-days:]
        yf_daily["fallback_from"] = attempts
        return yf_daily
    attempts.append({"source": "yfinance_daily", "status": yf_daily.get("status"), "notice": yf_daily.get("error")})
    return provider_result("all_providers_failed", source="none", provider="none", fallback=attempts)


def get_weekly_ohlcv(ticker: str, keys: dict[str, str]) -> dict:
    attempts = []
    direct = alpha_vantage_series(ticker, "TIME_SERIES_WEEKLY", keys.get("ALPHA_VANTAGE_API_KEY"))
    if direct.get("status") == "ok":
        return direct
    attempts.append({"source": "alpha_vantage", "status": direct.get("status"), "notice": direct.get("notice") or direct.get("error")})

    prefetched = get_prefetched_ohlcv(ticker, "weekly", "prefetched_weekly")
    if prefetched.get("status") == "ok":
        prefetched["fallback_from"] = attempts
        return prefetched
    attempts.append({"source": "prefetched_weekly", "status": prefetched.get("status")})

    yf_weekly = yfinance_history(ticker, "5y", "1wk", "yfinance_weekly")
    if yf_weekly.get("status") == "ok":
        yf_weekly["fallback_from"] = attempts
        return yf_weekly
    attempts.append({"source": "yfinance_weekly", "status": yf_weekly.get("status"), "notice": yf_weekly.get("error")})
    return provider_result("all_providers_failed", source="none", provider="none", fallback=attempts)


def get_intraday_ohlcv(ticker: str, keys: dict[str, str], resolution: str, window: str, requested_source: str) -> dict:
    window_seconds = intraday_window_seconds(window)
    if window_seconds is None:
        return provider_result("invalid_window", source="none", provider="none", notice="Unsupported intraday window")

    attempts = []
    to_ts = int(datetime.now(timezone.utc).timestamp())
    from_ts = int((datetime.now(timezone.utc) - timedelta(seconds=window_seconds)).timestamp())

    if requested_source in {"auto", "finnhub"}:
        direct_finnhub = finnhub_candles(ticker, keys.get("FINNHUB_API_KEY"), resolution, from_ts, to_ts)
        if direct_finnhub.get("status") == "ok":
            direct_finnhub["is_realtime"] = True
            return direct_finnhub
        attempts.append({"source": "finnhub", "status": direct_finnhub.get("status"), "notice": direct_finnhub.get("notice") or direct_finnhub.get("error")})

    if requested_source in {"auto", "alpha_vantage"}:
        direct_av = alpha_vantage_intraday_series(ticker, f"{resolution}min", keys.get("ALPHA_VANTAGE_API_KEY"), window_seconds)
        if direct_av.get("status") == "ok":
            direct_av["fallback_from"] = attempts or None
            direct_av["is_realtime"] = False
            return direct_av
        attempts.append({"source": "alpha_vantage", "status": direct_av.get("status"), "notice": direct_av.get("notice") or direct_av.get("error")})

    if requested_source in {"yahoo", "auto"}:
        direct_yahoo = yahoo_chart_series(ticker, f"{resolution}m", window)
        if direct_yahoo.get("status") == "ok":
            direct_yahoo["fallback_from"] = attempts or None
            direct_yahoo["is_realtime"] = False
            return direct_yahoo
        attempts.append({"source": "yahoo_chart", "status": direct_yahoo.get("status"), "notice": direct_yahoo.get("notice") or direct_yahoo.get("error")})

    prefetched = get_prefetched_ohlcv(ticker, "intraday", "prefetched_intraday")
    if prefetched.get("status") == "ok":
        prefetched["fallback_from"] = attempts
        prefetched["is_realtime"] = False
        prefetched["resolution"] = resolution
        prefetched["window"] = window
        return prefetched
    attempts.append({"source": "prefetched_intraday", "status": prefetched.get("status")})

    yf_intraday = yfinance_history(ticker, yahoo_range_for_window(window), f"{resolution}m", "yfinance_intraday")
    if yf_intraday.get("status") == "ok":
        yf_intraday["fallback_from"] = attempts
        yf_intraday["is_realtime"] = False
        yf_intraday["resolution"] = resolution
        yf_intraday["window"] = window
        return yf_intraday
    attempts.append({"source": "yfinance_intraday", "status": yf_intraday.get("status"), "notice": yf_intraday.get("error")})
    return provider_result("all_providers_failed", source="none", provider="none", fallback=attempts)


def intraday_window_seconds(window: str) -> int | None:
    normalized = window.strip().lower()
    if normalized in {"today", "1d"}:
        return 24 * 60 * 60
    if normalized.endswith("d") and normalized[:-1].isdigit():
        return int(normalized[:-1]) * 24 * 60 * 60
    if normalized.endswith("w") and normalized[:-1].isdigit():
        return int(normalized[:-1]) * 7 * 24 * 60 * 60
    if normalized.endswith("m") and normalized[:-1].isdigit():
        return int(normalized[:-1]) * 30 * 24 * 60 * 60
    return None


# ---------------------------------------------------------------------------
# Fundamentals history (added for stock-backtest skill).
# Returns quarterly time series of EPS / revenue / FCF / debt / equity /
# current assets/liabilities / shares / dividends. Used by persona-mode
# backtests. Apply embargo of period_end + 60 days as a filing-date proxy.
# ---------------------------------------------------------------------------


def _pick(df_index_labels: list[str], candidates: list[str]) -> str | None:
    """Find the first candidate label that matches any row in a yfinance frame."""
    lowered = {str(label).strip().lower(): label for label in df_index_labels}
    for candidate in candidates:
        key = candidate.strip().lower()
        if key in lowered:
            return lowered[key]
        # try fuzzy substring match
        for low, original in lowered.items():
            if key in low:
                return original
    return None


def _row_values(frame: Any, label: str | None) -> dict[str, float | None]:
    if label is None or frame is None:
        return {}
    try:
        row = frame.loc[label]
    except KeyError:
        return {}
    out: dict[str, float | None] = {}
    for col, val in row.items():
        try:
            col_str = col.strftime("%Y-%m-%d") if hasattr(col, "strftime") else str(col)
        except Exception:  # noqa: BLE001
            col_str = str(col)
        out[col_str] = as_float(val)
    return out


def yfinance_fundamentals_history(ticker: str) -> dict:
    if direct_disabled():
        return {"status": "network_blocked", "source": "yfinance", "provider": "none"}
    try:
        import yfinance as yf  # type: ignore
    except ImportError:
        return {"status": "missing_dependency", "source": "yfinance", "provider": "none"}

    try:
        t = yf.Ticker(ticker)
        income = getattr(t, "quarterly_income_stmt", None)
        if income is None or income.empty:
            income = getattr(t, "quarterly_financials", None)
        balance = getattr(t, "quarterly_balance_sheet", None)
        cashflow = getattr(t, "quarterly_cashflow", None)
        # dividends as a Series indexed by date
        dividends_series = t.dividends if hasattr(t, "dividends") else None
    except Exception as exc:  # noqa: BLE001
        return {"status": "error", "error": type(exc).__name__, "source": "yfinance", "provider": "none"}

    if income is None or income.empty or balance is None or balance.empty:
        return {"status": "no_data", "source": "yfinance", "provider": "none"}

    income_labels = list(income.index)
    balance_labels = list(balance.index)
    cashflow_labels = list(cashflow.index) if cashflow is not None and not cashflow.empty else []

    # Look up the standard labels (yfinance label names shift between versions).
    eps_row    = _row_values(income, _pick(income_labels, ["Diluted EPS", "Basic EPS", "EPS"]))
    rev_row    = _row_values(income, _pick(income_labels, ["Total Revenue", "Revenue", "Operating Revenue"]))
    ni_row     = _row_values(income, _pick(income_labels, ["Net Income", "Net Income Common Stockholders", "Net Income From Continuing Operations"]))
    ocf_row    = _row_values(cashflow, _pick(cashflow_labels, ["Operating Cash Flow", "Total Cash From Operating Activities", "Cash Flow From Continuing Operating Activities"]))
    capex_row  = _row_values(cashflow, _pick(cashflow_labels, ["Capital Expenditure", "Capital Expenditures"]))
    debt_row   = _row_values(balance, _pick(balance_labels, ["Total Debt", "Long Term Debt"]))
    eq_row     = _row_values(balance, _pick(balance_labels, ["Total Equity Gross Minority Interest", "Stockholders Equity", "Total Stockholder Equity", "Common Stock Equity"]))
    ca_row     = _row_values(balance, _pick(balance_labels, ["Current Assets", "Total Current Assets"]))
    cl_row     = _row_values(balance, _pick(balance_labels, ["Current Liabilities", "Total Current Liabilities"]))
    shares_row = _row_values(balance, _pick(balance_labels, ["Share Issued", "Ordinary Shares Number", "Common Stock"]))

    # Build a unified set of quarter-end dates (intersection of available columns).
    all_dates: set[str] = set()
    for row in (eps_row, rev_row, ni_row, ocf_row, capex_row, debt_row, eq_row, ca_row, cl_row, shares_row):
        all_dates.update(row.keys())
    ordered_dates = sorted(all_dates)

    # Build quarterly dividend totals from the dividends series.
    dividend_quarter_totals: dict[str, float] = {}
    if dividends_series is not None and not dividends_series.empty:
        for ts, val in dividends_series.items():
            try:
                date_str = ts.strftime("%Y-%m-%d")
            except Exception:  # noqa: BLE001
                date_str = str(ts)[:10]
            # bucket to the nearest reported quarter-end date
            nearest = None
            best_diff = None
            for q_end in ordered_dates:
                diff = abs((datetime.strptime(q_end, "%Y-%m-%d") - datetime.strptime(date_str, "%Y-%m-%d")).days)
                if best_diff is None or diff < best_diff:
                    best_diff = diff
                    nearest = q_end
            if nearest is not None and best_diff is not None and best_diff <= 95:
                dividend_quarter_totals[nearest] = dividend_quarter_totals.get(nearest, 0.0) + float(val)

    quarters: list[dict] = []
    missing_fields: set[str] = set()
    for period_end_str in ordered_dates:
        try:
            period_end_dt = datetime.strptime(period_end_str, "%Y-%m-%d")
        except ValueError:
            continue
        # Embargo proxy: filing date = period end + 60 calendar days.
        as_of_dt = period_end_dt + timedelta(days=60)
        eps        = eps_row.get(period_end_str)
        revenue    = rev_row.get(period_end_str)
        net_income = ni_row.get(period_end_str)
        ocf        = ocf_row.get(period_end_str)
        capex      = capex_row.get(period_end_str)
        # CapEx is reported as a negative cash flow; FCF = OCF - |CapEx|.
        fcf = None
        if ocf is not None and capex is not None:
            fcf = ocf - abs(capex)
        debt    = debt_row.get(period_end_str)
        equity  = eq_row.get(period_end_str)
        ca      = ca_row.get(period_end_str)
        cl      = cl_row.get(period_end_str)
        shares  = shares_row.get(period_end_str)
        dps     = dividend_quarter_totals.get(period_end_str)

        for fname, val in [("eps_diluted", eps), ("revenue", revenue), ("fcf", fcf),
                            ("total_debt", debt), ("total_equity", equity),
                            ("current_assets", ca), ("current_liabilities", cl),
                            ("shares_diluted", shares), ("dividend_per_share", dps)]:
            if val is None:
                missing_fields.add(fname)

        quarters.append({
            "period_end_date": period_end_str,
            "as_of_date": as_of_dt.strftime("%Y-%m-%d"),
            "eps_diluted": eps,
            "revenue": revenue,
            "net_income": net_income,
            "fcf": fcf,
            "total_debt": debt,
            "total_equity": equity,
            "current_assets": ca,
            "current_liabilities": cl,
            "shares_diluted": shares,
            "dividend_per_share": dps,
        })

    if not quarters:
        return {"status": "no_data", "source": "yfinance", "provider": "none"}

    return {
        "status": "ok",
        "source": "yfinance",
        "provider": "yfinance",
        "ticker": ticker.upper(),
        "quarters": quarters,
        "missing_fields": sorted(missing_fields),
        "embargo_days": 60,
        "embargo_note": "Period-end + 60 calendar days used as filing-date proxy; yfinance does not expose the true 10-Q filing date.",
        "data_quality": "good" if not missing_fields else "partial",
    }


def get_prefetched_fundamentals(ticker: str) -> dict:
    data = read_prefetched_json(ticker, "fundamentals")
    if data is None:
        return {"status": "missing_prefetch", "source": "none", "provider": "none"}
    if not isinstance(data, dict) or "quarters" not in data:
        return {"status": "invalid_prefetch", "source": "prefetched_web", "provider": "prefetched_web"}
    out = dict(data)
    out.setdefault("status", "ok")
    out.setdefault("source", "prefetched_web")
    out.setdefault("provider", "prefetched_web")
    out.setdefault("embargo_days", 60)
    out.setdefault("embargo_note", "Period-end + 60 calendar days used as filing-date proxy.")
    out.setdefault("data_quality", "partial")
    return out


def get_fundamentals_history(ticker: str, keys: dict[str, str]) -> dict:
    """Return quarterly fundamentals time series for persona-mode backtests.

    Provider order: yfinance (primary v1) → prefetched_web JSON. Finnhub
    /stock/financials-reported parsing is deferred to v2 because XBRL concept
    mapping is non-trivial. Schema is documented in BACKTEST_DESIGN.md §1.
    """
    attempts: list[dict] = []

    yf_fund = yfinance_fundamentals_history(ticker)
    if yf_fund.get("status") == "ok":
        return yf_fund
    attempts.append({"source": "yfinance", "status": yf_fund.get("status"), "notice": yf_fund.get("error")})

    prefetched = get_prefetched_fundamentals(ticker)
    if prefetched.get("status") == "ok":
        prefetched["fallback_from"] = attempts
        return prefetched
    attempts.append({"source": "prefetched_web", "status": prefetched.get("status")})

    # Reserved for v2: Finnhub financials-reported parsing using keys.get("FINNHUB_API_KEY").
    _ = keys  # silence unused-arg lint while the v2 path is pending.

    return {
        "status": "all_providers_failed",
        "source": "none",
        "provider": "none",
        "data_quality": "unavailable",
        "fallback_from": attempts,
        "missing_fields": ["eps_diluted", "revenue", "fcf", "total_debt", "total_equity",
                            "current_assets", "current_liabilities", "shares_diluted",
                            "dividend_per_share"],
    }
