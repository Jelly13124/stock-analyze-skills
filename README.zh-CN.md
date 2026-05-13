<div align="right">

[English](README.md) · **中文**

</div>

# 股票分析 Skill 包 (Stock Analyze Skills)

![Skills](https://img.shields.io/badge/skills-18-blue)
![Personas](https://img.shields.io/badge/investor%20personas-8-success)
![Multi-Subagent Debate](https://img.shields.io/badge/debate-real%20multi--subagent-orange)
![Platforms](https://img.shields.io/badge/platforms-Claude%20Code%20·%20Desktop%20·%20Codex%20·%20Web-purple)
![Last Commit](https://img.shields.io/github/last-commit/Jelly13124/stock-analyze-skills)

一套机构级股票研究的可组合 Skill 工具集,把多步分析师 SOP 翻译成 Markdown 提示词文件 — 含显式数值阈值、真实多 subagent 辩论、以及 8 位可直接对话的投资大师人格。

支持 Claude Code、Claude Desktop、Codex,以及 Claude.ai 网页端 (需要额外打包 zip)。

## 最近更新 (2026-05)

- **8 个投资大师人格 skill** — Buffett · Munger · Graham · Lynch · Fisher · Wood · Druckenmiller · Burry。可单独激活,以该大师视角对话;也可在辩论环节中替换通用 Bull / Bear 角色。
- **真实多 subagent 辩论** — `stock-debate-panel` 现在在 Claude Code 中会**真正**派遣并行 `Agent` 工具调用,每个角色每轮一个独立 subagent。调用时询问辩论轮数 (1 / 2 / 3) 和参与人格列表。仅在 Agent tool 不可用时降级为单 LLM 顺序模式,且必须在 transcript 头部明确标注。
- **新增 `stock-sentiment-analysis`** — 4 通道情绪分析: insider 交易 (20%) + news flow (25%) + 分析师 EPS revision (35%) + short interest / 期权定位 (20%)。
- **量化层加在财报 / 技术 / 估值 / 风险 4 个 skill** — 显式数值阈值 (ROE > 15%、P/B < 1.5、FCF yield ≥ 15%、ADX、Z-score、Owner Earnings、波动率调整仓位上限等) **叠加在**已有的定性框架之上,不替换。

## Skill 列表

### 分析类 Skill (10 个)

| Skill | 用途 |
|---|---|
| `stock-analysis` | 主调度。按报告深度 (basic / standard / full SOP) 路由,调用各子 skill,生成最终 Markdown 或 DOCX 报告。 |
| `stock-macro-analysis` | 宏观环境: 美联储、利率、收益率曲线、CPI、就业、VIX、流动性。 |
| `stock-sector-analysis` | 行业 / GICS / 同业对比、行业 ETF 强度。 |
| `stock-company-fundamentals` | 商业模式、护城河、TAM、定价权、管理层、资本配置。 |
| `stock-financial-statement-analysis` | 10-K / 10-Q、三大报表、盈利质量 + 新增的 Quantitative Quick Filters。 |
| `stock-valuation-analysis` | 相对估值 + 内在估值,DCF、Owner Earnings、Residual Income、WACC 参考表、情景概率加权。 |
| `stock-technical-analysis` | 多时间框架趋势、RSI / KDJ / MACD / BB / ATR / OBV + 新增 4 策略量化层 (趋势 / 动量 / 均值回归 / 波动率制度)。 |
| `stock-sentiment-analysis` | Insider 交易、新闻流、分析师 EPS 修正、空头利息、期权定位。 |
| `stock-risk-position-analysis` | 仓位、止损逻辑、R:R、行业上限、波动率调整的单股 cap。 |
| `stock-debate-panel` | 真实多 subagent 投资委员会辩论 (1 / 2 / 3 轮)。 |

### 投资大师人格 Skill (8 个)

| Skill | 思维框架 |
|---|---|
| `stock-investor-buffett` | 护城河 + 股东盈余 + 安全边际 + 能力圈。 |
| `stock-investor-munger` | ROIC + 资本配置 + 业务可预测性 + 品质优先于价格。 |
| `stock-investor-graham` | Net-Net + Graham number + 股息记录 + 防守型投资者测试。 |
| `stock-investor-lynch` | GARP + PEG ≤ 1 + 6 类公司分类 + 投资你了解的。 |
| `stock-investor-fisher` | 15 点清单 + scuttlebutt + R&D 强度 + 管理层深度。 |
| `stock-investor-wood` | 破坏式创新 + R&D > 15% + 5 年指数模型 + 25x 终值倍数。 |
| `stock-investor-druckenmiller` | 宏观优先 + 集中持仓 + 不对称风险回报 + 动量叠加。 |
| `stock-investor-burry` | 深度价值 + FCF yield ≥ 15% + EV/EBIT < 6 + 逆向布局。 |

每个人格都有显式的 `Conflict And Pass Rules` — Buffett 拒绝评价 pre-profit 生物科技股**是正确行为**,不是分析失败。各人格的评分权重和阈值参考 `virattt/ai-hedge-fund/src/agents/<persona>.py`,翻译成 SKILL.md 提示词形式。

## 与 ai-hedge-fund 的差异

| 维度 | 本仓库 (Skill 体系) | virattt/ai-hedge-fund |
|---|---|---|
| 形式 | Markdown SKILL.md 提示词 | Python + LangGraph 框架 |
| 自定义 | 改一个提示词文件 | 改代码 + 改框架 |
| 数据缺失处理 | 内置 Data Health 门禁与降级规则 | 字段缺失会崩 |
| 定性 + 定量 | 双轨叠加 (定性权威, 定量做过滤) | 仅定量 |
| 人格驱动辩论 | 是 — Claude Code 原生 Agent tool 派每个 persona 为独立 subagent | 是 — LangGraph nodes |
| 回测 | 暂无 (规划中) | 有 |
| 接入成本 | `git clone` + 拷贝目录 | `pip install` + LLM API key + 数据 API key |
| 输出形式 | 专业级 Markdown / DOCX 报告 | JSON 信号 + reasoning |

两个项目解决不同问题。ai-hedge-fund 是可编程的对冲基金模拟器。本仓库是分析师的提示词库,产出报告级输出,数据不全时也能继续工作。

## 快速安装

```powershell
git clone https://github.com/Jelly13124/stock-analyze-skills.git
cd stock-analyze-skills
```

### Claude Code

```powershell
Copy-Item .\stock-* "$env:USERPROFILE\.claude\skills\" -Recurse -Force
```

### Codex

```powershell
Copy-Item .\stock-* "$env:USERPROFILE\.codex\skills\" -Recurse -Force
```

### Claude Desktop

在 Skills 页面里把所有 `stock-*` 文件夹都导入。最少导入 `stock-analysis`;要 full SOP 报告就导入全部分析子 skill;要 persona 对话或 persona 辩论再导入 `stock-investor-*` 文件夹。

### Claude.ai 网页端

先打包 zip:

```powershell
.\tools\build_claude_zips.ps1
```

然后在 Skills UI 上传。详细跨平台说明见 `docs/CROSS_PLATFORM.md`。

## API Key 配置

在 repo 根目录创建 `key.txt`:

```text
FINNHUB_API_KEY=your_finnhub_key
ALPHA_VANTAGE_API_KEY=your_alpha_vantage_key
FRED_API_KEY=your_fred_key
```

| Key | 用途 | 是否必需 |
|---|---|---|
| `FINNHUB_API_KEY` | 报价和部分盘中数据 | 推荐 |
| `ALPHA_VANTAGE_API_KEY` | 日线 / 周线历史 OHLCV | 推荐 |
| `FRED_API_KEY` | 宏观数据 (利率、VIX、信用利差) | 可选 |

Yahoo 盘中 K 线不需要任何 key — 数据脚本默认用 Yahoo 作为盘中数据源。

冒烟测试:

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

### 模式 1 — 完整 SOP 报告

```text
/stock-analysis NFLX full SOP md 盘中 目标价 / 短线交易 / 中期策略 / 长期投资 / 财报分析
```

主调度收集证据,按顺序调用每个子 skill,组装成单份 Markdown / DOCX 报告。

### 模式 2 — 单独调用子 skill

```text
/stock-valuation-analysis NFLX full 目标价
/stock-technical-analysis NFLX 盘中 5m KDJ RSI
/stock-sentiment-analysis NFLX 30 天窗口
/stock-company-fundamentals NFLX full 公司基本面
```

### 模式 3 — 大师人格对话 (新)

```text
/stock-investor-buffett
> 你怎么看 NVDA 现在的价格?
```

整个对话以该大师视角进行。Buffett 会拒绝评价能力圈外的名字,Wood 会嫌弃成熟分红股不值得投资 — 这是设计本意。

### 模式 4 — 真实多 subagent 辩论 (新)

```text
/stock-debate-panel
```

辩论面板会通过 Request Gate 询问两件事:

1. **轮数** — 1 (只独立写论点) / 2 (加反驳) / 3 (加置信度修订)
2. **人格列表** — 默认 = 通用 Bull / Bear / Quant / Risk / Moderator;或指定大师替换,例如 "Buffett vs Wood + 标准 Quant / Risk / Moderator"

在 Claude Code 中,每个角色都作为独立的并行 `Agent` subagent 派遣 — 而不是同一个 LLM 演多个角色。

## 报告深度

| Depth | 适用场景 | 输出 |
|---|---|---|
| `basic` | 快速一瞥、初判 | Data Health、价格快照、估值快照、关键风险 |
| `standard` | 常规研究请求 | 宏观 / 行业 / 基本面 / 财报 / 估值 / 技术 / 情绪 / 风险计划 + bear/base/bull 区间 |
| `full SOP` | 机构级报告或明确"完整"请求 | 完整 7 步 SOP + 证据账本 + DCF / 情景计算 + 图表 + 评分 + 事件风险 + 真实多 subagent 辩论 (1-3 轮) |

如果用户只输入裸 ticker,主 skill 会先追问报告深度、输出格式、目标和技术窗口,再开始生成。

## 仓库结构

```text
stock-analyze-skills/
├── stock-analysis/                       # 主调度
├── stock-macro-analysis/
├── stock-sector-analysis/
├── stock-company-fundamentals/
├── stock-financial-statement-analysis/
├── stock-valuation-analysis/
├── stock-technical-analysis/
├── stock-sentiment-analysis/             # 新 (2026-05)
├── stock-risk-position-analysis/
├── stock-debate-panel/                   # 已升级为真实多 subagent
├── stock-investor-buffett/               # 新人格 skill (2026-05)
│   └── references/persona-skill-template.md   # 共用结构模板
├── stock-investor-munger/
├── stock-investor-graham/
├── stock-investor-lynch/
├── stock-investor-fisher/
├── stock-investor-wood/
├── stock-investor-druckenmiller/
├── stock-investor-burry/
├── docs/                                 # 跨平台说明
├── tools/                                # Claude.ai 网页端 zip 打包工具
└── README.md / README.zh-CN.md
```

## 免责声明

本 skill 包产出研究分析,**不构成投资建议**。每份报告末尾都强制包含 `Not investment advice -- for your own research.`,这一行不可省略。
