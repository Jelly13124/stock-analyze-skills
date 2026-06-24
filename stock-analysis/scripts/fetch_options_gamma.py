#!/usr/bin/env python3
"""Fetch the option chain and compute dealer gamma (GEX), gamma flip, walls, max pain.

No API key required (yfinance primary, prefetched fallback). Writes
{TICKER}_gamma_bundle.json. Dealer-sign convention documented in gamma_math.py.
"""

from __future__ import annotations

import argparse
import json
from datetime import date, datetime
from pathlib import Path

from data_provider import ensure_yfinance, get_option_chain, get_output_dir, get_quote, load_keys
from gamma_math import find_gamma_flip, gamma_wall, max_pain, net_gex_at


def _t_years(expiry: str, today: date) -> float | None:
    try:
        exp = datetime.strptime(expiry[:10], "%Y-%m-%d").date()
    except ValueError:
        return None
    days = (exp - today).days
    return days / 365.0 if days > 0 else None


def build_contracts(chain: dict, today: date) -> list[dict]:
    contracts: list[dict] = []
    for leg in chain.get("chains", []):
        t = _t_years(leg.get("expiry", ""), today)
        if not t:
            continue
        for kind, rows in (("call", leg.get("calls", [])), ("put", leg.get("puts", []))):
            for row in rows:
                iv = row.get("implied_volatility")
                oi = row.get("open_interest") or 0.0
                if iv is None or iv <= 0 or oi <= 0:
                    continue
                contracts.append({"strike": row["strike"], "t_years": t, "iv": iv, "oi": oi, "kind": kind})
    return contracts


def main() -> None:
    parser = argparse.ArgumentParser(description="Compute dealer gamma exposure for a ticker.")
    parser.add_argument("ticker")
    parser.add_argument("--key-file", default=None)
    parser.add_argument("--output-dir", default=None)
    parser.add_argument("--rate", type=float, default=0.045, help="assumed risk-free rate")
    parser.add_argument("--max-expiries", type=int, default=6)
    args = parser.parse_args()

    ensure_yfinance()
    keys = load_keys(args.key_file)
    quote = get_quote(args.ticker, keys)
    spot = quote.get("c")
    chain = get_option_chain(args.ticker, keys)

    out_dir = Path(args.output_dir) if args.output_dir and args.output_dir != "auto" else get_output_dir()
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{args.ticker.upper()}_gamma_bundle.json"

    bundle = {
        "ticker": args.ticker.upper(),
        "spot": spot,
        "provider": chain.get("provider"),
        "source": chain.get("source"),
        "r_assumed": args.rate,
        "dealer_sign_assumption": "long call gamma / short put gamma (naive GEX)",
        "caveats": [
            "Dealer-sign is a heuristic; true dealer positioning is unobservable.",
            "yfinance IV is noisy on illiquid strikes; contracts with OI<=0 or IV<=0 are dropped.",
            "r and calendar-T are approximations; snapshot drifts intraday and around OPEX.",
        ],
    }

    if chain.get("status") != "ok" or spot is None or not chain.get("chains"):
        bundle["status"] = "n/a"
        bundle["reason"] = "no option chain / not optionable / spot unavailable"
        out_path.write_text(json.dumps(bundle, indent=2), encoding="utf-8")
        print(f"[gamma] wrote {out_path} (status=n/a)")
        return

    today = datetime.now().date()
    contracts = build_contracts(chain, today)
    if not contracts:
        bundle["status"] = "n/a"
        bundle["reason"] = "chain too thin after OI/IV filtering"
        out_path.write_text(json.dumps(bundle, indent=2), encoding="utf-8")
        print(f"[gamma] wrote {out_path} (status=n/a)")
        return

    calls_oi: dict = {}
    puts_oi: dict = {}
    for leg in chain["chains"]:
        for row in leg.get("calls", []):
            calls_oi[row["strike"]] = calls_oi.get(row["strike"], 0.0) + (row.get("open_interest") or 0.0)
        for row in leg.get("puts", []):
            puts_oi[row["strike"]] = puts_oi.get(row["strike"], 0.0) + (row.get("open_interest") or 0.0)

    net = net_gex_at(spot, contracts, args.rate)
    flip = find_gamma_flip(contracts, spot * 0.7, spot * 1.3, args.rate, steps=240)
    bundle.update(
        {
            "status": "ok",
            "net_gex": net,
            "regime": "positive" if net >= 0 else "negative",
            "gamma_flip_level": flip,
            "distance_to_flip_pct": ((spot - flip) / spot * 100.0) if flip else None,
            "call_wall_strike": gamma_wall(contracts, "call", spot, args.rate),
            "put_wall_strike": gamma_wall(contracts, "put", spot, args.rate),
            "max_pain_strike": max_pain(calls_oi, puts_oi),
            "expiries_used": chain.get("expiries", []),
            "n_contracts": len(contracts),
        }
    )
    out_path.write_text(json.dumps(bundle, indent=2), encoding="utf-8")
    print(f"[gamma] wrote {out_path} (status=ok, regime={bundle['regime']})")


if __name__ == "__main__":
    main()
