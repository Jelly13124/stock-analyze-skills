# Institutional Company Analysis Logic / 机构级公司分析逻辑

Use this reference when `stock-company-fundamentals` is called directly, or when `stock-analysis` asks for a full SOP company fundamentals section.

本参考用于 `stock-company-fundamentals` 被单独调用，或 `stock-analysis` 生成完整标准流程报告时的公司基本面部分。

The structure is inspired by sell-side equity research report logic: begin with the investment question, explain the asset/business, then prove or disprove the thesis through business model, industry structure, competitive position, unit economics, valuation implications, and risks. Do not copy source report wording.

结构参考卖方股票研究报告的逻辑：先明确投资问题，再解释公司或资产本身，然后通过商业模式、行业结构、竞争位置、单位经济模型、估值含义和风险来证明或反驳投资论点。不要复制来源报告原文。

## Language Discipline / 语言规则

- Match the user's output language. If the user asks in Chinese, use Chinese headings and Chinese analysis.
- 保持用户语言一致。用户要求中文时，章节标题、表格字段、分析段落都用中文。
- Keep only unavoidable proper nouns, tickers, source names, accounting standards, and URLs in English.
- 只有不可避免的专有名词、股票代码、来源名称、会计准则和链接保留英文。
- On first use, translate key financial terms: for example, "average revenue per user / 单用户平均收入", "enterprise value / 企业价值".
- 关键术语首次出现时给出中英对照，之后优先使用中文。

## Report Logic / 报告逻辑

### 1. Investment Question / 投资问题

English:
- What is the one question the fundamental section must answer?
- Is the company misunderstood, underappreciated, overearning, underinvesting, or entering a new growth phase?
- What must be true for the stock to deserve a higher or lower multiple?

中文：
- 这家公司基本面分析最核心的问题是什么？
- 公司是否被市场误解、低估、处在高盈利周期、投入不足，或正在进入新的增长阶段？
- 哪些条件成立时，股票应该获得更高或更低估值？

Output requirement / 输出要求：
- State the core question in one sentence.
- 用一句话写清楚核心投资问题。

### 2. Asset And Business Overview / 资产与业务概览

English:
- Define the company or key asset.
- Explain segment mix, product/service lines, customers, geography, ownership, and contribution to the parent if relevant.
- Identify the asset that matters most to the stock.

中文：
- 定义公司或核心资产。
- 解释业务分部、产品或服务线、客户、地区、所有权结构，以及该资产对母公司的贡献。
- 找出真正驱动股价的关键资产或关键业务。

Required table / 必备表格：

| English Field | 中文字段 | What to include / 写什么 |
|---|---|---|
| Segment / Asset | 分部或资产 | Revenue, profit, strategic importance / 收入、利润、战略重要性 |
| Customer / User Base | 客户或用户基础 | Count, growth, quality, concentration / 数量、增长、质量、集中度 |
| Revenue Model | 收入模式 | Subscription, transaction, advertising, hardware, services, licensing / 订阅、交易、广告、硬件、服务、授权 |
| Geography | 地区 | Region exposure and geopolitical risk / 地区暴露和地缘风险 |
| Parent / Ownership | 母公司或所有权 | Hidden asset, minority stake, consolidation, spin-off relevance / 隐藏资产、少数股权、并表、分拆影响 |

### 3. Industry Structure And Market Context / 行业结构与市场背景

English:
- Size the addressable market only with dated sources.
- Explain demand drivers, adoption curve, pricing, regulation, distribution, and industry profitability.
- Separate cyclical growth from structural growth.

中文：
- 只有在有日期来源支持时才估算潜在市场空间。
- 解释需求驱动、渗透率曲线、价格、监管、渠道和行业盈利能力。
- 区分周期性增长和结构性增长。

Analytical lens / 分析角度：
- Market size / 市场空间
- Penetration and adoption / 渗透率与采用曲线
- Pricing power / 定价权
- Supply constraints / 供给约束
- Regulation and policy / 监管和政策
- Customer budget cycle / 客户预算周期

### 4. Business Model And Unit Economics / 商业模式与单位经济模型

English:
- Explain how the company makes money and what metric drives incremental profit.
- Identify volume, price, mix, churn, retention, utilization, take rate, advertising yield, margin, or content/product cost drivers.
- Show whether growth is profitable, subsidized, or investment-heavy.

中文：
- 解释公司如何赚钱，以及哪个指标驱动增量利润。
- 识别销量、价格、产品组合、流失率、留存率、产能利用率、抽成率、广告收益率、利润率、内容或产品成本等驱动因素。
- 判断增长是有利润的、靠补贴的，还是需要大量投入的。

Required table / 必备表格：

| Driver / 驱动因素 | Current Evidence / 当前证据 | Direction / 方向 | Margin Impact / 利润率影响 | Confidence / 置信度 |
|---|---|---|---|---|

### 5. Competitive Position And Moat / 竞争位置与护城河

English:
- Compare the company against direct competitors and substitutes.
- Identify why customers choose the company and why that advantage may persist or fade.
- Do not call something a moat unless it affects pricing power, customer retention, cost advantage, distribution, supply, or product differentiation.

