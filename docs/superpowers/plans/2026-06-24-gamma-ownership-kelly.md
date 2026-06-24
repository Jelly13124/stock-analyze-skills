# Dealer Gamma + Ownership Structure + Total-Capital Kelly Sizing — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add an options dealer-gamma module and an ownership-structure module to the `stock-analysis` skill, and change the Request Gate from "budget" to "total investable capital (总仓位)" with Kelly-optimal position sizing.

**Architecture:** The skill is a router (`SKILL.md`) that `Read`s Markdown modules on demand; Python data scripts (`scripts/`) fetch via `data_provider.py` on a `direct API → yfinance → prefetched` chain. This plan adds two new modules + two new fetch scripts (sharing new yfinance helpers in `data_provider.py`), a Kelly section in the risk module, and the cross-file doc/schema updates the CLAUDE.md consistency rule requires. Three independent feature phases (Kelly → Ownership → Gamma) each end working and committed; a final phase reconciles cross-file consistency.

**Tech Stack:** Python 3 (stdlib + lazy-imported `yfinance`, no other deps), Markdown skill modules, a self-contained HTML report template. No test framework in repo — tests are stdlib `unittest`/`assert` scripts in a repo-root `tests/` dir (NOT shipped in the skill ZIP), plus `python -m py_compile` and CLI smoke-tests per CLAUDE.md.

---

## Repo conventions (read before starting)

- **No `git add .`** — stage files explicitly (CLAUDE.md Git rule). End every commit message with:
  `Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>`
- **Do not commit** build artifacts/scratch: `outputs/`, `claude_web_zips/`, `stock-analysis.skill`, `prefetched_data/`.
- **Consistency rule (CLAUDE.md):** Request-Gate / output / scoring / module-count wording lives in several files. When you change one, update all affected: `stock-analysis/SKILL.md`, `references/depth-framework.md`, `references/report-template.md`, `references/report-template.html`, `modules/risk-position.md`, plus `CLAUDE.md`, `README.md`, `README.zh-CN.md`. Keep the two READMEs in sync.
- **Skill ZIP hygiene:** the shipped skill is only the `stock-analysis/` folder. Keep all tests in repo-root `tests/` so `tools/build_claude_zips.ps1` never packages them.
- **Data-provider pattern:** every fetch helper handles `direct_disabled()` → `network_blocked`, `ImportError` → `missing_dependency`, generic `Exception` → `error`; yfinance is imported lazily *inside* the function; a `get_*` wrapper tries yfinance then `read_prefetched_json(ticker, suffix)`.
- **No-key invariant:** scripts must run with no API key (yfinance auto-installed by `ensure_yfinance()`); never require a key.
- **Module count bookkeeping:** current totals are **18 modules = 9 analytical + 1 backtest + 8 personas** (SKILL.md Overview phrasing) which `CLAUDE.md`/`README.md` count as **10 analytical** (backtest folded in). After this plan: **20 modules**, **SKILL.md "11 analytical"**, **CLAUDE.md/README.md "12 analytical"**.

---

## Phase 0 — Branch & test scaffold

### Task 0.1: Create the feature branch and test directory

**Files:**
- Create: `tests/__init__.py` (empty)
- Create: `tests/README.md`

- [ ] **Step 1: Branch off main**

```bash
git checkout main
git pull --ff-only || true
git checkout -b feat/gamma-ownership-kelly
```

- [ ] **Step 2: Create the dev-only test directory**

Create `tests/__init__.py` as an empty file. Create `tests/README.md` with:

```markdown
# Dev tests (not shipped)

Stdlib-only unit tests for the `stock-analysis` data scripts. These live in the repo root
(NOT under `stock-analysis/`) so `tools/build_claude_zips.ps1` never packages them into the
shipped skill. Run them with the system Python:

    python -m unittest discover -s tests -v

No third-party test framework is required.
```

- [ ] **Step 3: Verify the skill ZIP would not include tests**

