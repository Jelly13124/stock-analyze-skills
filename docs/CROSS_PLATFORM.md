# Claude.ai Web Setup

This repo is the source of truth for the stock analysis skills. Claude Code, Claude Desktop, and Codex can use the folders directly. Claude.ai web needs each skill uploaded as a ZIP file.

## Build ZIP Files

Run from the repo root on Windows:

```powershell
.\tools\build_claude_zips.ps1
```

Output goes to:

```text
claude_web_zips/
```

The ZIP structure must be:

```text
stock-analysis.zip
  stock-analysis/
    SKILL.md
    scripts/
    references/
```

Do not upload a ZIP where `SKILL.md` is directly at the root.

## Upload To Claude.ai

1. Open Claude.ai.
2. Enable Code execution and file creation in Settings / Capabilities.
3. Go to Customize / Skills.
4. Upload `stock-analysis.zip` first.
5. Upload the other `stock-*.zip` files.
6. Toggle every uploaded skill on.

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
```

Should not trigger:

```text
帮我写一首诗
你是什么
```

## Local Verification

Direct mode:

```powershell
python .\stock-analysis\scripts\fetch_price_charts.py NFLX --key-file .\key.txt --output-dir .\outputs\NFLX_direct_test --intraday-window 1d --intraday-resolution 5 --no-charts
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
