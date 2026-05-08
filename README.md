# Stock Analysis Skills / 股票分析 Skills

专业股票分析技能包，用于 Codex、Claude Code 和 Claude Desktop。它以 `stock-analysis` 为主 skill，协调宏观、行业、公司基本面、财报、估值、技术、风险仓位和多智能体辩论等子 skill，生成 Markdown 或 DOCX 格式的股票研究报告。

Professional stock analysis skill suite for Codex, Claude Code, and Claude Desktop. The main skill, `stock-analysis`, orchestrates macro, sector, company fundamentals, financial statements, valuation, technical analysis, risk/position sizing, and debate sub-skills to produce Markdown or DOCX equity research reports.

## What This Repo Contains / 仓库内容

```text
stock_analyze/
  README.md
  .gitignore
  Stock_Analysis_SOP_v1.0.md
  stock-analysis/
    SKILL.md
    agents/openai.yaml
    references/
      depth-framework.md
      report-template.md
      Stock_Analysis_SOP_v1.0.md
    scripts/
      fetch_price_charts.py
  stock-company-fundamentals/
    SKILL.md
    agents/openai.yaml
    references/institutional-company-analysis-bilingual.md
  stock-financial-statement-analysis/
    SKILL.md
    agents/openai.yaml
  stock-valuation-analysis/
    SKILL.md
    agents/openai.yaml
  stock-technical-analysis/
    SKILL.md
    agents/openai.yaml
  stock-macro-analysis/
    SKILL.md
    agents/openai.yaml
  stock-sector-analysis/
    SKILL.md
    agents/openai.yaml
  stock-risk-position-analysis/
    SKILL.md
    agents/openai.yaml
  stock-debate-panel/
    SKILL.md
    agents/openai.yaml
```

## Skill Architecture / Skill 架构

| Skill | 中文职责 | English Role |
|---|---|---|
| `stock-analysis` | 主调度 skill。识别请求、追问缺失信息、运行数据脚本、调用子 skill、汇总最终报告 | Main orchestrator. Clarifies the request, runs data scripts, coordinates sub-skills, and produces the final report |
| `stock-company-fundamentals` | 公司基本面、商业模式、护城河、管理层、资本配置、催化剂 | Company fundamentals, business model, moat, management, capital allocation, catalysts |
| `stock-financial-statement-analysis` | 10-K、10-Q、财报、利润表、资产负债表、现金流、指引质量 | Filings, earnings releases, income statement, balance sheet, cash flow, guidance quality |
| `stock-valuation-analysis` | 相对估值、DCF、目标价、空头 / 基准 / 多头情景 | Relative valuation, DCF, target price, bear/base/bull scenarios |
| `stock-technical-analysis` | 日线、周线、盘中 K 线、RSI、KDJ、MACD、布林带、ATR、支撑阻力 | Daily, weekly, intraday charts, RSI, KDJ, MACD, Bollinger Bands, ATR, support/resistance |
| `stock-macro-analysis` | 利率、通胀、就业、美联储、波动率、风险偏好 | Rates, inflation, jobs, Fed policy, volatility, risk regime |
| `stock-sector-analysis` | 行业结构、同业比较、行业 ETF、相对强弱 | Sector structure, peer comparison, sector ETF, relative strength |
| `stock-risk-position-analysis` | 仓位、止损、止盈、风险回报、事件风险、组合约束 | Position sizing, stop loss, take profit, risk/reward, event risk, portfolio constraints |
| `stock-debate-panel` | 完整报告中的多智能体辩论、反方观点、置信度校准 | Multi-agent debate, counterarguments, confidence calibration |

## Data Flow / 数据流程

1. User asks for a ticker, report, target price, trade plan, valuation, or financial review.
2. `stock-analysis` checks whether ticker, depth, output format, objective, and technical window are clear.
3. If the request is vague, it asks one clarification question before analysis.
4. The bundled script `stock-analysis/scripts/fetch_price_charts.py` fetches price data and generates technical data bundles plus chart images.
5. The script only fetches data and creates artifacts. It does not make recommendations.
6. Skills analyze the generated data, filings, earnings releases, macro data, sector/peer data, and news.
7. Full SOP reports include data health, evidence ledger, macro, sector, fundamentals, financials, valuation, technicals, risk, scenarios, scoring, event risk, debate, strategy, missing data, and disclaimer.

中文流程：