Run: `python -c "import pathlib; print([p.as_posix() for p in pathlib.Path('tests').glob('*')])"`
Expected: lists `tests/__init__.py` and `tests/README.md` (confirming they're outside `stock-analysis/`).

- [ ] **Step 4: Commit**

```bash
git add tests/__init__.py tests/README.md
git commit -m "chore: add dev-only tests/ scaffold for stock-analysis scripts

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Phase A — Total capital (总仓位) + Kelly sizing

No new data dependency. Smallest blast radius; ship first.

### Task A.1: Rewrite Request Gate item (3a) in SKILL.md

**Files:**
- Modify: `stock-analysis/SKILL.md` (Request Gate combined question + notes + Position & Risk Profile Use)

- [ ] **Step 1: Change the combined-question item (3)**

In `stock-analysis/SKILL.md`, find item `(3) Position & risk` inside the combined question (the fenced block starting `Before I analyze <TICKER>`). Replace its sub-item `(a)`:

Old:
```
(a) budget: a dollar amount or % of portfolio;
```
New:
```
(a) total investable capital (总仓位) — your whole account / investable pot, so I can compute the Kelly-optimal allocation for this name; OR give a fixed dollar amount or % if you'd rather size it yourself, and I'll use that directly;
```

- [ ] **Step 2: Update the one-liner example in the same block**

In the same fenced question, replace the example line:

Old:
```
You can also reply with a one-liner like "standard, target price, $10k, hold at $9.50, OK with a ~15% drawdown" and I'll start straight away.
```
New:
```
You can also reply with a one-liner like "standard, target price, total capital $100k, hold at $9.50, OK with a ~15% drawdown" and I'll start straight away.
```

- [ ] **Step 3: Update the "Item (3) shapes the risk section" note**

Find the bullet beginning `- **Item (3) shapes the risk section.**`. Replace its first sentence:

Old:
```
- **Item (3) shapes the risk section.** Budget → concrete dollar sizing in `risk-position.md`.
```
New:
```
- **Item (3) shapes the risk section.** Total capital → Kelly-optimal allocation (% + dollars) in `risk-position.md`; a user-supplied fixed amount overrides Kelly and sizes to that amount directly.
```

- [ ] **Step 4: Rewrite the "Budget" paragraph under "Position & Risk Profile Use"**

Find the `### Position & Risk Profile Use` section. Replace the `**Budget**` block (from `**Budget** (dollar amount or % of portfolio)` through its bullet list, ending before `**Current holding + cost basis**`) with:

```
**Total capital (总仓位)** — the user's whole investable pot. The risk section computes the **Kelly-optimal allocation** for this name and produces concrete numbers:

- recommended position as **% of total capital and in dollars**, via the Kelly Position Sizing method in `modules/risk-position.md` (fractional Kelly scaled by risk tolerance, then capped by the single-stock and volatility-adjusted caps, floored at 0)
- exact share count or notional at the entry level
- dollar value at each scenario (bear / base / bull), at the stop (max loss in $), and at the target (max gain in $)
- R:R ratio with dollar context
- the full Kelly worktable (f*, fraction k, caps, stop-based size) and which constraint binds

If the user instead gave a **fixed dollar amount or %**, skip Kelly: size to that amount, still warn if it exceeds the single-stock cap.
```

- [ ] **Step 5: Update the skip-fallback line in the same section**

Find the final paragraph of `### Position & Risk Profile Use` beginning `If the user replied \`skip\``. Replace `budget skipped → % terms only, no dollar sizing;` with:
```
total capital skipped → Kelly fraction in % terms only, no dollar sizing;
```

- [ ] **Step 6: Verify wording is internally consistent**

Run: `grep -n "budget" stock-analysis/SKILL.md`
Expected: remaining hits are only the Technical Window / other-gate-triggers mentions ("If the user gives a position budget but no objective…"). Update that one line too — find `- If the user gives a position budget but no objective, still ask the objective` and change `position budget` → `total capital or a fixed amount`.

- [ ] **Step 7: Commit**

```bash
git add stock-analysis/SKILL.md
git commit -m "feat(gate): switch Request Gate item 3a to total capital + Kelly sizing

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

### Task A.2: Add the Kelly Position Sizing section to risk-position.md

**Files:**
- Modify: `stock-analysis/modules/risk-position.md` (Inputs, new Kelly section, Output Contract)

- [ ] **Step 1: Extend Inputs**

In `stock-analysis/modules/risk-position.md`, find the `## Inputs` list. Replace the first bullet:

Old:
```
- Position budget (account size, or a dollar/% allocation) if provided; otherwise use percentage-based sizing only.
```
New:
```
- Total investable capital (总仓位) if provided — drives Kelly Position Sizing below. A user-supplied fixed dollar/% amount overrides Kelly and is used as-is. If neither is given, use percentage-based sizing only.
```

- [ ] **Step 2: Insert the Kelly section after "## Position Sizing"**

Immediately after the `## Position Sizing` section (after the "Tolerable drawdown drives the stop" paragraph, before `## Held-Position Analysis`), insert:

````markdown
## Kelly Position Sizing (Total-Capital Mode)

When the user gives **total investable capital (总仓位)** rather than a fixed amount, compute the
Kelly-optimal allocation for this name from the bear/base/bull scenarios. Kelly answers "what
fraction of capital maximizes long-run growth", which is exactly the total-capital question.

**Inputs:** total capital `C`; entry `E`; stop `S`; scenario targets `T_bear / T_base / T_bull`
with probabilities `p_bear / p_base / p_bull` (sum = 1); risk-tolerance band.

**Method (multi-outcome Kelly over the three scenarios):**

```
r_i      = (T_i − E) / E                            # scenario returns (bear negative)
r_bear   = max((T_bear − E)/E, −|E − S|/E)          # the stop caps the realized downside
f*       = the f in [0,1] maximizing  Σ p_i · ln(1 + f·r_i)   # full Kelly (grid-search f)
                                                    # binary sanity check: f = (p·b − q)/b,
                                                    # p = P(r>0), q = 1−p, b = mean win / |mean loss|
k        = 0.25 conservative | 0.50 balanced | 0.75 aggressive   # fractional Kelly by tolerance
f_kelly  = max(0, k · f*)                           # negative edge → 0 (avoid / short candidate)
f_final  = min(f_kelly, single_stock_cap, vol_adjusted_cap)      # Kelly never exceeds the caps
f_stop   = risk_per_trade ÷ (|E − S| / E)           # the existing stop-based size, as % of capital
position = min(f_final, f_stop) × C                 # most conservative binds; output $ and shares
```

- **Show the worktable**: `f*`, `k`, `f_kelly`, the caps, `f_stop`, and which constraint binds.
- **Held position**: target $ = `position`; delta = target − current value → **add / trim** to reach optimal.
- **`f* ≤ 0`** (negative edge): recommend **no long position**; flag as an avoid / potential short.

**Scenario probabilities.** Prefer the bear/base/bull confidences already set in the report. When
they are not explicit, map from the conviction score:

| Conviction score | (p_bear, p_base, p_bull) |
|---|---|
| 75–100 | 0.15 / 0.45 / 0.40 |
| 65–74  | 0.20 / 0.50 / 0.30 |
| 50–64  | 0.30 / 0.50 / 0.20 |
| <50    | 0.45 / 0.45 / 0.10 |

**Caveats (always disclose):** Kelly is highly sensitive to `p` and `b` estimation error — hence
fractional Kelly, never full. A single analysis gives uncertain estimates. Kelly assumes
repeatable independent bets; for a one-off concentrated position treat the output as an **upper
bound** and lean toward the smaller of the capped Kelly and the stop-based size.
````

- [ ] **Step 3: Update the Output Contract**

In `## Output Contract`, replace the bullet:
```
- position sizing formula or percentage guidance
```
with:
```
- Kelly Position Sizing worktable when total capital was given (f*, fraction k, caps, stop-based size, binding constraint, recommended % + $ + shares); otherwise the position-sizing formula or percentage guidance
```

- [ ] **Step 4: Verify**

Run: `grep -n "Kelly" stock-analysis/modules/risk-position.md`
Expected: the new section heading + the Output Contract bullet appear.

- [ ] **Step 5: Commit**

```bash
git add stock-analysis/modules/risk-position.md
git commit -m "feat(risk): add Kelly Position Sizing (total-capital mode)

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

### Task A.3: Reflect Kelly in the report schema (report-template.md)

**Files:**
- Modify: `stock-analysis/references/report-template.md` (Risk & Position Sizing schema bullets)

- [ ] **Step 1: Add Kelly bullets to the Risk schema**

Find the `## Risk and Position Sizing` block in the Default Report Output Schema. Replace:
```
- Risk style assumption:
- Conservative plan:
- Balanced plan:
- Aggressive plan:
```
with:
```
- Risk style assumption:
- Sizing mode: Kelly (total-capital) or fixed-amount:
- Kelly worktable (f*, fraction k, caps, stop-based size, binding constraint): when total capital given
- Recommended position (% of total capital + $ + shares):
- Conservative plan:
- Balanced plan:
- Aggressive plan:
```

- [ ] **Step 2: Verify and commit**

Run: `grep -n "Kelly worktable" stock-analysis/references/report-template.md`
Expected: one hit.

```bash
git add stock-analysis/references/report-template.md
git commit -m "docs(schema): add Kelly sizing fields to Risk section

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

### Task A.4: Reflect Kelly in the HTML template (report-template.html)

**Files:**
- Modify: `stock-analysis/references/report-template.html` (timestamp label + Risk section block)

- [ ] **Step 1: Update the header timestamp label**

Find `<dt>Position budget:</dt> <dd>{{POSITION_BUDGET_OR_NA}}</dd>` and replace with:
```html
  <dt>Total capital / sizing:</dt> <dd>{{TOTAL_CAPITAL_OR_NA}}</dd>
```

- [ ] **Step 2: Add a Kelly block to the Risk and Position Sizing section**

Find the `<h2>Risk and Position Sizing</h2>` block. Immediately after its closing `</table>` (the one with the Plan/Entry/Stop columns), insert:

```html
<h3>Kelly Position Sizing (total-capital mode)</h3>
<!-- Fill when the user gave total capital (总仓位). If they gave a fixed amount, omit this
     block and size to that amount. -->
<table>
  <thead>
    <tr><th>Input / step</th><th>Value</th></tr>
  </thead>
  <tbody>
    <tr><td>Total capital (C)</td><td class="num"></td></tr>
    <tr><td>Scenario probabilities (bear / base / bull)</td><td></td></tr>
    <tr><td>Full Kelly f*</td><td class="num"></td></tr>
    <tr><td>Fraction k (risk-tolerance)</td><td class="num"></td></tr>
    <tr><td>Caps (single-stock / vol-adjusted)</td><td></td></tr>
    <tr><td>Stop-based size f_stop</td><td class="num"></td></tr>
    <tr><td><strong>Recommended position (% / $ / shares)</strong></td><td></td></tr>
    <tr><td>Binding constraint</td><td></td></tr>
  </tbody>
</table>
```

- [ ] **Step 3: Verify and commit**

Run: `grep -n "Kelly Position Sizing" stock-analysis/references/report-template.html`
Expected: one hit.

```bash
git add stock-analysis/references/report-template.html
git commit -m "docs(html): add Kelly sizing block + total-capital label

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

### Task A.5: Sync CLAUDE.md + READMEs for the gate change

**Files:**
- Modify: `CLAUDE.md` (Request Gate invariant)
- Modify: `README.md` (Report Depth paragraph)
- Modify: `README.zh-CN.md` (mirror)

- [ ] **Step 1: CLAUDE.md invariant**

Find the `- **Request Gate**` invariant bullet. Replace `(3) position & risk profile — budget / current holding + cost basis / risk tolerance` with:
```
(3) position & risk profile — total capital (总仓位, → Kelly-optimal sizing) or a fixed amount / current holding + cost basis / risk tolerance
```

- [ ] **Step 2: README.md Report Depth paragraph**

Find `If the user enters a bare ticker, the main skill asks for depth, objective, position budget, and` and replace `position budget` with `total capital (for Kelly-optimal sizing) or a fixed amount`.

- [ ] **Step 3: README.zh-CN.md mirror**

Open `README.zh-CN.md`, find the equivalent Report Depth / bare-ticker sentence (the Chinese mirror of Step 2) and update it to say 总仓位（用于凯利最优配比）或固定金额 in place of the budget wording. Keep parallel to README.md.

- [ ] **Step 4: Verify and commit**

Run: `grep -rn "position budget" CLAUDE.md README.md README.zh-CN.md`
Expected: no hits (all converted).

```bash
git add CLAUDE.md README.md README.zh-CN.md
git commit -m "docs: sync gate wording to total-capital + Kelly

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Phase B — Ownership-Structure module

> Phases are sequential (A→B→C→D). Module-count steps below assume Phase A is done.

### Task B.1: Add ownership fetch helpers to data_provider.py

**Files:**
- Modify: `stock-analysis/scripts/data_provider.py` (add `_holder_rows`, `yfinance_ownership`, `get_ownership`)

- [ ] **Step 1: Add the yfinance ownership helpers**

In `stock-analysis/scripts/data_provider.py`, immediately after the `yfinance_history` function definition, add:

```python
def _holder_rows(frame: Any) -> list[dict]:
    rows: list[dict] = []
    if frame is None:
        return rows
    try:
        for _, row in frame.iterrows():
            rows.append(
                {
                    "holder": str(row.get("Holder") or row.get("holder") or ""),
                    "shares": as_float(row.get("Shares") or row.get("shares")),
                    "pct_out": as_float(row.get("pctHeld") or row.get("% Out") or row.get("pctOut")),
                    "date_reported": str(row.get("Date Reported") or row.get("dateReported") or ""),
                }
            )
    except Exception:  # noqa: BLE001
        return rows
    return rows


def yfinance_ownership(ticker: str) -> dict:
    if direct_disabled():
        return {"status": "network_blocked", "source": "yfinance", "provider": "none"}
    try:
        import yfinance as yf  # type: ignore

        tk = yf.Ticker(ticker)
        try:
            info = tk.get_info() or {}
        except Exception:  # noqa: BLE001
            info = {}
        return {
            "status": "ok",
            "source": "yfinance",
            "provider": "yfinance",
            "shares_outstanding": as_float(info.get("sharesOutstanding")),
            "float_shares": as_float(info.get("floatShares")),
            "pct_held_insiders": as_float(info.get("heldPercentInsiders")),
            "pct_held_institutions": as_float(info.get("heldPercentInstitutions")),
            "shares_short": as_float(info.get("sharesShort")),
            "shares_short_prior": as_float(info.get("sharesShortPriorMonth")),
            "short_pct_float": as_float(info.get("shortPercentOfFloat")),
            "short_ratio": as_float(info.get("shortRatio")),
            "institutional_holders": _holder_rows(getattr(tk, "institutional_holders", None)),
            "fund_holders": _holder_rows(getattr(tk, "mutualfund_holders", None)),
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        }
    except ImportError:
        return {"status": "missing_dependency", "source": "yfinance", "provider": "none"}
    except Exception as exc:  # noqa: BLE001
        return {"status": "error", "error": type(exc).__name__, "source": "yfinance", "provider": "none"}
```

- [ ] **Step 2: Add the `get_ownership` wrapper**

Immediately after the `get_quote` function definition, add:

```python
def get_ownership(ticker: str, keys: dict[str, str] | None = None) -> dict:
    yf_own = yfinance_ownership(ticker)
    if yf_own.get("status") == "ok":
        return yf_own
    prefetched = read_prefetched_json(ticker, "ownership")
    if isinstance(prefetched, dict):
        prefetched.setdefault("status", "ok")
        prefetched.setdefault("provider", "prefetched_web")
        prefetched.setdefault("source", "prefetched_web")
        return prefetched
    return yf_own
```

- [ ] **Step 3: Syntax-check**

Run: `python -m py_compile stock-analysis/scripts/data_provider.py`
Expected: no output (success).

- [ ] **Step 4: Commit**

```bash
git add stock-analysis/scripts/data_provider.py
git commit -m "feat(data): add yfinance ownership/holders fetch helpers

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

### Task B.2: Create fetch_ownership.py

**Files:**
- Create: `stock-analysis/scripts/fetch_ownership.py`

- [ ] **Step 1: Write the script**

Create `stock-analysis/scripts/fetch_ownership.py` with:

```python
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
```

- [ ] **Step 2: Syntax-check**

Run: `python -m py_compile stock-analysis/scripts/fetch_ownership.py`
Expected: no output (success).

- [ ] **Step 3: Commit**

```bash
git add stock-analysis/scripts/fetch_ownership.py
git commit -m "feat(scripts): add fetch_ownership.py

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

### Task B.3: Unit-test summarize_ownership

**Files:**
- Create: `tests/test_ownership.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_ownership.py` with:

```python
import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "stock-analysis" / "scripts"))