中文：
- 将公司与直接竞争对手和替代品比较。
- 说明客户为什么选择这家公司，以及该优势为什么能持续或为什么会消失。
- 除非某项优势影响定价权、客户留存、成本优势、渠道、供给或产品差异化，否则不要轻易称为护城河。

Moat checklist / 护城河检查：
- Content / intellectual property / 内容或知识产权
- Scale / 规模
- Distribution / 渠道
- Switching costs / 转换成本
- Network effects / 网络效应
- Cost position / 成本位置
- Data advantage / 数据优势
- Regulatory or supply access / 监管或供给准入

### 6. Strategic Change And Catalysts / 战略变化与催化剂

English:
- Identify recent strategic decisions and why they change the thesis.
- Distinguish real catalysts from vague narratives.
- Explain expected timing and measurable proof points.

中文：
- 识别近期战略变化，并解释这些变化如何改变投资论点。
- 区分真实催化剂和模糊叙事。
- 写清楚催化剂的时间点和可验证指标。

Required table / 必备表格：

| Catalyst / 催化剂 | Timing / 时间 | Evidence / 证据 | What It Changes / 改变什么 | Monitor / 跟踪指标 |
|---|---|---|---|---|

### 7. Management, Capital Allocation, And Ownership / 管理层、资本配置与所有权

English:
- Evaluate execution record, incentives, balance sheet discipline, acquisitions, divestitures, buybacks, dividends, and hidden assets.
- If a key asset is minority-owned, unconsolidated, spun off, or embedded inside a parent company, explain who controls it and who captures value.

中文：
- 评估管理层执行记录、激励、资产负债表纪律、收购、剥离、回购、分红和隐藏资产。
- 如果关键资产是少数股权、未并表、分拆资产或嵌在母公司内部，必须解释谁控制资产、谁获得价值。

### 8. Financial Translation / 财务转化

English:
- Translate the qualitative thesis into revenue, margin, cash flow, and valuation drivers.
- Explain which financial line items should move if the thesis is correct.
- Tie business evidence to valuation assumptions.

中文：
- 把定性投资论点转化为收入、利润率、现金流和估值驱动因素。
- 说明如果论点正确，哪些财务项目应该改善。
- 把业务证据连接到估值假设。

Required table / 必备表格：

| Thesis Driver / 论点驱动 | Financial Line / 财务项目 | Expected Direction / 预期方向 | Valuation Implication / 估值含义 |
|---|---|---|---|

### 9. Risks, Thesis Breakers, And Variant View / 风险、论点破坏条件与差异化观点

English:
- List what would prove the thesis wrong.
- Separate execution risk, market risk, competitive risk, regulatory risk, financial risk, and valuation risk.
- State what the market may already believe and what your analysis says differently.

中文：
- 列出哪些事实会证明投资论点错误。
- 区分执行风险、市场风险、竞争风险、监管风险、财务风险和估值风险。
- 说明市场可能已经相信什么，以及本分析的差异化观点在哪里。

Required table / 必备表格：

| Risk / 风险 | Evidence To Monitor / 跟踪证据 | Impact / 影响 | Mitigant / 缓释因素 | Thesis Breaker? / 是否破坏论点 |
|---|---|---|---|---|

## Standalone Output Schema / 单独调用输出结构

Use this structure for standalone `stock-company-fundamentals` reports. Translate headings fully into the user's language.

单独调用 `stock-company-fundamentals` 时使用以下结构。标题必须完全翻译成用户语言。

1. Fundamental Verdict / 基本面结论
2. Investment Question / 投资问题
3. Asset And Business Overview / 资产与业务概览
4. Industry Structure And Market Context / 行业结构与市场背景
5. Business Model And Unit Economics / 商业模式与单位经济模型
6. Competitive Position And Moat / 竞争位置与护城河
7. Strategic Change And Catalysts / 战略变化与催化剂
8. Management, Capital Allocation, And Ownership / 管理层、资本配置与所有权
9. Financial Translation / 财务转化
10. Risks, Thesis Breakers, And Variant View / 风险、论点破坏条件与差异化观点
11. Implication For Valuation And Strategy / 对估值和策略的含义
12. Evidence Gaps / 证据缺口

## Full SOP Company Section Gate / 完整报告公司章节门槛

For a full SOP report, the company fundamentals section is incomplete unless it includes:

完整标准流程报告中，公司基本面部分必须包含：

- Core investment question / 核心投资问题
- Business and segment map / 业务与分部图谱
- Revenue model and unit economics / 收入模式与单位经济模型
- Industry structure / 行业结构
- Competitive position and substitutes / 竞争位置与替代品
- Strategic changes and catalysts / 战略变化与催化剂
- Management and capital allocation / 管理层与资本配置
- Financial translation into revenue, margin, cash flow, and valuation assumptions / 对收入、利润率、现金流和估值假设的财务转化
- Thesis breakers and variant view / 论点破坏条件与差异化观点
- Evidence gaps and confidence / 证据缺口与置信度
