# Stock Analyze Skills / 股票分析 Skill 包

这是一个可在 Codex、Claude Code、Claude Desktop 中使用的股票分析 skill 包。主 skill 是 `stock-analysis`，它会按用户需求调用多个子 skill，生成基础、标准或完整 SOP 股票分析报告。

This repo contains a stock analysis skill suite for Codex, Claude Code, and Claude Desktop. The main skill is `stock-analysis`; it coordinates sub-skills to generate basic, standard, or full SOP equity reports.

## 1. Skill 结构 / Skill Structure

```text
stock-analyze-skills/
  stock-analysis/                       # main skill
  stock-company-fundamentals/           # company and business quality
  stock-financial-statement-analysis/   # 10-K, 10-Q, earnings, cash flow
  stock-valuation-analysis/             # valuation and target price
  stock-technical-analysis/             # charts, RSI, KDJ, MACD, support/resistance
  stock-macro-analysis/                 # rates, Fed, CPI, jobs, risk regime
  stock-sector-analysis/                # sector, peers, ETF relative strength
  stock-risk-position-analysis/         # position sizing, stop loss, trade plan
  stock-debate-panel/                   # full SOP debate stage
```

| Skill | 中文用途 | English Use |
|---|---|---|
| `stock-analysis` | 主调度，负责完整报告 | Main orchestrator |
| `stock-company-fundamentals` | 公司基本面、商业模式、护城河 | Company fundamentals |
| `stock-financial-statement-analysis` | 财报、10-K、10-Q、现金流 | Financial statements |
| `stock-valuation-analysis` | 估值、目标价、情景分析 | Valuation and target price |
| `stock-technical-analysis` | 日线、周线、盘中、KDJ、RSI | Technical analysis |
| `stock-macro-analysis` | 宏观、利率、通胀、美联储 | Macro analysis |
| `stock-sector-analysis` | 行业、同业、行业 ETF | Sector and peers |
| `stock-risk-position-analysis` | 仓位、止损、风险回报 | Risk and position plan |
| `stock-debate-panel` | 多智能体辩论 | Multi-agent debate |

## 2. 快速安装 / Quick Install

先 clone：

```powershell
git clone https://github.com/Jelly13124/stock-analyze-skills.git
cd stock-analyze-skills
```

安装到 Codex：

```powershell
Copy-Item .\stock-* "$env:USERPROFILE\.codex\skills\" -Recurse -Force
```

安装到 Claude Code：

```powershell
Copy-Item .\stock-* "$env:USERPROFILE\.claude\skills\" -Recurse -Force
```

Claude Desktop：

```text
把所有 stock-* 文件夹导入 Claude Desktop 的 Skills 页面。
至少要导入 stock-analysis；如果要完整 SOP，就导入全部 stock-* folders。
```

For Claude Desktop, import all `stock-*` folders in the Skills page. At minimum import `stock-analysis`; for full SOP reports, import all sub-skills.

Claude.ai 网页端需要先打包 zip：

```powershell
.\tools\build_claude_zips.ps1
```

详细说明见 `docs/CROSS_PLATFORM.md`。

## 3. API Key 配置 / API Key Setup

在 repo 根目录创建 `key.txt`：

```powershell
notepad .\key.txt
```

填入下面格式：

```text
FINNHUB_API_KEY=your_finnhub_key
ALPHA_VANTAGE_API_KEY=your_alpha_vantage_key
FRED_API_KEY=your_fred_key
```

用途：

| Key | 用途 |
|---|---|
| `FINNHUB_API_KEY` | 抓取 quote 和部分实时/盘中数据 |
| `ALPHA_VANTAGE_API_KEY` | 抓取日线、周线历史 OHLCV |
| `FRED_API_KEY` | 抓取宏观数据，如利率、VIX、信用利差 |

Yahoo intraday chart data does not require an API key. The script uses it as the default intraday source.

Yahoo 盘中 K 线默认不需要 API key，脚本会优先用它生成盘中图表。

测试数据脚本：

```powershell
python .\stock-analysis\scripts\fetch_price_charts.py NFLX --key-file .\key.txt --output-dir .\outputs\NFLX_test --benchmark SPY --sector XLC --intraday-window 1d --intraday-resolution 5
```

如果成功，会生成：

```text
outputs/NFLX_test/NFLX_technical_bundle.json
outputs/NFLX_test/NFLX_daily_chart.png
outputs/NFLX_test/NFLX_intraday_1d_5m_chart.png
```

## 4. 使用方式 / Usage

Codex：

```text
[$stock-analysis](C:\Users\Jerry\.codex\skills\stock-analysis\SKILL.md) NFLX full SOP md 盘中 目标价 / 短线交易 / 中期策略 / 长期投资 / 财报分析
```

Claude Code：

```text
/stock-analysis NFLX full SOP md 盘中 目标价 / 短线交易 / 中期策略 / 长期投资 / 财报分析
```

Claude Desktop：

```text
Use stock-analysis to analyze NFLX.
Full SOP, Markdown, Chinese report.
Include target price, short-term trading, medium-term strategy, long-term investing, and financial statement analysis.
Use intraday, 1-week, daily, and weekly technical windows.
```

子 skill 也可以单独调用：

```text
stock-valuation-analysis NFLX full target price
stock-technical-analysis NFLX intraday 5m KDJ RSI
stock-company-fundamentals NFLX full fundamentals report
```

## 5. 报告深度 / Report Depth

| Depth | 中文说明 | English |
|---|---|---|
| `basic` | 快速分析，不做完整辩论 | Quick view |
| `standard` | 常规研究报告 | Normal research report |
| `full SOP` | 完整 SOP、图表、估值、策略、多智能体辩论 | Full report with charts, valuation, strategy, and debate |

如果用户只输入一个 ticker，例如 `NFLX`，主 skill 应先追问报告深度、格式、目标和技术窗口。

If the user only enters a bare ticker such as `NFLX`, the main skill should ask for depth, output format, objective, and technical window before generating a report.