from fetch_ownership import summarize_ownership  # noqa: E402


class TestSummarizeOwnership(unittest.TestCase):
    def test_retail_residual(self):
        out = summarize_ownership({"pct_held_institutions": 0.70, "pct_held_insiders": 0.10})
        self.assertAlmostEqual(out["pct_held_retail"], 0.20, places=6)

    def test_retail_floored_at_zero(self):
        out = summarize_ownership({"pct_held_institutions": 0.95, "pct_held_insiders": 0.10})
        self.assertEqual(out["pct_held_retail"], 0.0)

    def test_retail_none_when_missing(self):
        out = summarize_ownership({"pct_held_institutions": None, "pct_held_insiders": 0.10})
        self.assertIsNone(out["pct_held_retail"])

    def test_top10_concentration_sums_pct_out(self):
        raw = {"institutional_holders": [{"pct_out": 0.05}, {"pct_out": 0.03}, {"pct_out": None}]}
        out = summarize_ownership(raw)
        self.assertAlmostEqual(out["top10_concentration_pct"], 0.08, places=6)

    def test_top10_caps_at_ten(self):
        raw = {"institutional_holders": [{"pct_out": 0.01} for _ in range(15)]}
        out = summarize_ownership(raw)
        self.assertEqual(len(out["top10_institutional"]), 10)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run it (passes immediately — `summarize_ownership` already exists)**

