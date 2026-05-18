# Web Prefetch Helper

Use this helper when `data_provider.py` reports direct API failures in Claude.ai web sandbox, such as `network_blocked`, `missing_key`, or `all_providers_failed`.

## Goal

Claude should use web search / web fetch to collect market data, write JSON files to `PREFETCH_DIR`, then re-run `fetch_price_charts.py`. The default directory is:

```text
/tmp/prefetched_data
```

You may override it:

```bash
export PREFETCH_DIR=/tmp/prefetched_data
```

## Files To Write

Use uppercase tickers in filenames:

```text
/tmp/prefetched_data/{TICKER}_quote.json
/tmp/prefetched_data/{TICKER}_daily.json
/tmp/prefetched_data/{TICKER}_weekly.json
/tmp/prefetched_data/{TICKER}_intraday.json
```

## Quote Schema

```json
{
  "c": 84.62,
  "h": 84.75,
  "l": 83.57,
  "o": 84.10,
  "pc": 84.30,
  "52w_high": 84.75,
  "52w_low": 51.66,
  "date": "2026-05-07",
  "source_url": "https://stockanalysis.com/stocks/example/",
  "source_name": "StockAnalysis"
}
```

## OHLCV Schema

Daily, weekly, and intraday files must be JSON arrays, or an object with a `rows` array:

```json
[
  {
    "date": "2026-05-07",
    "open": 84.10,
    "high": 84.75,
    "low": 83.57,
    "close": 84.62,
    "volume": 12345678
  }
]
```

Intraday rows should include ISO timestamps when possible:

```json
[
  {
    "date": "2026-05-07T20:00:00+00:00",
    "timestamp_utc": "2026-05-07T20:00:00+00:00",
    "open": 84.10,
    "high": 84.20,
    "low": 84.00,
    "close": 84.15,
    "volume": 12000
  }
]
```

## Suggested Web Sources

- Quote and statistics: `stockanalysis.com/stocks/{ticker}/`
- ETF quote and statistics: `stockanalysis.com/etf/{ticker}/`
- Price history: Yahoo Finance historical pages, Nasdaq, MarketWatch, Investing.com, or other reputable sources available through web tools
- Filings and earnings: SEC, company investor relations, Nasdaq earnings calendar

## Re-run

After writing the JSON files, run:

```bash
python stock-analysis/scripts/fetch_price_charts.py TICKER \
  --output-dir auto \
  --intraday-window 1d \
  --intraday-resolution 5
```

The script will mark prefetched data as `provider=prefetched_web`. The final report must disclose that this is a secondary web-sourced fallback and lower confidence for intraday precision.