1. 用户提出 ticker、报告、目标价、交易计划、估值或财报分析请求。
2. `stock-analysis` 检查 ticker、报告深度、输出格式、用户目标和技术窗口是否明确。
3. 如果请求不明确，先追问一次，而不是默认生成简单报告。
4. `stock-analysis/scripts/fetch_price_charts.py` 负责抓取价格数据，并生成技术数据包和图表。
5. 脚本只负责获取数据和生成图表，不负责给出投资建议。
6. skills 基于脚本数据、财报、公告、宏观、行业、同业和新闻进行分析。
7. Full SOP 报告必须包含数据状态、证据台账、宏观、行业、基本面、财报、估值、技术、风险、情景、评分、事件风险、辩论、策略、缺失数据和免责声明。

## Report Depth / 报告深度

| Depth | 中文说明 | English Description |
|---|---|---|
| `basic` | 快速观点，少量指标，不做完整辩论 | Quick view with limited indicators and no formal debate |
| `standard` | 常规股票分析，覆盖宏观、行业、基本面、财报、估值、技术和风险 | Normal equity analysis covering macro, sector, fundamentals, financials, valuation, technicals, and risk |
| `full SOP` | 机构级完整报告，必须包含完整 SOP、多智能体辩论、证据台账、评分和策略 | Institutional-style full report with complete SOP, debate, evidence ledger, scoring, and strategy |

Bare tickers such as `NFLX` or `AXTI` are intentionally treated as unclear. The skill should ask for report depth, format, objective, and technical window before producing the report.

单独输入 `NFLX` 或 `AXTI` 这类纯 ticker 时，skill 会先追问报告深度、格式、目标和技术窗口，不会默认生成 Basic 报告。

## Install For Codex / 在 Codex 中安装

Current Codex Desktop installs these skills under:

当前 Codex Desktop 使用的安装目录：

```powershell
C:\Users\Jerry\.codex\skills
```

Copy the skill folders:

复制 skill 文件夹：

```powershell
$src = "C:\Users\Jerry\Desktop\stock_analyze"
$dst = "$env:USERPROFILE\.codex\skills"
$skills = @(
  "stock-analysis",
  "stock-company-fundamentals",
  "stock-financial-statement-analysis",
  "stock-valuation-analysis",
  "stock-technical-analysis",
  "stock-macro-analysis",
  "stock-sector-analysis",
  "stock-risk-position-analysis",
  "stock-debate-panel"
)

New-Item -ItemType Directory -Force -Path $dst | Out-Null
foreach ($skill in $skills) {
  Copy-Item -Path (Join-Path $src $skill) -Destination (Join-Path $dst $skill) -Recurse -Force
}
```

Example Codex usage:

Codex 示例：

```text
[$stock-analysis](C:\Users\Jerry\.codex\skills\stock-analysis\SKILL.md) NFLX full SOP md 盘中 目标价 / 短线交易 / 中期策略 / 长期投资 / 财报分析
```

Sub-skills can also be called directly:

子 skill 也可以单独调用：

```text
[$stock-valuation-analysis](C:\Users\Jerry\.codex\skills\stock-valuation-analysis\SKILL.md) NFLX full target price
[$stock-technical-analysis](C:\Users\Jerry\.codex\skills\stock-technical-analysis\SKILL.md) NFLX 盘中 5m KDJ RSI
```

## Install For Claude Code / 在 Claude Code 中安装

Claude Code supports local skills under user-level or project-level skill directories. Official docs describe `~/.claude/skills/<skill-name>/SKILL.md` and project-local `.claude/skills/<skill-name>/SKILL.md`.

Claude Code 支持用户级或项目级 skill 目录。官方文档描述的路径是 `~/.claude/skills/<skill-name>/SKILL.md`，也可以使用项目内 `.claude/skills/<skill-name>/SKILL.md`。

User-level install on Windows:

Windows 用户级安装：

```powershell
$src = "C:\Users\Jerry\Desktop\stock_analyze"
$dst = "$env:USERPROFILE\.claude\skills"
$skills = @(
  "stock-analysis",
  "stock-company-fundamentals",
  "stock-financial-statement-analysis",
  "stock-valuation-analysis",
  "stock-technical-analysis",
  "stock-macro-analysis",
  "stock-sector-analysis",
  "stock-risk-position-analysis",
  "stock-debate-panel"
)

New-Item -ItemType Directory -Force -Path $dst | Out-Null
foreach ($skill in $skills) {
  Copy-Item -Path (Join-Path $src $skill) -Destination (Join-Path $dst $skill) -Recurse -Force
}
```

Example Claude Code usage:

Claude Code 示例：

```text
/stock-analysis NFLX full SOP md 盘中 目标价 / 短线交易 / 中期策略 / 长期投资 / 财报分析
/stock-company-fundamentals NFLX full fundamentals report
/stock-technical-analysis NFLX 盘中 5m KDJ RSI
```