Run: `python -m unittest tests.test_ownership -v`
Expected: 5 tests, all PASS. (Because Task B.2 already created the function; this test locks its behavior.)

- [ ] **Step 3: Commit**

```bash
git add tests/test_ownership.py
git commit -m "test: lock summarize_ownership residual + concentration logic

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

### Task B.4: Create the ownership-structure module

**Files:**
- Create: `stock-analysis/modules/ownership-structure.md`

- [ ] **Step 1: Write the module**

Create `stock-analysis/modules/ownership-structure.md` with:

````markdown
# Ownership & Shareholder Structure Module

> Internal module of the orchestrator. Loaded on demand when the report needs
> this section, or when the user invokes it directly. New in 2026-06.

## Overview

Map **who owns the stock and how control is distributed** — the structural counterpart to the
*flow* signals in `modules/sentiment.md`. Ownership structure drives squeeze/liquidity risk
(float, short interest) and governance quality (insider alignment, voting control), feeding both
`modules/risk-position.md` and `modules/company-fundamentals.md`.

**Boundary with `sentiment.md` (do not duplicate):** ownership = *structure / stock* (who holds
it, how much float, who controls votes). sentiment = *flow / signal* (Form-4 buys/sells as a
bull/bear signal; short-interest *change* as a squeeze signal). Short interest appears in both:
**this module owns the structural float / short % of float**; sentiment owns the **change and
signal**. Cross-reference, never restate.

## Data

Run `scripts/fetch_ownership.py <TICKER> --output-dir <out>` (no key needed; yfinance primary,
prefetched fallback). It writes `{TICKER}_ownership_bundle.json` with institutional / insider /
retail %, float vs. shares outstanding, top-10 institutional holders + concentration, short % of
float, days-to-cover. **Share classes / voting control and quarterly 13F deltas are not in the
bundle** — fill them via web search, recency-gated, and label them web-sourced.

## Standalone Markdown Report Mode

When called directly, produce a self-contained Markdown report in the user's language. Structure:

1. `## Ownership Verdict`
2. `## Ownership Composition` (institutional / insider / retail %, float vs. shares out)
3. `## Holder Concentration` (top-10 holders, single-holder dominance)
4. `## Share Classes & Voting Control` (dual-class, super-voting, founder control — governance)
5. `## Short Structure` (short % of float, days-to-cover — structural; cross-ref Sentiment)
6. `## Recent Ownership Changes` (notable 13F adds/trims, insider roster — web, dated)
7. `## Implication For Risk And Fundamentals`

## Interpretation

| Signal | Reading |
|---|---|
| High institutional % rising | Sponsorship/validation; but crowded, higher de-rating risk on misses |
| High insider % (founder-held) | Skin in the game; but watch governance/control concentration |
| Low float + high short % of float | Squeeze + liquidity risk → tighten long-stop logic, **lower the vol-adjusted single-stock cap** |
| Dual-class / super-voting | Common holders have limited control → governance discount; flag as thesis breaker if egregious |
| Top-1 holder dominance | Key-holder / overhang risk (lockups, forced selling) |

## Data Failure and Low-Confidence Rules

- If holder fields are missing for a small cap, report what exists and mark the rest unavailable.
- 13F snapshots lag (quarterly); state the report date and label as lagging.
- Voting structure is web-sourced — apply the recency gate and cite the filing.
- Verify percentage units (fraction vs. %) before display.

## Output Contract

Return a Markdown report or section with: one-sentence ownership verdict; composition table
(institutional / insider / retail %, float vs. shares out); top-10 concentration; share-class /
voting note; structural short % of float + days-to-cover (cross-ref Sentiment for the signal);
recent dated ownership changes; implication for **risk** (squeeze / liquidity → sizing caps) and
**fundamentals** (governance / alignment / thesis breakers); data gaps and source dates;
standalone disclaimer when called directly: `Not investment advice -- for your own research.`

## Depth gating

`standard` + `full SOP` include this section. `basic` includes it only when ownership materially
drives the thesis (e.g., a low-float / high-short name).
````

- [ ] **Step 2: Verify and commit**

Run: `grep -n "Ownership Verdict" stock-analysis/modules/ownership-structure.md`
Expected: one hit.

```bash
git add stock-analysis/modules/ownership-structure.md
git commit -m "feat(module): add ownership-structure module

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

### Task B.5: Wire the ownership module into SKILL.md

**Files:**
- Modify: `stock-analysis/SKILL.md` (Overview count, Module Routing, Workflow, Output Rules QA, description)

- [ ] **Step 1: Overview module count**

Find in `## Overview`: `It contains 18 internal modules under \`modules/\` (9 analytical + 8 investor personas + 1 backtest).` Replace `18 internal modules` → `19 internal modules` and `9 analytical` → `10 analytical`.

- [ ] **Step 2: Module Routing table row**

In `### Analytical modules`, add a row after the `modules/sentiment.md` row:
```
| Ownership structure: float, institutional / insider %, top holders, share classes, short float | `modules/ownership-structure.md` | standard, full SOP |
```

- [ ] **Step 3: Workflow module defaults (step 5)**

In Workflow step 5, find the `standard` default list (`- \`standard\` — add ...`) and append `, \`modules/ownership-structure.md\`` to it. The `full SOP` line says "all of the above" so it inherits automatically.

- [ ] **Step 4: Output Rules QA expected-sections**

In `## Output Rules`, find the `full SOP` QA gate sentence listing expected sections (`Expected sections: Data Health, Executive Summary, ... fundamentals, financials,`). Insert `ownership structure,` immediately after `fundamentals,`.

- [ ] **Step 5: description keyword**

In the YAML frontmatter `description:`, add `ownership structure / float / short interest,` after `sentiment,`.

- [ ] **Step 6: Verify and commit**

Run: `grep -n "ownership-structure" stock-analysis/SKILL.md`
Expected: routing row + workflow line hits.

```bash
git add stock-analysis/SKILL.md
git commit -m "feat(skill): route ownership-structure module (standard/full SOP)

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

### Task B.6: Add the ownership section to the report schema + HTML

**Files:**
- Modify: `stock-analysis/references/report-template.md`
- Modify: `stock-analysis/references/report-template.html`

- [ ] **Step 1: Schema section (report-template.md)**

In the Default Report Output Schema, immediately after the `## Company Fundamentals` block (before `## Financial Statement Review`), insert:
```
## Ownership & Shareholder Structure
- Ownership composition (institutional % / insider % / retail residual):
- Float vs. shares outstanding; free float:
- Top-10 holders and concentration:
- Share classes and voting control (governance flag):
- Short interest as % of float; days-to-cover (structural; cross-ref Sentiment for the change/signal):
- Recent 13F / insider ownership changes (dated, web-sourced):
- Implication for risk (squeeze / liquidity → sizing caps) and fundamentals (governance / alignment):
```

- [ ] **Step 2: Section Length Budget row (report-template.md)**

In the `### full SOP` Section Length Budget table, add a row after the `Company Fundamentals` row:
```
| Ownership & Shareholder Structure | 200–350 + table | float / holders / short structure; cross-ref Sentiment for flow |
```

- [ ] **Step 3: Full SOP Minimum Gate (report-template.md)**

In `## Full SOP Minimum Gate`, add a bullet:
```
- Ownership & Shareholder Structure covers float, institutional/insider %, top-holder concentration, share-class/voting, and structural short % of float (or `n/a — <reason>`).
```

- [ ] **Step 4: HTML section (report-template.html)**

