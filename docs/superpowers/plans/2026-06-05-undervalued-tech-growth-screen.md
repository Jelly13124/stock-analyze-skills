# Undervalued Tech-Growth Screen → Full SOP — Implementation Plan

> **For agentic workers:** This is an overnight orchestration runbook. The Python screen
> helper is built test-first; the agent fan-out is executed via the Workflow tool and
> verified by artifact checks. Steps use checkbox (`- [ ]`) syntax.

**Goal:** Screen a hybrid US tech-growth universe with yfinance, run the `stock-analysis`
full SOP on every gate-passer (cap 12, Aggressive, $1000, medium-term, no personas), and
produce a master ranking HTML + per-name SOP HTMLs.

**Architecture:** A standalone Python helper pulls yfinance fundamentals for the universe.
A Workflow script expands the universe (web), fans out screen agents, computes Screen Scores
in JS, gates to ≤12 names, fans out one full-SOP agent per qualifier, and returns structured
results. The orchestrator then builds the master summary HTML.

**Tech Stack:** Python + yfinance; Workflow tool (JS); the repo's `stock-analysis` skill,
`scripts/fetch_price_charts.py`, `scripts/backtest.py`.

Spec: `docs/superpowers/specs/2026-06-05-undervalued-tech-growth-screen-design.md`

---

## File Structure

- `screen_run/screen_metrics.py` — yfinance fundamentals puller (scratch, not committed)
- `screen_run/test_screen_metrics.py` — smoke test for the helper
- `screen_run/universe_seed.txt` — seed tickers (one per line)
- `screen_run/workflow.js` — the Workflow script (persisted by the Workflow tool too)
- `outputs/<TICKER>/<TICKER>_full_sop.html` — per-name reports (written by SOP agents)
- `outputs/screen_summary.html` — master ranking (written by orchestrator in Phase 4)
- `outputs/screen_table.json` — raw screen rows + scores (audit trail)

---

### Task 1: Screen-metrics helper (yfinance puller)

**Files:**
- Create: `screen_run/screen_metrics.py`
- Test: `screen_run/test_screen_metrics.py`

- [ ] **Step 1: Write the helper**

```python
#!/usr/bin/env python3
"""Pull yfinance fundamentals for a list of tickers; emit one JSON array to stdout.
Standalone scratch tool for the overnight tech-growth screen. No API key needed."""
import sys, json, subprocess

def ensure_yfinance():
    try:
        import yfinance  # noqa
        return
    except ImportError:
        for args in (["--user"], ["--break-system-packages"], []):
            try:
                subprocess.run([sys.executable, "-m", "pip", "install", "-q",
                                "yfinance", *args], check=True)
                import yfinance  # noqa
                return
            except Exception:
                continue
        print("ERROR: could not install yfinance", file=sys.stderr); sys.exit(2)

FIELDS = [
    "shortName", "sector", "industry", "marketCap", "currentPrice",
    "revenueGrowth", "earningsGrowth", "revenueQuarterlyGrowth",
    "pegRatio", "trailingPE", "forwardPE", "priceToSalesTrailing12Months",
    "enterpriseToRevenue", "grossMargins", "operatingMargins",
    "targetMedianPrice", "numberOfAnalystOpinions",
    "fiftyTwoWeekHigh", "fiftyTwoWeekLow", "twoHundredDayAverage",
    "totalDebt", "totalCash", "freeCashflow", "averageVolume",
]

def pull(ticker):
    import yfinance as yf
    row = {"ticker": ticker, "error": None}
    try:
        info = yf.Ticker(ticker).info or {}
        for f in FIELDS:
            row[f] = info.get(f)
        # avg dollar volume proxy
        px, vol = info.get("currentPrice"), info.get("averageVolume")
        row["avgDollarVolume"] = (px * vol) if (px and vol) else None
    except Exception as e:
        row["error"] = str(e)
    return row

def main():
    tickers = [t.strip().upper() for t in sys.argv[1:] if t.strip()]
    if not tickers:
        tickers = [t.strip().upper() for t in sys.stdin.read().split() if t.strip()]
    ensure_yfinance()
    print(json.dumps([pull(t) for t in tickers]))

if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Write the smoke test**

```python
import json, subprocess, sys
def test_pull_amba_has_core_fields():
    out = subprocess.run([sys.executable, "screen_run/screen_metrics.py", "AMBA"],
                         capture_output=True, text=True, timeout=120)
    rows = json.loads(out.stdout)
    assert len(rows) == 1 and rows[0]["ticker"] == "AMBA"
    assert rows[0]["error"] is None
    assert rows[0]["marketCap"] and rows[0]["marketCap"] > 0
