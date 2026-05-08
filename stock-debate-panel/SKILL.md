---
name: stock-debate-panel
description: Use when stock analysis needs bull/bear debate, quant review, risk-manager review, thesis challenge, confidence calibration, or investment committee synthesis.
---

# Stock Debate Panel

## Overview

Run a structured debate after the evidence layer is complete. Use this for full-depth stock reports or whenever the user explicitly asks for multi-agent debate, bull/bear debate, or investment committee review.

Respect the active environment's tool policy. If true subagents are available and permitted, assign each role separately. If not, run the roles sequentially in one agent while keeping their reasoning independent and evidence-based.

## Standalone Markdown Report Mode

When called directly by a user, produce a self-contained Markdown debate appendix in the user's language. If ticker, evidence base, target horizon, or objective is unclear, ask one concise clarification or state that the debate is low-confidence because evidence is missing.

Use this structure:

1. `## Debate Setup And Evidence Base`
2. `## Round 1: Independent Theses`
3. `## Round 2: Challenges`
4. `## Round 3: Revised Confidence`
5. `## Moderator Synthesis`
6. `## Rejected Arguments`
7. `## Monitoring Checklist`

For full-depth requests, include 2-3 rounds and confidence by role. Do not run a superficial bull/bear list when a full debate is requested.

## Data Failure and Low-Confidence Rules

- Do not run a high-confidence debate on an empty or stale evidence base.
- If one evidence module is missing, include that absence as a debate item and reduce confidence for affected roles.
- If source dates conflict, the moderator must state which evidence was accepted, rejected, or left unresolved.
- If valuation, financials, or technical data is insufficient, the moderator must avoid actionable conclusions and list required follow-up data.

## Required Output Elements

Every standalone report or main-report section must include a conclusion, source dates, at least one key table when evidence exists, bullish interpretation, bearish interpretation, uncertain/missing evidence, implications for valuation/strategy/risk, and missing data.

## Required Inputs

- Macro, sector, fundamentals, financial statements, valuation, technical, and risk outputs.
- Evidence ledger with source dates.
- User objective and time horizon.
- Current price and valuation targets if available.

Do not run debate on an empty evidence base. If evidence is missing, ask for data collection or state that the debate is low confidence.

## Roles

| Role | Mandate |
|---|---|
| Bull Analyst | Build the strongest upside thesis and identify catalysts |
| Bear Analyst | Build the strongest downside thesis and identify invalidation risks |
| Quant Analyst | Check valuation math, factor exposure, trend, revisions, and statistical consistency |
| Risk Manager | Stress-test position sizing, downside, liquidity, event risk, and stop logic |
| Moderator | Reconcile views into target ranges, strategy, confidence, and open questions |

## Debate Rounds

1. Round 1: each role writes an independent thesis using only cited evidence.
2. Round 2: each role challenges at least two claims from other roles.
3. Round 3: each role revises confidence and lists what evidence would change the view.
4. Moderator synthesis:
   - agreed facts
   - unresolved disputes
   - bear/base/bull target range
   - short-term strategy
   - medium-term strategy
   - invalidation points

## Output Contract

Return a Markdown report or report section with:

- compact debate transcript or appendix
- confidence score by role
- strongest bull and bear evidence
- rejected arguments and why
- moderator conclusion
- exact items that need monitoring after the report
- standalone disclaimer when called directly: `Not investment advice -- for your own research.`