In `references/report-template.html`, after the `<h2>Company Fundamentals</h2>\n<p></p>` block (before `<h2>Financial Statement Review</h2>`), insert:
```html
<h2>Ownership &amp; Shareholder Structure</h2>
<table>
  <thead><tr><th>Metric</th><th>Value</th><th>As of</th></tr></thead>
  <tbody>
    <tr><td>Institutional / insider / retail %</td><td></td><td></td></tr>
    <tr><td>Float / shares outstanding</td><td class="num"></td><td></td></tr>
    <tr><td>Top-10 concentration</td><td class="num"></td><td></td></tr>
    <tr><td>Share classes / voting control</td><td></td><td></td></tr>
    <tr><td>Short % of float / days-to-cover</td><td class="num"></td><td></td></tr>
  </tbody>
</table>
<p><strong>Read (risk + governance):</strong> </p>
```

- [ ] **Step 5: Verify and commit**

Run: `grep -n "Ownership" stock-analysis/references/report-template.md stock-analysis/references/report-template.html`
Expected: hits in both files.

```bash
git add stock-analysis/references/report-template.md stock-analysis/references/report-template.html
git commit -m "docs(schema+html): add Ownership & Shareholder Structure section

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

### Task B.7: Cross-reference notes in sentiment.md + company-fundamentals.md + depth-framework.md

**Files:**
- Modify: `stock-analysis/modules/sentiment.md`
- Modify: `stock-analysis/modules/company-fundamentals.md`
- Modify: `stock-analysis/references/depth-framework.md`

- [ ] **Step 1: sentiment.md boundary note**

In `stock-analysis/modules/sentiment.md` `## Overview`, after the sentence ending `...short interest / options positioning.`, add:
```
Structural ownership (float, short % of float, institutional/insider %, voting control) lives in `modules/ownership-structure.md`; this module covers the *change* and squeeze *signal*, not the static structure.
```

- [ ] **Step 2: company-fundamentals.md pointer**

In `stock-analysis/modules/company-fundamentals.md`, in the `## Required Output Elements` full-SOP list, replace the bullet `- management, ownership, and capital allocation` with:
```
- management, ownership, and capital allocation (structural ownership detail — float, institutional/insider %, top holders, voting control — lives in `modules/ownership-structure.md`)
```

- [ ] **Step 3: depth-framework.md modules columns**

In `references/depth-framework.md` table, add `, ownership structure` to the `standard` row's Modules cell and (since `full` says "all modules") leave `full` as-is.

- [ ] **Step 4: Verify and commit**

Run: `grep -rn "ownership-structure" stock-analysis/modules/sentiment.md stock-analysis/modules/company-fundamentals.md`
Expected: one hit each.

```bash
git add stock-analysis/modules/sentiment.md stock-analysis/modules/company-fundamentals.md stock-analysis/references/depth-framework.md
git commit -m "docs: cross-reference ownership-structure from sentiment/fundamentals/depth

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

### Task B.8: Sync CLAUDE.md + READMEs for the ownership module

**Files:**
- Modify: `CLAUDE.md`
- Modify: `README.md`
- Modify: `README.zh-CN.md`

- [ ] **Step 1: CLAUDE.md**

In `CLAUDE.md`: (a) update **both** `10 analytical` occurrences → `11 analytical` (the top layout block comment `modules/ # 10 analytical modules + investors/` AND the Architecture "Modules" bullet) and add `ownership-structure` to the parenthesized module list in the Architecture bullet. (b) In the Consistency rule file list, add `modules/ownership-structure.md`.

- [ ] **Step 2: README.md**

In `README.md`: (a) badge line — `18%20modules` → `19%20modules`. (b) "Module Map" intro — `18 internal modules` → `19`. (c) heading `### Analytical modules (10)` → `(11)` and add a table row:
```
| `modules/ownership-structure.md` | Float, institutional / insider %, top holders, share classes, voting control, structural short interest. |
```
(d) Claude Desktop line — `All 18 modules` → `All 19 modules`. (e) Repository Layout tree — add `│   │   ├── ownership-structure.md` near the other module entries. (f) Add a `## What's New` bullet:
```
- **Ownership & Shareholder Structure module** — float, institutional/insider %, top-holder concentration, share-class/voting control, and structural short interest, feeding risk sizing and governance.
```

- [ ] **Step 3: README.zh-CN.md mirror**

