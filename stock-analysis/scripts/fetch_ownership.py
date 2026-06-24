#!/usr/bin/env python3
"""Fetch ownership / shareholder structure for a ticker.

No API key required. Uses scripts/data_provider.py (yfinance primary, prefetched
fallback). Writes {TICKER}_ownership_bundle.json. Never prints API keys.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from data_provider import ensure_yfinance, get_ownership, get_output_dir, load_keys


def summarize_ownership(raw: dict) -> dict:
    """Pure transform of a get_ownership() result into report fields."""
    inst = raw.get("pct_held_institutions")
    insiders = raw.get("pct_held_insiders")
    retail = None
    if inst is not None and insiders is not None:
        retail = max(0.0, 1.0 - inst - insiders)
    holders = raw.get("institutional_holders") or []
    ranked = sorted(
        (h for h in holders if h.get("pct_out") is not None),
        key=lambda h: h["pct_out"],
        reverse=True,
    )
    top10 = ranked[:10]
    top10_pct = sum(h["pct_out"] for h in top10) if top10 else None
    return {
        "pct_held_institutions": inst,
        "pct_held_insiders": insiders,
        "pct_held_retail": retail,
        "top10_institutional": top10,
        "top10_concentration_pct": top10_pct,
        "float_shares": raw.get("float_shares"),
        "shares_outstanding": raw.get("shares_outstanding"),
        "short_pct_float": raw.get("short_pct_float"),
        "short_ratio_days_to_cover": raw.get("short_ratio"),
        "shares_short": raw.get("shares_short"),
        "shares_short_prior": raw.get("shares_short_prior"),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Fetch ownership structure for a ticker.")
    parser.add_argument("ticker")
    parser.add_argument("--key-file", default=None)
    parser.add_argument("--output-dir", default=None)
    args = parser.parse_args()

    ensure_yfinance()
    keys = load_keys(args.key_file)
    raw = get_ownership(args.ticker, keys)

    bundle = {
        "ticker": args.ticker.upper(),
        "status": raw.get("status"),
        "provider": raw.get("provider"),
        "source": raw.get("source"),
        "as_of": raw.get("timestamp_utc"),
        "fund_holders": raw.get("fund_holders", []),
        "notes": [
            "Percentages are fractions (0-1) as reported by the source; verify units before display.",
            "Dual-class / voting structure and quarterly 13F deltas are NOT in this bundle — fill via web search (recency-gated).",
        ],
    }
    if raw.get("status") == "ok":
        bundle.update(summarize_ownership(raw))

    out_dir = Path(args.output_dir) if args.output_dir and args.output_dir != "auto" else get_output_dir()
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{args.ticker.upper()}_ownership_bundle.json"
    out_path.write_text(json.dumps(bundle, indent=2), encoding="utf-8")
    print(f"[ownership] wrote {out_path} (status={bundle['status']})")


if __name__ == "__main__":
    main()
