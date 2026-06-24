<div align="right">

[English](README.md) · **中文**

</div>

# 股票分析 Skill 包 (Stock Analyze Skills)

![Skills](https://img.shields.io/badge/skills-1%20suite%2C%2019%20modules-blue)
![Personas](https://img.shields.io/badge/investor%20personas-8-success)
![Multi-Subagent Debate](https://img.shields.io/badge/debate-real%20multi--subagent-orange)
![Backtest](https://img.shields.io/badge/backtest-v1%20indicator%20%2B%20signal%20%2B%20persona-yellow)
![Platforms](https://img.shields.io/badge/platforms-Claude%20Code%20·%20Desktop%20·%20Codex%20·%20Web-purple)
![Last Commit](https://img.shields.io/github/last-commit/Jelly13124/stock-analyze-skills)

一套机构级股票研究的可组合 Skill 工具集,把多步分析师 SOP 翻译成 Markdown 提示词文件 — 含显式数值阈值、真实多 subagent 辩论、以及 8 位可直接对话的投资大师人格。

支持 Claude Code、Claude Desktop、Cowork、Codex,以及 Claude.ai 网页端 (需要额外打包 zip)。

## 最近更新 (2026-05)

- **统一 HTML 输出** — 每份报告现在都是单个自包含 HTML 文件: 图表内嵌、明暗双色、可直接打印成 PDF。输出格式问题已移除 — DOCX (生成慢、丢图表保真度) 和"Markdown 当报告" (不能嵌图) 都已弃用。
- **无需 API key — `yfinance` 是主数据源** — 没有 key 时, `yfinance` 是实时报价、OHLCV、基本面的主数据源 (首次运行自动安装), 盘中走 Yahoo。Web 搜索负责补非价格类缺口 (新闻、分析师修正、催化剂日期), 并强制做时效复查。API key 现在完全可选。
- **Section Length Budget (分区块字数预算)** — 每个区块给字数区间, 有下限 (确保够细) 和上限 (杜绝注水)。公司基本面和财报审阅拿到最高字数预算, 是全报告最详细的两个区块。
- **人格辩论开关** — Request Gate 里唯一的人格相关提问是一个开关 (仅 full SOP): 多智能体辩论用投资人人格还是通用 Bull/Bear/Quant/Risk 角色。具体用**哪些**人格仍由 Claude 按个股画像自动选 — 从不让用户点名。
- **单 skill 合并** — 原本 18 个 `stock-*` 独立 skill 现在合并成一个 `stock-analysis` skill 下的 18 个 module。安装从 "上传 18 个 ZIP" 变成 "上传 1 个 ZIP"。顶层 `SKILL.md` 是路由器, 按需 `Read` 加载 `stock-analysis/modules/` 下的对应 module, token 成本仍然随实际工作量缩放。设计见 `MIGRATION_PLAN.md`; 18 个原始 skill 可从 git 历史恢复。
- **`stock-backtest` v1** (现在是 `modules/backtest.md`) — 单股票回测引擎。三种模式: 规则化指标策略 (KDJ 金叉、SMA50/200、RSI 均值回归、布林下轨反弹、MACD)、信号事件研究 (信号 X 在 +1/+5/+10/+20/+60 日的远期收益是否为正?)、以及投资大师配仓回测 (Lynch / Graham / Burry / Druckenmiller-lite)。报告样本内 / 样本外指标分离, 扣除真实交易成本, 当样本外证据不足时**拒绝**给出"策略有效"结论。Buffett / Munger / Fisher / Wood 人格在 v1 返回 `data_insufficient` — 它们等 v2 把 fundamentals 层扩展到 owner earnings + ROIC 时间序列后再开放。
- **8 个投资大师人格 skill** — Buffett · Munger · Graham · Lynch · Fisher · Wood · Druckenmiller · Burry。可单独激活,以该大师视角对话;也可在辩论环节中替换通用 Bull / Bear 角色。
- **真实多 subagent 辩论** — `modules/debate-panel.md` 在 Claude Code 中会**真正**派遣并行 `Agent` 工具调用,每个角色每轮一个独立 subagent。full SOP 默认 2 轮;参与人格由 Claude 按个股画像自动选取。仅在 Agent tool 不可用时降级为单 LLM 顺序模式,且必须在 transcript 头部明确标注。
- **新增 `stock-sentiment-analysis`** — 4 通道情绪分析: insider 交易 (20%) + news flow (25%) + 分析师 EPS revision (35%) + short interest / 期权定位 (20%)。
- **量化层加在财报 / 技术 / 估值 / 风险 4 个 module** — 显式数值阈值 (ROE > 15%、P/B < 1.5、FCF yield ≥ 15%、ADX、Z-score、Owner Earnings、波动率调整仓位上限等) **叠加在**已有的定性框架之上,不替换。

## Module 列表

整套 suite 是一个 skill (`stock-analysis`),包含 19 个被 orchestrator 按需加载的内部 module。

### 分析类 module (11 个)

| Module | 用途 |
|---|---|
| `modules/macro.md` | 宏观环境: 美联储、利率、收益率曲线、CPI、就业、VIX、流动性。 |
| `modules/sector.md` | 行业 / GICS / 同业对比、行业 ETF 强度。 |
| `modules/company-fundamentals.md` | 商业模式、护城河、TAM、定价权、管理层、资本配置。 |
| `modules/financial-statements.md` | 10-K / 10-Q、三大报表、盈利质量 + Quantitative Quick Filters。 |
| `modules/valuation.md` | 相对估值 + 内在估值,DCF、Owner Earnings、Residual Income、WACC 参考表、情景概率加权。 |
| `modules/technical.md` | 多时间框架趋势、RSI / KDJ / MACD / BB / ATR / OBV + 4 策略量化层。 |
| `modules/sentiment.md` | Insider 交易、新闻流、分析师 EPS 修正、空头利息、期权定位。 |
| `modules/ownership-structure.md` | 流通股、机构 / 内部人持股 %、前十大股东、股权分级、投票权、结构性空头。 |
| `modules/risk-position.md` | 仓位、止损逻辑、R:R、行业上限、波动率调整的单股 cap。 |
| `modules/debate-panel.md` | 真实多 subagent 投资委员会辩论 (1 / 2 / 3 轮)。 |
| `modules/backtest.md` | 单股票历史回测。指标策略、信号事件研究、或投资大师配仓回测。输出权益曲线、Sharpe、MDD、交易明细 CSV、样本内 / 样本外指标拆分、过拟合诊断。 |

### 投资大师人格 module (8 个)

| Module | 思维框架 |
|---|---|
| `modules/investors/buffett.md` | 护城河 + 股东盈余 + 安全边际 + 能力圈。 |
| `modules/investors/munger.md` | ROIC + 资本配置 + 业务可预测性 + 品质优先于价格。 |
| `modules/investors/graham.md` | Net-Net + Graham number + 股息记录 + 防守型投资者测试。 |
| `modules/investors/lynch.md` | GARP + PEG ≤ 1 + 6 类公司分类 + 投资你了解的。 |
| `modules/investors/fisher.md` | 15 点清单 + scuttlebutt + R&D 强度 + 管理层深度。 |
| `modules/investors/wood.md` | 破坏式创新 + R&D > 15% + 5 年指数模型 + 25x 终值倍数。 |
| `modules/investors/druckenmiller.md` | 宏观优先 + 集中持仓 + 不对称风险回报 + 动量叠加。 |
| `modules/investors/burry.md` | 深度价值 + FCF yield ≥ 15% + EV/EBIT < 6 + 逆向布局。 |

每个人格都有显式的 `Conflict And Pass Rules` — Buffett 拒绝评价 pre-profit 生物科技股**是正确行为**,不是分析失败。各人格的评分权重和阈值参考 `virattt/ai-hedge-fund/src/agents/<persona>.py`,翻译成 SKILL.md 提示词形式。

## 与 ai-hedge-fund 的差异

| 维度 | 本仓库 (Skill 体系) | virattt/ai-hedge-fund |
|---|---|---|
| 形式 | Markdown SKILL.md 提示词 | Python + LangGraph 框架 |
| 自定义 | 改一个提示词文件 | 改代码 + 改框架 |
| 数据缺失处理 | 内置 Data Health 门禁与降级规则 | 字段缺失会崩 |
| 定性 + 定量 | 双轨叠加 (定性权威, 定量做过滤) | 仅定量 |
| 人格驱动辩论 | 是 — Claude Code 原生 Agent tool 派每个 persona 为独立 subagent | 是 — LangGraph nodes |
| 回测 | **v1 单股 (指标 / 信号 / 大师) — `modules/backtest.md`** | 有 (多股 + walk-forward) |
| 接入成本 | `git clone` + 拷贝目录 | `pip install` + LLM API key + 数据 API key |
| 输出形式 | 专业级单文件 HTML 报告 | JSON 信号 + reasoning |

两个项目解决不同问题。ai-hedge-fund 是可编程的对冲基金模拟器。本仓库是分析师的提示词库,产出报告级输出,数据不全时也能继续工作。

## 快速安装

### 一键装(npx,Claude Code)

```bash
npx skills add Jelly13124/stock-analyze-skills/stock-analysis
```

直接拷到 `~/.claude/skills/stock-analysis/`,装完重启 Claude Code 就能用。下面那些步骤可以跳过 —— 除非你还想装 Codex / Desktop / Web,或者想读 / 改源码。

### 手动安装 —— 先 clone

```powershell
git clone https://github.com/Jelly13124/stock-analyze-skills.git
cd stock-analyze-skills
```

### Claude Code

```powershell
Copy-Item .\stock-analysis "$env:USERPROFILE\.claude\skills\" -Recurse -Force
```

### Codex

```powershell
Copy-Item .\stock-analysis "$env:USERPROFILE\.codex\skills\" -Recurse -Force
```

### Claude Desktop

在 Skills 页面里导入单个 `stock-analysis` 文件夹。全部 19 个 module 都在里面。

### Claude.ai 网页端

下载最新 release 直接传,不用自己打包:

**[下载 `stock-analysis.skill`(最新 release)](https://github.com/Jelly13124/stock-analyze-skills/releases/latest/download/stock-analysis.skill)**

然后进 **Customize → Skills → + → Upload a skill**,把文件拖进去。

想自己打包?跑 `.\tools\build_claude_zips.ps1` → 上传 `claude_web_zips/stock-analysis.zip`。注意上传的是那个 `.zip` **文件本身**(压缩包图标)—— 不是解压后的文件夹,拖文件夹会被报错 *"must have a .skill, .zip, or .md extension"*。详细跨平台说明见 `docs/CROSS_PLATFORM.md`。

## API Key (可选)

**不需要任何 API key。** 没有 key 时, 数据脚本用 `yfinance` 作为实时报价、OHLCV、基本面的主数据源 (首次运行自动安装), 盘中走 Yahoo。Web 搜索负责补非价格类缺口 (新闻、分析师修正、催化剂日期), 并做时效复查。

加 key 是可选的, 只影响"先试哪个数据源"。要用的话, 在 repo 根目录创建 `key.txt`:

```text
FINNHUB_API_KEY=your_finnhub_key
ALPHA_VANTAGE_API_KEY=your_alpha_vantage_key
FRED_API_KEY=your_fred_key
```

| Key | 用途 | 是否必需 |
|---|---|---|
| `FINNHUB_API_KEY` | 报价和部分盘中数据 | 可选 |
| `ALPHA_VANTAGE_API_KEY` | 日线 / 周线历史 OHLCV | 可选 |
| `FRED_API_KEY` | 宏观数据 (利率、VIX、信用利差) | 可选 |

冒烟测试 (有没有 `key.txt` 都能跑 — 没有 key 就省略 `--key-file`):

```powershell
python .\stock-analysis\scripts\fetch_price_charts.py NFLX `
  --key-file .\key.txt --output-dir .\outputs\NFLX_test `
  --benchmark SPY --sector XLC `
  --intraday-window 1d --intraday-resolution 5
```

成功时生成:

```text
outputs/NFLX_test/NFLX_technical_bundle.json
outputs/NFLX_test/NFLX_daily_chart.png
outputs/NFLX_test/NFLX_intraday_1d_5m_chart.png
```

## 使用方式

5 种模式都用同一个 `/stock-analysis` 斜杠命令 — 区别在你怎么描述需求, orchestrator 自动路由到对应 module。

### 模式 1 — 完整 SOP 报告

```text
/stock-analysis NFLX full SOP, 目标 目标价 (或 短线交易 / 中期策略 / 长期投资 / 财报分析)
```

orchestrator 收集证据,按顺序 `Read` 必需的 module,组装成单份自包含 HTML 报告。

### 模式 2 — 单 module 调用

```text
/stock-analysis 只跑 valuation module, NFLX full 目标价
/stock-analysis 跑一下 technical module, NFLX 盘中 5m KDJ RSI
/stock-analysis 只要 sentiment module, NFLX 30 天窗口
```

不再有每个 module 各自的斜杠命令 — 在提示里写明要哪个 module 即可。

### 模式 3 — 大师人格对话

```text
/stock-analysis 用 Buffett 的视角分析 NVDA
```

orchestrator 加载 `modules/investors/buffett.md`, 整个对话以该大师视角进行。Buffett 会拒绝评价能力圈外的名字, Wood 会嫌弃成熟分红股不值得投资 — 这是设计本意。

### 模式 4 — 真实多 subagent 辩论

```text
/stock-analysis Buffett vs Wood 辩论 TSLA, 2 轮
```

orchestrator 加载 `modules/debate-panel.md`, 把每个角色作为独立并行 `Agent` subagent 派遣 (Claude Code 中) 或退化到带标签的单 LLM 模式 (其他环境)。轮数默认 2;人格名单由 Claude 按个股画像自动选取。

### 模式 5 — 回测

```text
/stock-analysis 回测 NVDA, indicator kdj_golden_cross, 2020-01-01 到 2025-12-31
/stock-analysis 回测 NVDA, signal kdj_golden_cross, 20 日远期收益
/stock-analysis 回测 MSFT, Lynch persona, 季度调仓, 2018 到 2025
```

输出权益曲线 PNG、交易明细 CSV、以及 Markdown verdict, 含样本内 / 样本外指标拆分、交易成本假设、过拟合诊断。仅支持单股票; 多股组合 + walk-forward 参数优化是 v2 计划。

## 报告深度

| Depth | 适用场景 | 输出 |
|---|---|---|
| `basic` | 快速一瞥、初判 | Data Health、价格快照、估值快照、关键风险 |
| `standard` | 常规研究请求 | 宏观 / 行业 / 基本面 / 财报 / 估值 / 技术 / 情绪 / 风险计划 + bear/base/bull 区间 |
| `full SOP` | 机构级报告或明确"完整"请求 | 完整机构级工作流 + 证据账本 + DCF / 情景计算 + 图表 + 评分 + 事件风险 + 回测验证 + 真实多 subagent 辩论 (1-3 轮) |

如果用户只输入裸 ticker,主 skill 会先追问报告深度、目标、总仓位(用于凯利最优配比)或固定金额,以及(仅 full SOP)辩论模式是否启用投资人人格,再开始生成。报告统一输出为单文件 HTML,不再追问输出格式;技术窗口由目标自动推导。

## 仓库结构

```text
stock-analyze-skills/
├── stock-analysis/                       # 唯一发布的 skill
│   ├── SKILL.md                          # 路由器 + 工作流 + SOP
│   ├── agents/openai.yaml
│   ├── modules/                          # 按需加载的内部 module
│   │   ├── macro.md
│   │   ├── sector.md
│   │   ├── company-fundamentals.md
│   │   ├── financial-statements.md
│   │   ├── valuation.md
│   │   ├── technical.md
│   │   ├── sentiment.md
│   │   ├── ownership-structure.md
│   │   ├── risk-position.md
│   │   ├── debate-panel.md
│   │   ├── backtest.md
│   │   └── investors/
│   │       ├── buffett.md       munger.md       graham.md       lynch.md
│   │       └── fisher.md        wood.md         druckenmiller.md burry.md
│   ├── references/
│   │   ├── depth-framework.md
│   │   ├── report-template.md            # 内容 schema + Section Length Budget
│   │   ├── report-template.html          # HTML 结构 + 样式
│   │   ├── institutional-company-analysis-bilingual.md
│   │   ├── persona-skill-template.md
│   │   ├── strategy-registry.md
│   │   ├── persona-criteria-v1.md
│   │   ├── persona-criteria-v1.yaml
│   │   └── overfitting-checklist.md
│   └── scripts/
│       ├── data_provider.py
│       ├── fetch_price_charts.py
│       ├── backtest.py
│       └── web_prefetch_helper.md
├── docs/                                 # 跨平台说明
├── tools/                                # Claude.ai 网页端 zip 打包工具 (单 ZIP)
├── MIGRATION_PLAN.md                     # 18→1 合并设计文档
├── BACKTEST_DESIGN.md                    # backtest v1 设计文档
└── README.md / README.zh-CN.md
```

## 免责声明

本 skill 包产出研究分析,**不构成投资建议**。每份报告末尾都强制包含 `Not investment advice -- for your own research.`,这一行不可省略。