Apply the same six edits to `README.zh-CN.md` (badge, count, analytical table heading + new row translated, desktop line, layout tree, What's New bullet). Keep parallel to README.md.

- [ ] **Step 4: Verify and commit**

Run: `grep -rn "ownership-structure" README.md README.zh-CN.md CLAUDE.md`
Expected: hits in all three.

```bash
git add CLAUDE.md README.md README.zh-CN.md
git commit -m "docs: sync README/CLAUDE for ownership-structure module (19 modules)

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

### Task B.9: Smoke-test the ownership path

- [ ] **Step 1: Run the new script on a liquid name (needs network for yfinance)**

Run: `python stock-analysis/scripts/fetch_ownership.py AAPL --output-dir ./outputs/own_test`
Expected: prints `[ownership] wrote .../AAPL_ownership_bundle.json (status=ok)` when network is available; on a restricted box it prints `status=network_blocked`/`missing_dependency` and still writes a bundle (graceful). Inspect the JSON has `pct_held_institutions`, `float_shares`, `top10_concentration_pct`.

- [ ] **Step 2: Confirm no test artifacts ship; do not commit outputs/**

Run: `git status --porcelain outputs/`
Expected: `outputs/` is untracked/ignored — do NOT `git add` it.

---

## Phase C — Options-Gamma module (GEX)

> Most code-heavy phase. Pure math lives in `gamma_math.py` (stdlib only, no data deps) so it is
> trivially unit-testable; the CLI script wires it to `data_provider.py`.

### Task C.1: Add option-chain fetch helpers to data_provider.py

**Files:**
- Modify: `stock-analysis/scripts/data_provider.py` (`_opt_rows`, `yfinance_option_chain`, `get_option_chain`)

- [ ] **Step 1: Add the yfinance option-chain helpers**

In `stock-analysis/scripts/data_provider.py`, immediately after the `yfinance_ownership` function (added in Task B.1), add:

```python
def _opt_rows(frame: Any) -> list[dict]:
    rows: list[dict] = []
    if frame is None:
        return rows
    try:
        for _, row in frame.iterrows():
            strike = as_float(row.get("strike"))
            if strike is None:
                continue
            rows.append(
                {
                    "strike": strike,
                    "open_interest": as_float(row.get("openInterest")) or 0.0,
                    "implied_volatility": as_float(row.get("impliedVolatility")),
                    "volume": as_float(row.get("volume")) or 0.0,
                }
            )
    except Exception:  # noqa: BLE001
        return rows
    return rows


def yfinance_option_chain(ticker: str, max_expiries: int = 6) -> dict:
    if direct_disabled():
        return {"status": "network_blocked", "source": "yfinance", "provider": "none", "expiries": [], "chains": []}
    try:
        import yfinance as yf  # type: ignore

        tk = yf.Ticker(ticker)
        expiries = list(tk.options or [])[:max_expiries]
        chains = []
        for exp in expiries:
            oc = tk.option_chain(exp)
            chains.append({"expiry": exp, "calls": _opt_rows(oc.calls), "puts": _opt_rows(oc.puts)})
        return {
            "status": "ok" if chains else "no_data",
            "source": "yfinance",
            "provider": "yfinance",
            "expiries": expiries,
            "chains": chains,
        }
    except ImportError:
        return {"status": "missing_dependency", "source": "yfinance", "provider": "none", "expiries": [], "chains": []}
    except Exception as exc:  # noqa: BLE001
        return {"status": "error", "error": type(exc).__name__, "source": "yfinance", "provider": "none", "expiries": [], "chains": []}
```

- [ ] **Step 2: Add the `get_option_chain` wrapper**

Immediately after the `get_ownership` function (added in Task B.1), add:

```python
def get_option_chain(ticker: str, keys: dict[str, str] | None = None) -> dict:
    yf_chain = yfinance_option_chain(ticker)
    if yf_chain.get("status") == "ok":
        return yf_chain
    prefetched = read_prefetched_json(ticker, "options")
    if isinstance(prefetched, dict):
        prefetched.setdefault("status", "ok")
        prefetched.setdefault("provider", "prefetched_web")
        prefetched.setdefault("source", "prefetched_web")
        return prefetched
    return yf_chain
```

- [ ] **Step 3: Syntax-check and commit**

Run: `python -m py_compile stock-analysis/scripts/data_provider.py`
Expected: no output.

```bash
git add stock-analysis/scripts/data_provider.py
git commit -m "feat(data): add yfinance option-chain fetch helpers

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

### Task C.2: Write the failing gamma-math tests (TDD red)

**Files:**
- Create: `tests/test_gamma_math.py`

- [ ] **Step 1: Write the tests (the module they import does not exist yet)**

Create `tests/test_gamma_math.py` with:

```python
import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "stock-analysis" / "scripts"))

from gamma_math import bs_gamma, find_gamma_flip, gamma_wall, max_pain, net_gex_at  # noqa: E402


class TestBSGamma(unittest.TestCase):
    def test_positive_atm(self):
        self.assertGreater(bs_gamma(100, 100, 0.25, 0.30), 0.0)

    def test_atm_exceeds_far_otm(self):
        self.assertGreater(bs_gamma(100, 100, 0.25, 0.30), bs_gamma(100, 140, 0.25, 0.30))

    def test_degenerate_inputs_zero(self):
        self.assertEqual(bs_gamma(100, 100, 0.0, 0.30), 0.0)
        self.assertEqual(bs_gamma(100, 100, 0.25, 0.0), 0.0)
        self.assertEqual(bs_gamma(0, 100, 0.25, 0.30), 0.0)


class TestNetGex(unittest.TestCase):
    def test_calls_positive_puts_negative(self):
        calls = [{"strike": 100, "t_years": 0.25, "iv": 0.30, "oi": 1000, "kind": "call"}]
        puts = [{"strike": 100, "t_years": 0.25, "iv": 0.30, "oi": 1000, "kind": "put"}]
        self.assertGreater(net_gex_at(100, calls), 0.0)
        self.assertLess(net_gex_at(100, puts), 0.0)


class TestGammaFlip(unittest.TestCase):
    def test_flip_between_put_and_call_clusters(self):
        contracts = [
            {"strike": 90, "t_years": 0.25, "iv": 0.30, "oi": 5000, "kind": "put"},
            {"strike": 110, "t_years": 0.25, "iv": 0.30, "oi": 5000, "kind": "call"},
        ]
        flip = find_gamma_flip(contracts, 70, 130, steps=400)
        self.assertIsNotNone(flip)
        self.assertTrue(70 < flip < 130)

    def test_no_crossing_returns_none(self):
        contracts = [{"strike": 100, "t_years": 0.25, "iv": 0.30, "oi": 1000, "kind": "call"}]
        self.assertIsNone(find_gamma_flip(contracts, 80, 120))


class TestMaxPain(unittest.TestCase):
    def test_pain_minimized_at_heavy_oi_strike(self):
        calls = {90: 100, 100: 5000, 110: 100}
        puts = {90: 100, 100: 5000, 110: 100}
        self.assertEqual(max_pain(calls, puts), 100)

    def test_empty_none(self):
        self.assertIsNone(max_pain({}, {}))


class TestGammaWall(unittest.TestCase):
    def test_call_wall_at_highest_gamma_oi(self):
        contracts = [
            {"strike": 100, "t_years": 0.25, "iv": 0.30, "oi": 100, "kind": "call"},
            {"strike": 105, "t_years": 0.25, "iv": 0.30, "oi": 9000, "kind": "call"},
        ]
        self.assertEqual(gamma_wall(contracts, "call", 100), 105)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run to verify it FAILS**

Run: `python -m unittest tests.test_gamma_math -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'gamma_math'` (the import in the test cannot resolve yet).

### Task C.3: Implement gamma_math.py (TDD green)

**Files:**
- Create: `stock-analysis/scripts/gamma_math.py`

- [ ] **Step 1: Write the pure math module**

Create `stock-analysis/scripts/gamma_math.py` with:

```python
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
        contract_gex(spot, c["strike"], c["t_years"], c["iv"], c.get("oi", 0.0), c["kind"], r)
        for c in contracts
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
```

- [ ] **Step 2: Run tests to verify they PASS**

Run: `python -m unittest tests.test_gamma_math -v`
Expected: all 9 tests PASS.

- [ ] **Step 3: Syntax-check and commit**

Run: `python -m py_compile stock-analysis/scripts/gamma_math.py`
Expected: no output.

```bash
git add stock-analysis/scripts/gamma_math.py tests/test_gamma_math.py
git commit -m "feat(gamma): add pure GEX/flip/walls/max-pain math + unit tests

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

### Task C.4: Create fetch_options_gamma.py (CLI)

**Files:**
- Create: `stock-analysis/scripts/fetch_options_gamma.py`

- [ ] **Step 1: Write the CLI script**

Create `stock-analysis/scripts/fetch_options_gamma.py` with:

```python
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
```

- [ ] **Step 2: Syntax-check and commit**

Run: `python -m py_compile stock-analysis/scripts/fetch_options_gamma.py`
Expected: no output.

```bash
git add stock-analysis/scripts/fetch_options_gamma.py
git commit -m "feat(scripts): add fetch_options_gamma.py CLI

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

### Task C.5: Create the options-gamma module

**Files:**
- Create: `stock-analysis/modules/options-gamma.md`

- [ ] **Step 1: Write the module**

Create `stock-analysis/modules/options-gamma.md` with:

````markdown
# Options Positioning & Dealer Gamma Module

> Internal module of the orchestrator. Loaded on demand when the report needs
> this section, or when the user invokes it directly. New in 2026-06.

## Overview

Estimate **dealer gamma positioning (GEX)** to read the volatility regime and the option-driven
price magnets. This is the structural counterpart to the *flow* metrics (IV / put-call / skew) in
`modules/sentiment.md` — those stay in sentiment as a signal; **GEX, gamma flip, walls, and max
pain live here.**

Dealer-sign convention (the standard naive GEX): dealers are **long call gamma, short put gamma**.
- **Net GEX > 0 (positive-gamma regime):** dealers buy dips / sell rips → **vol suppression, mean
  reversion, pinning** toward walls / max pain.
- **Net GEX < 0 (negative-gamma regime):** dealers sell dips / buy rips → **vol amplification,
  trending, wider ranges** → widen stops or size down.

## Data

Run `scripts/fetch_options_gamma.py <TICKER> --output-dir <out>` (no key; yfinance option chain,
prefetched fallback). It computes Black-Scholes gamma per contract (yfinance gives no greeks),
sums signed GEX, finds the gamma flip by scanning spot ±30%, and reports call/put walls and max
pain. Output: `{TICKER}_gamma_bundle.json`.

## Standalone Markdown Report Mode

When called directly, produce a self-contained Markdown report in the user's language. Structure:

1. `## Gamma Verdict` (regime + one-line implication)
2. `## Net GEX & Regime`
3. `## Gamma Flip (Zero-Gamma) Level` (and distance from spot)
4. `## Call Wall / Put Wall` (resistance / support)
5. `## Max Pain` (OPEX magnet)
6. `## Implication For Levels, Stops, And Event Risk`

## Interpretation

| Metric | Reading |
|---|---|
| Net GEX sign | `+` vol suppression / mean-revert; `−` vol amplification / trend |
| Gamma flip level | regime-switch price; above = stable, below = unstable — use as invalidation context |
| Call wall | largest call gamma·OI strike → resistance / upside pin |
| Put wall | largest put gamma·OI strike → support |
| Max pain | strike minimizing holder payout → magnet into OPEX week |

## Feeds

- **Technical Analysis** — walls / flip are price levels complementing support/resistance.
- **Risk & Position Sizing** — negative-gamma regime → widen stop or reduce size.
- **Event Risk Check** — OPEX week, negative-gamma into earnings IV.

## Data Failure and Low-Confidence Rules

- Not optionable / chain too thin (all strikes filtered for OI<=0 or IV<=0) → section is
  `n/a — not optionable / chain too thin`. Do not fabricate GEX.
- Disclose the dealer-sign heuristic, the assumed rate, and that the snapshot drifts intraday and
  around OPEX.
- yfinance IV noise: contracts with non-positive OI or IV are dropped before computation.

## Output Contract

Return a Markdown report or section with: one-sentence gamma verdict (regime); net GEX + regime;
gamma flip level + distance from spot; call/put walls; max pain; implication for technical levels,
stop width, and event risk; explicit `n/a — <reason>` when not optionable; caveats (dealer-sign
heuristic, assumed rate, snapshot drift); standalone disclaimer when called directly:
`Not investment advice -- for your own research.`

## Depth gating

`full SOP`: include when the name is liquidly optionable. `standard`: only when objective =
short-term trade or on explicit request. `basic`: skip unless asked. Non-optionable → `n/a`.
````

- [ ] **Step 2: Verify and commit**

Run: `grep -n "Gamma Verdict" stock-analysis/modules/options-gamma.md`
Expected: one hit.

```bash
git add stock-analysis/modules/options-gamma.md
git commit -m "feat(module): add options-gamma (dealer GEX) module

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

### Task C.6: Wire the gamma module into SKILL.md

**Files:**
- Modify: `stock-analysis/SKILL.md`

- [ ] **Step 1: Overview module count**

Find `19 internal modules under \`modules/\` (10 analytical + 8 investor personas + 1 backtest)` (set by Task B.5) and change `19 internal modules` → `20 internal modules`, `10 analytical` → `11 analytical`.

- [ ] **Step 2: Module Routing row**

In `### Analytical modules`, add after the `modules/ownership-structure.md` row:
```
| Options dealer gamma (GEX), gamma flip, call/put walls, max pain | `modules/options-gamma.md` | full SOP (optionable); standard on request / short-term |
```

- [ ] **Step 3: Workflow — full SOP module set + fetch scripts**

In Workflow step 5, on the `full SOP` line (`- \`full SOP\` — all of the above plus \`modules/debate-panel.md\` plus the backtest signal-validation step (6).`), insert `plus \`modules/options-gamma.md\` (when optionable) ` before `plus the backtest`. Then in Workflow step 3 (data collection), add a sub-bullet:
```
   - **ownership + options data when those sections are in scope** — run `scripts/fetch_ownership.py <TICKER> --output-dir <out>` and (when optionable) `scripts/fetch_options_gamma.py <TICKER> --output-dir <out>` (no key required) and read their JSON bundles.
```

- [ ] **Step 4: Event Risk Check bullet**

In `## Event Risk Check`, add a bullet after the `unusual options implied volatility` line:
```
- dealer gamma regime (negative-gamma = amplified moves) and OPEX-week pin risk from `modules/options-gamma.md` when optionable
```

- [ ] **Step 5: Output Rules QA expected sections + description**

In `## Output Rules` QA expected-sections sentence, insert `options positioning / dealer gamma,` after `technicals + backtest validation,`. In the frontmatter `description:`, add `dealer gamma / GEX / max pain,` after the `ownership structure ...` keywords added in Task B.5.

- [ ] **Step 6: Verify and commit**

Run: `grep -n "options-gamma" stock-analysis/SKILL.md`
Expected: routing + workflow hits.

```bash
git add stock-analysis/SKILL.md
git commit -m "feat(skill): route options-gamma module (full SOP/optionable)

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

### Task C.7: Add the gamma section to the report schema + HTML

**Files:**
- Modify: `stock-analysis/references/report-template.md`
- Modify: `stock-analysis/references/report-template.html`

- [ ] **Step 1: Schema section (report-template.md)**

In the Default Report Output Schema, immediately after the `## Technical Analysis` block (before `## Risk and Position Sizing`), insert:
```
## Options Positioning & Dealer Gamma
- Net GEX and regime (positive = vol suppression / mean-revert; negative = vol amplification / trend):
- Gamma flip (zero-gamma) level and distance from spot:
- Call wall / put wall (gamma-weighted) as resistance / support:
- Max pain (OPEX magnet):
- Implication for technical levels, stop width, and event risk (OPEX / earnings IV):
- `n/a — <reason>` when not optionable / chain too thin
```

- [ ] **Step 2: Length budget row + Full SOP gate (report-template.md)**

In the `### full SOP` Section Length Budget table, add after the Technical Analysis row:
```
| Options Positioning & Dealer Gamma | 150–280 + table | full SOP when optionable; `n/a` otherwise |
```
In `## Full SOP Minimum Gate`, add a bullet:
```
- Options Positioning & Dealer Gamma present when the name is optionable (net GEX, gamma flip, walls, max pain), else `n/a — not optionable`.
```

- [ ] **Step 3: HTML section (report-template.html)**

In `references/report-template.html`, after the Backtest Validation block (the `<p><em>Signal tested...` line) and before `<h2>Risk and Position Sizing</h2>`, insert:
```html
<h2>Options Positioning &amp; Dealer Gamma</h2>
<!-- Fill from {TICKER}_gamma_bundle.json. If status=n/a, write: n/a — <reason>. -->
<table>
  <thead><tr><th>Metric</th><th>Value</th><th>Read</th></tr></thead>
  <tbody>
    <tr><td>Net GEX / regime</td><td></td><td>positive = vol suppression; negative = amplification</td></tr>
    <tr><td>Gamma flip (zero-gamma)</td><td class="num"></td><td>regime-switch level</td></tr>
    <tr><td>Call wall / put wall</td><td></td><td>resistance / support</td></tr>
    <tr><td>Max pain</td><td class="num"></td><td>OPEX magnet</td></tr>
  </tbody>
</table>
<p><strong>Implication (levels / stop width / event risk):</strong> </p>
```

- [ ] **Step 4: Verify and commit**

Run: `grep -n "Dealer Gamma" stock-analysis/references/report-template.md stock-analysis/references/report-template.html`
Expected: hits in both.

```bash
git add stock-analysis/references/report-template.md stock-analysis/references/report-template.html
git commit -m "docs(schema+html): add Options Positioning & Dealer Gamma section

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

### Task C.8: Cross-reference notes in sentiment.md + depth-framework.md

**Files:**
- Modify: `stock-analysis/modules/sentiment.md`
- Modify: `stock-analysis/references/depth-framework.md`

- [ ] **Step 1: sentiment.md options pointer**

In `stock-analysis/modules/sentiment.md`, at the end of the `### Short Interest and Options` section (after its table), add:
```
> Dealer gamma exposure (GEX), gamma flip, call/put walls, and max pain are covered in `modules/options-gamma.md`. This channel keeps only IV / put-call / skew as a near-term sentiment signal.
```

- [ ] **Step 2: depth-framework.md note**

In `references/depth-framework.md`, in the `full` row Modules cell (`all modules + backtest signal-validation`), change to `all modules (+ options-gamma when optionable) + backtest signal-validation`.

- [ ] **Step 3: Verify and commit**

Run: `grep -n "options-gamma" stock-analysis/modules/sentiment.md stock-analysis/references/depth-framework.md`
Expected: one hit each.

```bash
git add stock-analysis/modules/sentiment.md stock-analysis/references/depth-framework.md
git commit -m "docs: cross-reference options-gamma from sentiment/depth

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

### Task C.8b (OPTIONAL): Let debate roles cite gamma + ownership

Spec lists `debate-panel.md` as a light-touch enrichment. This is optional (the debate roles can
already reference any report section); include only if you want it explicit.

**Files:**
- Modify: `stock-analysis/modules/debate-panel.md`

- [ ] **Step 1: Add one line to the Quant / Risk role guidance**

Find the section describing the Quant and Risk-manager roles. Add:
```
Quant and Risk-manager roles should cite the dealer-gamma regime (`modules/options-gamma.md`) and structural float / short interest (`modules/ownership-structure.md`) when they bear on the setup — e.g., negative-gamma amplification, low-float squeeze risk.
```

- [ ] **Step 2: Commit (only if done)**

```bash
git add stock-analysis/modules/debate-panel.md
git commit -m "docs(debate): let quant/risk roles cite gamma + ownership

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

### Task C.9: Sync CLAUDE.md + READMEs for the gamma module

**Files:**
- Modify: `CLAUDE.md`
- Modify: `README.md`
- Modify: `README.zh-CN.md`

- [ ] **Step 1: CLAUDE.md**

Update **both** `11 analytical` occurrences → `12 analytical` (the top layout block comment AND the Architecture "Modules" bullet — both were set to 11 in Task B.8), add `options-gamma` to the Architecture bullet's module list, and add `modules/options-gamma.md` to the Consistency rule file list.

- [ ] **Step 2: README.md**

(a) badge `19%20modules` → `20%20modules`. (b) Module Map intro `19 internal modules` → `20`. (c) `### Analytical modules (11)` → `(12)` + add row:
```
| `modules/options-gamma.md` | Dealer gamma exposure (GEX), gamma flip / zero-gamma level, call/put walls, max pain. |
```
(d) Claude Desktop line `All 19 modules` → `All 20 modules`. (e) Repository Layout tree — add `│   │   ├── options-gamma.md`. (f) Add a `## What's New` bullet:
```
- **Options Positioning & Dealer Gamma module** — net GEX, gamma-flip (zero-gamma) level, call/put walls, and max pain from the yfinance option chain (Black-Scholes gamma), feeding technical levels, stop width, and event risk.
```
(g) Add a `## What's New` bullet for Kelly (Phase A, if not already present):
```
- **Total-capital Kelly sizing** — the Request Gate now asks for total investable capital (总仓位) and computes the Kelly-optimal allocation (fractional Kelly scaled by risk tolerance, capped by the single-stock / volatility caps). A fixed amount still overrides Kelly.
```

- [ ] **Step 3: README.zh-CN.md mirror**

Apply the same edits to `README.zh-CN.md` (badge, count, analytical heading + 2 new rows translated, desktop line, layout tree, two What's New bullets — gamma + Kelly). Keep parallel to README.md.

- [ ] **Step 4: Verify and commit**

Run: `grep -rn "options-gamma" README.md README.zh-CN.md CLAUDE.md`
Expected: hits in all three.

```bash
git add CLAUDE.md README.md README.zh-CN.md
git commit -m "docs: sync README/CLAUDE for options-gamma + Kelly (20 modules)

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

### Task C.10: Smoke-test the gamma path

- [ ] **Step 1: Optionable name (needs network)**

Run: `python stock-analysis/scripts/fetch_options_gamma.py AAPL --output-dir ./outputs/gamma_test`
Expected (with network): `[gamma] wrote .../AAPL_gamma_bundle.json (status=ok, regime=...)`; JSON has `net_gex`, `gamma_flip_level`, `call_wall_strike`, `put_wall_strike`, `max_pain_strike`. Without network: `status=n/a` and a bundle is still written (graceful).

- [ ] **Step 2: Non-optionable / bad ticker**

Run: `python stock-analysis/scripts/fetch_options_gamma.py ZZZZNOTREAL --output-dir ./outputs/gamma_test`
Expected: `status=n/a` with a `reason`; no crash. Do NOT `git add outputs/`.

---

## Phase D — Final cross-file consistency QA

### Task D.1: Reconcile all module counts and gate wording

- [ ] **Step 1: Counts agree**

Run: `grep -rn "internal modules\|analytical\|20%20modules\|19%20modules\|18%20modules" stock-analysis/SKILL.md CLAUDE.md README.md README.zh-CN.md`
Expected final state: SKILL.md "20 internal modules (11 analytical + 8 investor personas + 1 backtest)"; CLAUDE.md "12 analytical"; README badge "20 modules"; README/zh "Analytical modules (12)". Fix any stragglers and commit.

- [ ] **Step 2: No stale "budget" gate wording**

Run: `grep -rn "position budget\|budget: a dollar" stock-analysis CLAUDE.md README.md README.zh-CN.md`
Expected: no hits (all converted to total-capital / Kelly).

### Task D.2: Syntax-check every script

- [ ] **Step 1**

Run: `python -m py_compile stock-analysis/scripts/data_provider.py stock-analysis/scripts/fetch_ownership.py stock-analysis/scripts/fetch_options_gamma.py stock-analysis/scripts/gamma_math.py stock-analysis/scripts/fetch_price_charts.py stock-analysis/scripts/backtest.py`
Expected: no output (all compile).

### Task D.3: Run the full test suite

- [ ] **Step 1**

Run: `python -m unittest discover -s tests -v`
Expected: all tests in `test_ownership.py` + `test_gamma_math.py` PASS.

### Task D.4: Confirm skill ZIP would not ship tests

- [ ] **Step 1**

Run: `python -c "import pathlib; print('tests under stock-analysis:', list(pathlib.Path('stock-analysis').rglob('test_*.py')))"`
Expected: empty list (`[]`) — no test files inside the shipped folder.

### Task D.5: Final review against spec + hand back

- [ ] **Step 1: Spec success-criteria walkthrough**

Open `docs/superpowers/specs/2026-06-24-gamma-ownership-kelly-design.md` and confirm each of the 5 success criteria is met by the work above. Note any gap and fix inline.

- [ ] **Step 2: Final status (do NOT push or open a PR unless the user asks)**

Run: `git log --oneline main..feat/gamma-ownership-kelly` and `git status`
Expected: a clean tree on `feat/gamma-ownership-kelly` with the phase commits. Report the branch + commit list back to the user and ask whether to push / open a PR (per repo rule: distribute via GitHub Releases, never commit the `.skill`).