You can also ask naturally; Claude Code should load the skill when the request matches the `description` in `SKILL.md`.

也可以自然语言触发；当请求匹配 `SKILL.md` 的 `description` 时，Claude Code 会自动加载对应 skill。

## Install For Claude Desktop / 在 Claude Desktop 中安装

Claude Desktop and Claude.ai expose skills through the Skills interface. Because this project contains multiple standalone skills, install or upload all `stock-*` skill folders, not only `stock-analysis`.

Claude Desktop 和 Claude.ai 通过 Skills 界面使用 skill。因为本项目包含多个可独立调用的 skill，安装或上传时应包含全部 `stock-*` 文件夹，而不是只上传 `stock-analysis`。

Recommended workflow:

推荐流程：

1. Package each `stock-*` folder as a skill folder, or upload/install them one by one if the UI expects one skill per upload.
2. Keep folder structure intact: each skill folder must contain `SKILL.md`; references and scripts must stay under the same skill folder.
3. Enable code execution if you want Claude to run the price/chart script.
4. Ask Claude to use the stock analysis skill and specify ticker, depth, output format, objective, and technical window.

Example Claude Desktop prompt:

Claude Desktop 示例：

```text
Use the stock-analysis skill to analyze NFLX. Full SOP, Markdown, Chinese report.
Include target price, short-term trade, medium-term strategy, long-term investment, and financial statement analysis.
Use today intraday, 1-week candles, daily swing, and weekly medium-term windows.
```

Official references:

官方参考：

- Claude Code skills docs: https://docs.claude.com/en/docs/claude-code/skills
- Claude skills overview: https://claude.com/docs/skills/overview
- Creating custom Claude skills: https://claude.com/docs/skills/how-to

## API Keys And Security / API Key 和安全

This repo expects API keys to remain local. Do not commit API keys.

本仓库要求 API key 只保存在本地，不要提交到 Git。

Ignored by `.gitignore`:

`.gitignore` 已忽略：

```text
key.txt
keys.txt
api_keys.txt
.env
.env.*
*.pem
*.key
outputs/
reports/
*.log
__pycache__/
```

The data script accepts a key file path:

数据脚本通过 key 文件路径读取密钥：

```powershell
python stock-analysis\scripts\fetch_price_charts.py NFLX `
  --key-file C:\Users\Jerry\Desktop\stock_analyze\key.txt `
  --output-dir C:\Users\Jerry\Desktop\stock_analyze\outputs\NFLX_test `
  --benchmark SPY `
  --sector XLC `
  --intraday-window 1d `
  --intraday-resolution 5
```

## Expected Full SOP Output / Full SOP 应包含内容

A complete report should include:

完整报告应包含：

- Data timestamp / 数据时间戳
- Data health / 数据状态
- Executive summary / 核心结论
- Evidence ledger / 证据台账
- Macro regime / 宏观环境
- Sector and peer comparison / 行业和同业比较
- Company fundamentals / 公司基本面
- Financial statement review / 财报分析
- Valuation analysis / 估值分析
- Technical analysis with daily, weekly, and requested intraday charts / 日线、周线和指定盘中窗口技术分析
- Risk and position sizing / 风险和仓位管理
- Bear/base/bull scenarios / 空头、基准、多头情景
- Conviction score / 置信度或设置质量评分
- Event risk check / 事件风险检查
- Multi-agent debate / 多智能体辩论
- Final conditional strategy / 最终条件策略
- Missing data and low-confidence areas / 缺失数据和低置信度区域
- Disclaimer / 免责声明

## Development Notes / 开发说明

- Keep sub-skills independently callable.
- Keep `fetch_price_charts.py` data-only. It should not produce buy/sell recommendations.
- If new data fields are needed, add them to the data bundle and update `stock-analysis/references/report-template.md`.
- If the full report becomes too short, strengthen the report template or the relevant sub-skill contract before changing prompts ad hoc.
- Sync changes to both the repo folder and the installed skill folder when testing locally.

中文开发规则：

- 子 skill 必须可以独立调用。
- `fetch_price_charts.py` 只负责数据和图表，不负责给出买卖建议。
- 如果需要新的数据字段，先加入数据包，再更新 `stock-analysis/references/report-template.md`。
- 如果完整报告变短，优先增强报告模板或子 skill 合约，不要只临时修改提示词。
- 本地测试时，需要同步 repo 文件夹和已安装 skill 文件夹。

## Disclaimer / 免责声明

This project is for research workflow automation only. It does not provide financial advice.

本项目仅用于研究流程自动化，不构成投资建议。
