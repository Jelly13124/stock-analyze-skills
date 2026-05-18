# Claude.ai Web Setup

This repo is the source of truth for the consolidated `stock-analysis` skill. Claude Code, Claude Desktop, and Codex can use the folder directly. Claude.ai web needs it uploaded as a single ZIP.

As of the 2026-05 consolidation, what used to be 18 separate sibling skills now lives as 18 modules under `stock-analysis/modules/`. Installation is one folder (or one ZIP), not 18.

## Build the ZIP

Run from the repo root on Windows:

```powershell
.\tools\build_claude_zips.ps1
```

Output:

```text
claude_web_zips/stock-analysis.zip
  stock-analysis/
    SKILL.md
    agents/
    modules/
      macro.md, sector.md, company-fundamentals.md, financial-statements.md,
      valuation.md, technical.md, sentiment.md, risk-position.md,
      debate-panel.md, backtest.md,
      investors/
        buffett.md, munger.md, graham.md, lynch.md,
        fisher.md, wood.md, druckenmiller.md, burry.md
    references/
    scripts/
```

Do not upload a ZIP where `SKILL.md` is directly at the root.

## Upload To Claude.ai

1. Open Claude.ai.
2. Enable Code execution and file creation in Settings / Capabilities.
3. Go to Customize / Skills.
4. Upload `stock-analysis.zip`. That is the only upload.
5. Toggle it on.

## API Keys

Do not put API keys in the repo or ZIP files.

For Claude.ai web, upload a local `key.txt` when starting a stock analysis session. The skill checks:

```text
./key.txt
/mnt/user-data/uploads/key.txt
/mnt/data/key.txt
```

Expected format:

```text
FINNHUB_API_KEY=your_finnhub_key
ALPHA_VANTAGE_API_KEY=your_alpha_vantage_key
FRED_API_KEY=your_fred_key
```

If Claude.ai blocks direct Python network calls, the skill will use `stock-analysis/scripts/web_prefetch_helper.md`: Claude gathers data with web tools, writes JSON to `/tmp/prefetched_data`, then reruns the chart script.

## Quick Test Prompts

Should trigger:

```text
分析一下 NVDA 最近的趋势
give me a full SOP report on TSLA
今天 ROBO 怎么样?
analyze NVDA through Buffett's lens
Buffett vs Wood debate on TSLA, 2 rounds
backtest NVDA KDJ golden cross 2020-2025
```

Should not trigger:

```text
帮我写一首诗
你是什么
```

## Local Verification

Direct mode (data scripts):

```powershell
python .\stock-analysis\scripts\fetch_price_charts.py NFLX --key-file .\key.txt --output-dir .\outputs\NFLX_direct_test --intraday-window 1d --intraday-resolution 5 --no-charts
```

Backtest:

```powershell
python .\stock-analysis\scripts\backtest.py NVDA --mode indicator --strategy kdj_golden_cross --start 2020-01-01 --end 2025-12-31 --key-file .\key.txt --output-dir .\outputs\NVDA_backtest
```

Prefetch mode:

```powershell
$env:STOCK_ANALYSIS_DISABLE_DIRECT="1"
$env:PREFETCH_DIR="$PWD\prefetched_data"
python .\stock-analysis\scripts\fetch_price_charts.py TEST --output-dir .\outputs\TEST_prefetch --intraday-window 1d --intraday-resolution 5
```

Clear test env vars after testing:

```powershell
Remove-Item Env:\STOCK_ANALYSIS_DISABLE_DIRECT
Remove-Item Env:\PREFETCH_DIR
```

## Rollback to the multi-skill layout (if needed)

The 18 original sibling folders are archived under `_legacy/`. See `_legacy/README.md` for the rollback procedure.