```

- [ ] **Step 3: Syntax-check**

Run: `python -m py_compile screen_run/screen_metrics.py`
Expected: no output (success).

- [ ] **Step 4: Run the smoke test (real network)**

Run: `python -m pytest screen_run/test_screen_metrics.py -q` (or run the script directly:
`python screen_run/screen_metrics.py AMBA CRDO`)
Expected: PASS — AMBA row has a positive marketCap and `error: null`. If yfinance is
network-blocked, note it and switch the screen phase to web-prefetched metrics.

- [ ] **Step 5: Write the seed file**

Create `screen_run/universe_seed.txt` with the seed tickers from the spec (one per line):
AMBA LSCC MTSI SITM POWI CRDO ALGM RMBS SLAB SMTC INDI NVTS FORM ONTO ACLS CAMT UCTT ICHR
NVMI AMKR ALAB BRZE GTLB FROG PATH ASAN MNDY DOCN FSLY PD ESTC CFLT AMPL PCOR APPN SEMR DV
GLBE BILL S TENB RPD QLYS VRNS CYBR DUOL IOT OUST RBLX YELP CARG.

---

### Task 2: Workflow script (screen → gate → SOP fan-out)

**Files:**
- Create: `screen_run/workflow.js`

- [ ] **Step 1: Author the workflow** with these phases:
  1. **Universe** — one agent expands the seed (passed via `args.seed`) with 2-3 web
     screener searches (small/mid-cap tech growth, growth-at-reasonable-price semis/SaaS),
     returns a deduped candidate ticker array (schema-validated). Cap universe at ~80.
  2. **Screen** — chunk the universe (~12/agent); each agent runs
     `python screen_run/screen_metrics.py <chunk>` and returns the parsed JSON rows.
  3. **Score + gate (JS, deterministic)** — compute Screen Score per the spec weights,
     apply hard guards (mktcap $300M–$20B, rev growth ≥15%, gross margin >0, avg $vol ≥$5M,
     not distressed), keep Screen Score ≥ 60, sort desc, take top 12. `log()` the funnel.
  4. **Full SOP** — `parallel` one agent per qualifier. Each agent prompt embeds the full
     SOP contract: read `stock-analysis/SKILL.md` + required modules, run
     `scripts/fetch_price_charts.py <T> --output-dir outputs/<T> --benchmark SPY --sector <etf>`
     (no intraday), run backtest signal-validation, build the report **incrementally** via
     Write+Edit to `outputs/<T>/<T>_full_sop.html`, Aggressive scoring, medium-term, $1000
     fresh entry, generic debate (no personas). Returns schema:
     `{ticker, convictionScore, verdict, bear, base, bull, thesis, shares, filePath}`.
  5. **Return** `{universeCount, screened, gated, qualifiers, sopResults}`.

- [ ] **Step 2: Guard against runaway** — if `gated.length > 12`, slice to 12 and record the
  overflow list in the return value as `deferred`.

- [ ] **Step 3: Verify the script parses** by launching it via the Workflow tool (Task 3).

---

### Task 3: Dispatch the overnight run

- [ ] **Step 1: Launch** the Workflow tool with `scriptPath: screen_run/workflow.js` (or
  inline `script`) and `args: { seed: [...] }`. Runs in background; returns a runId and
  notifies on completion.
- [ ] **Step 2: Record** the runId. If it hangs, resume with `resumeFromRunId`.
- [ ] **Step 3: On completion**, read the returned structured results.

---

### Task 4: Master summary HTML (Phase 4)

**Files:**
- Create: `outputs/screen_summary.html`, `outputs/screen_table.json`

- [ ] **Step 1: Write `outputs/screen_table.json`** with every universe row, Screen Score,
  guard pass/fail, gate status, and (for qualifiers) the SOP result — full audit trail.
- [ ] **Step 2: Build `outputs/screen_summary.html`** (self-contained, styled like
  `stock-analysis/references/report-template.html`):
  - Header: run date, parameters (Aggressive, $1000, medium-term, no personas), funnel counts.
  - **Winners table (Conviction Score ≥ 60)** at top — ticker, name, verdict, score,
    bear/base/bull, $1000 shares, one-line thesis, link to per-name HTML.
  - Full ranked table of all SOP'd names (incl. <60).
  - Screened-in-but-SOP-deferred list (if any) with screen metrics.
  - Full screen funnel table (universe → guards → gate).
  - Footer: data dates, `Not investment advice -- for your own research.`
- [ ] **Step 3: Verify** every per-name link resolves to an existing file; count winners.
- [ ] **Step 4: Leave a short morning note** summarizing counts and the winners list.

---

## Self-Review

- **Spec coverage:** universe (T1 seed + T2 web), screen+score (T1 helper + T2 JS), gate &
  cap-12 (T2), full SOP per qualifier (T2 phase 4), master summary + audit (T4), two distinct
  60s (Screen Score gate in T2 vs Conviction Score winners in T4) — all covered.
- **Placeholder scan:** helper and test are complete code; workflow phases are specified with
  exact commands; no TBDs.
- **Consistency:** field names in `screen_metrics.py` FIELDS match the Screen Score sources in
  the spec; SOP agent return schema matches the master-summary columns in T4.

## Execution

Per the user's standing instruction ("写完 spec 和 plan 你自动派 agent 运行"), execution
proceeds automatically via the Workflow tool (Task 3) — no interactive execution-mode choice.
