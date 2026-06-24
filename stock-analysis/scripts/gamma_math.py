#!/usr/bin/env python3
"""Pure options dealer-gamma math (stdlib only). No network, no data deps.

Dealer-sign convention: dealers are long call gamma, short put gamma (the
standard naive GEX assumption). Net GEX > 0 => positive-gamma regime
(vol suppression / mean reversion); < 0 => negative-gamma (vol amplification).
"""

from __future__ import annotations

import math

_NORM_PDF = 1.0 / math.sqrt(2.0 * math.pi)


def bs_gamma(spot: float, strike: float, t_years: float, iv: float, r: float = 0.045) -> float:
    """Black-Scholes gamma. Returns 0.0 for degenerate inputs."""
    if not spot or not strike or spot <= 0 or strike <= 0:
        return 0.0
    if t_years is None or t_years <= 0 or iv is None or iv <= 0:
        return 0.0
    v_sqrt = iv * math.sqrt(t_years)
    d1 = (math.log(spot / strike) + (r + 0.5 * iv * iv) * t_years) / v_sqrt
    pdf = _NORM_PDF * math.exp(-0.5 * d1 * d1)
    return pdf / (spot * v_sqrt)


def contract_gex(spot, strike, t_years, iv, oi, kind, r=0.045) -> float:
    """Signed dollar gamma exposure for one contract per 1% move (dealer convention)."""
    g = bs_gamma(spot, strike, t_years, iv, r)
    sign = 1.0 if kind == "call" else -1.0
    return sign * g * (oi or 0.0) * 100.0 * spot * spot * 0.01


def net_gex_at(spot, contracts, r=0.045) -> float:
    """Sum signed contract GEX across the chain at a hypothetical spot."""
    return sum(
        (contract_gex(spot, c["strike"], c["t_years"], c["iv"], c.get("oi", 0.0), c["kind"], r) for c in contracts),
        0.0,
    )


def find_gamma_flip(contracts, lo, hi, r=0.045, steps=200):
    """Spot where net GEX crosses zero, scanning [lo, hi]. None if no crossing."""
    if hi <= lo:
        return None
    prev_s = lo
    prev_g = net_gex_at(lo, contracts, r)
    for i in range(1, steps + 1):
        s = lo + (hi - lo) * i / steps
        g = net_gex_at(s, contracts, r)
        if prev_g == 0.0:
            return prev_s
        if (prev_g < 0.0) != (g < 0.0):
            if g == prev_g:
                return s
            return prev_s + (s - prev_s) * (0.0 - prev_g) / (g - prev_g)
        prev_s, prev_g = s, g
    return None


def gamma_wall(contracts, kind, spot, r=0.045):
    """Strike with the largest gamma*OI for the given kind. None if none."""
    best_k = None
    best_v = -1.0
    for c in contracts:
        if c["kind"] != kind:
            continue
        v = bs_gamma(spot, c["strike"], c["t_years"], c["iv"], r) * (c.get("oi", 0.0) or 0.0)
        if v > best_v:
            best_v, best_k = v, c["strike"]
    return best_k


def max_pain(calls_oi: dict, puts_oi: dict):
    """Strike minimizing total option-holder payout at expiry. None if empty."""
    strikes = sorted(set(list(calls_oi) + list(puts_oi)))
    if not strikes:
        return None
    best_k = None
    best_v = None
    for p in strikes:
        payout = 0.0
        for k, oi in calls_oi.items():
            payout += max(p - k, 0.0) * (oi or 0.0)
        for k, oi in puts_oi.items():
            payout += max(k - p, 0.0) * (oi or 0.0)
        if best_v is None or payout < best_v:
            best_v, best_k = payout, p
    return best_k
