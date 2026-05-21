# Debate Panel Module

> Internal module of the orchestrator. Loaded on demand by the
> orchestrator when the report needs this section, or when the user
> invokes it directly.
>
> Originally shipped as the standalone skill `stock-debate-panel` (pre-2026-05-merge).


## Overview

Run a structured investment-committee debate after the evidence layer is complete. Use this for full-depth stock reports or whenever the user explicitly asks for multi-agent debate, bull/bear debate, or investment committee review.

**Real multi-subagent debate is the default behavior in Claude Code.** When the `Agent` tool is available, the panel orchestrator MUST dispatch one independent subagent per role per round so that each role's reasoning is genuinely independent rather than the same LLM modelling multiple voices. The single-LLM sequential mode is a labeled fallback for environments without the Agent tool — see `Single-LLM Fallback` below.

## Request Gate

**Two things are settled before the panel runs; this module never asks the user *which* personas to use.**

1. **Persona mode (on/off)** — set by item (4) of the `stock-analysis` Request Gate. *On* (the default): the Bull/Bear slots are filled by investor personas, which Claude auto-selects from the ticker profile (Persona Selection Table in `stock-analysis/SKILL.md` plus the swap table below). *Off*: run the debate with generic Bull / Bear / Quant / Risk / Moderator roles and load no persona module.
2. **Round count** — auto-defaulted (see Round options below): 2 rounds for `full SOP`, 1 for direct standalone invocations.

- **Invoked by the orchestrator for a `full SOP` report** — use the persona mode passed from the gate, the auto-selected roster (if persona mode is on), and 2 rounds. Ask nothing.
- **Invoked directly / standalone by the user** — assume persona mode on and auto-select the roster; only if the round count is unclear, ask one short question: `Debate rounds: 1 (independent theses), 2 (adds a challenge round — default), or 3 (adds a confidence-revision round)?`
- **User named personas explicitly** ("Buffett vs Wood") — honor that roster exactly (implies persona mode on).

Never ask the user to pick the personas; when persona mode is on, Claude always selects the matchup itself.

### Round options

- **1 round** — each persona writes an independent thesis once. Moderator synthesizes. Lightest token cost; useful for quick committee read.
- **2 rounds** — adds a challenge round. Every persona must rebut at least two specific claims from other personas, citing them by name. Default for `full SOP`.
- **3 rounds** — adds a confidence-revision round. Each persona restates confidence after seeing all challenges and lists what evidence would flip them. Use when conviction calibration matters (large position sizing, contested thesis).

If the user does not specify, default to 2 rounds for `full SOP` reports and 1 round for direct standalone invocations.

### Persona options

Default roles: Bull / Bear / Quant / Risk / Moderator (5 roles). Claude **auto-selects** which persona fills each Bull/Bear slot — see "Auto-selecting the roster" below.

Acceptable substitutions for the Bull and Bear slots from the persona skill suite:

| Slot | Persona swaps |
|---|---|
| Bull | `modules/investors/wood.md` (disruptive growth), `modules/investors/druckenmiller.md` (macro tailwind growth), `modules/investors/lynch.md` (GARP), `modules/investors/fisher.md` (long-term quality growth) |
| Bear | `modules/investors/burry.md` (deep-value short-side discipline), `modules/investors/graham.md` (defensive quantitative), `modules/investors/buffett.md` (when valuation is stretched), `modules/investors/munger.md` (when business quality is questionable) |
| Quant | usually unchanged — generic quant role; no ai-hedge-fund-style quant persona in the suite |
| Risk Manager | usually unchanged |
| Moderator | usually unchanged, or `modules/investors/munger.md` for opinionated synthesis |

Other patterns the user may request:

- **All-persona panel** — replace generic Bull/Bear with two persona pairs (e.g. Buffett vs Wood + Burry vs Lynch + Munger as moderator). 5+ subagents per round.
- **Concentrated head-to-head** — only two personas (e.g. Wood vs Burry on TSLA), no Quant/Risk/Moderator. Useful for binary-thesis stocks.

### Auto-selecting the roster

**When persona mode is on**, Claude picks the roster itself, without asking the user:

- Fill the Bull and Bear slots with investor personas chosen via the Persona Selection Table in `stock-analysis/SKILL.md`: a Bull-side persona (growth / quality lens) and a Bear-side persona (value / skeptic lens) that create genuine tension — e.g. a disruptive-growth name → Wood (Bull) vs Burry (Bear); a mature compounder → Buffett (Bull-side quality) vs Graham (Bear-side value discipline); a macro-cyclical → Druckenmiller (Bull) vs Munger (Bear).
- If the ticker profile is ambiguous, still pick two contrasting personas rather than falling back to generic roles — the user opted into persona debate.
- Keep Quant / Risk / Moderator as generic roles unless the user asks otherwise.
- Only deviate from auto-selection when the user explicitly names personas.

**When persona mode is off**, use generic Bull / Bear / Quant / Risk / Moderator for all five roles and load no persona module.

## Subagent Dispatch Protocol

When the `Agent` tool is available (Claude Code), the orchestrator MUST follow this protocol. **Do not paraphrase, simulate, or sequentially write all roles in a single LLM call when the Agent tool is available** — that defeats the purpose of the panel.

### Round 1 dispatch

In a SINGLE message, issue N parallel `Agent` tool calls (one per persona slot). Use `subagent_type: "general-purpose"`. Each subagent prompt must include:

1. The persona content the subagent will adopt — for persona slots, **copy the full content of the relevant `modules/investors/<persona>.md` file inline into the prompt**, do not rely on the subagent discovering the file on its own
2. The full evidence ledger (macro, sector, fundamentals, financials, valuation, technical, sentiment, risk outputs) with source dates
3. The user objective, horizon, and any user-specified constraints
4. The exact output contract for debate participation (compact thesis paragraph + scoring breakdown + conviction band, NOT the full Standalone Markdown Report Mode)

Template:

```
Agent({
  description: "<Role name>: independent Round 1 thesis on <TICKER>",
  subagent_type: "general-purpose",
  prompt: `
You are participating in an investment committee debate for <TICKER>.

Your role this round: <Role name, e.g. "Bull Analyst" or "Buffett persona">.

<For persona slots:>
You MUST adopt the following investor lens. Stay in this persona for the
entire response. Do NOT write a balanced or neutral analyst voice.

--- BEGIN PERSONA SKILL CONTENT ---
<full content of modules/investors/<persona>.md, inline>
--- END PERSONA SKILL CONTENT ---

<For generic slots:>
You are the <Role>. Build the strongest <upside | downside | quant | risk>
case using only the cited evidence below. Do not invent facts.

EVIDENCE LEDGER:
<full ledger with dates>

USER OBJECTIVE: <objective>
HORIZON: <horizon>

OUTPUT (return exactly this structure):
1. One-paragraph thesis (200-400 words) in your role's voice
2. Scoring breakdown table (per the persona's framework, or 1-5 confidence
   for generic roles)
3. Conviction band (90-100 / 70-89 / 50-69 / 30-49 / 0-29)
4. Top 3 evidence items that drove the call, with dates

Do NOT include the Standalone Markdown Report Mode sections; this is
debate participation output only.
  `.trim()
})
```

### Round 2 dispatch (if 2+ rounds)

After Round 1 completes, the orchestrator dispatches N more parallel subagents. Each Round 2 prompt must additionally include the **verbatim Round 1 output of all OTHER personas** so that the subagent can rebut specific claims:

```
ADDITIONAL CONTEXT FOR ROUND 2:
The other personas wrote the following in Round 1. You must rebut at
least two specific claims, naming the persona and quoting the claim.

--- BEGIN OTHER PERSONAS' ROUND 1 ---
<verbatim concatenation of every other persona's Round 1 output>
--- END OTHER PERSONAS' ROUND 1 ---

OUTPUT FOR ROUND 2:
1. Two or more challenge points, each in the format:
   "<Other persona> claimed: '<quote>'. I disagree because <reason with
   evidence>." OR "I partially accept, with this qualification: <...>."
2. Updated thesis paragraph reflecting any concessions
3. Updated conviction band (may be unchanged)
```

### Round 3 dispatch (if 3 rounds)

Round 3 is conviction revision. Each subagent receives all Round 1 AND Round 2 transcripts and produces:

```
1. Confidence revision: <new conviction band> with one-sentence reason
2. Falsifiers: 2-4 specific evidence items that would flip this call
   (e.g. "EPS revisions turning negative for two consecutive quarters",
   "10-year yield breaking 5.5%", "FCF conversion dropping below 60%")
```

### Moderator synthesis

After all rounds complete, dispatch ONE moderator subagent (or perform synthesis in the main orchestrator if quality is sufficient). The moderator subagent receives the full transcript of all rounds from all personas and produces:

- Agreed facts (what survived all rebuttal)
- Unresolved disputes (what each side stuck to)
- Bear / Base / Bull target range with assumed scenario probabilities
- Short-term strategy implication
- Medium-term strategy implication
- Invalidation points (the falsifiers consolidated across personas)
- Rejected arguments and why

Recommend Opus for the moderator subagent when synthesis quality matters; default `general-purpose` (which selects an appropriate model) is fine for analysts.

## Single-LLM Fallback

When the `Agent` tool is NOT available (some non-Claude-Code surfaces, or when the panel is invoked from inside a subagent which itself cannot dispatch further subagents), the orchestrator runs all roles in one LLM call sequentially.

When this fallback is used, the output transcript MUST begin with this label:

> **Mode: single-LLM simulation (Agent tool not available). Reasoning chains are not independent. Treat conviction values as soft.**

This labeling is mandatory so users understand what they're reading is one model voicing multiple roles, not a real committee.

## Standalone Markdown Report Mode

When called directly by a user (not via `stock-analysis`), produce a self-contained Markdown debate appendix in the user's language. If ticker, evidence base, target horizon, or objective is unclear, ask one concise clarification first (combined with the Request Gate above).

Use this structure (sections used scale with the round count):

1. `## Debate Setup And Evidence Base` — including round count chosen and persona roster
2. `## Round 1: Independent Theses` — one subsection per persona with their full Round 1 output
3. `## Round 2: Challenges` — present only if 2+ rounds
4. `## Round 3: Revised Confidence` — present only if 3 rounds
5. `## Moderator Synthesis`
6. `## Rejected Arguments`
7. `## Monitoring Checklist` — the consolidated falsifiers

For full-depth requests, do not run a superficial bull/bear bullet list; use the real subagent protocol above.

## Data Failure and Low-Confidence Rules

- Do not run a high-confidence debate on an empty or stale evidence base.
- If one evidence module is missing, include that absence as a debate item and reduce confidence for affected roles.
- If source dates conflict, the moderator must state which evidence was accepted, rejected, or left unresolved.
- If valuation, financials, or technical data is insufficient, the moderator must avoid actionable conclusions and list required follow-up data.
- If the user requested investor personas but evidence is too thin for that persona's framework (e.g. Buffett requires 5-10 year operating history; Wood requires R&D and growth visibility), state the gap and either swap to a generic role or proceed with a low-confidence flag.

## Required Output Elements

Every standalone report or main-report section must include: a conclusion, source dates, at least one key table when evidence exists, bullish interpretation, bearish interpretation, uncertain/missing evidence, implications for valuation/strategy/risk, and missing data.

## Required Inputs

- Macro, sector, fundamentals, financial statements, valuation, technical, sentiment, and risk outputs.
- Evidence ledger with source dates.
- User objective and time horizon. Round count is auto-defaulted (2 for `full SOP`) and the persona roster is auto-selected — neither is asked of the user unless they raise it.
- Current price and valuation targets if available.

Do not run debate on an empty evidence base. If evidence is missing, ask for data collection or state that the debate is low confidence.

## Roles

| Role | Mandate | Persona swap allowed |
|---|---|---|
| Bull Analyst | Build the strongest upside thesis and identify catalysts | Yes (Wood / Druckenmiller / Lynch / Fisher) |
| Bear Analyst | Build the strongest downside thesis and identify invalidation risks | Yes (Burry / Graham / Buffett / Munger) |
| Quant Analyst | Check valuation math, factor exposure, trend, revisions, and statistical consistency | Usually no (no quant persona in suite) |
| Risk Manager | Stress-test position sizing, downside, liquidity, event risk, and stop logic | Usually no |
| Moderator | Reconcile views into target ranges, strategy, confidence, and open questions | Optional Munger swap |

## Output Contract

Return a Markdown report or report section with:

- mode label (real multi-subagent / single-LLM simulation)
- compact debate transcript or appendix per round
- confidence score by role and per round
- strongest bull and bear evidence
- rejected arguments and why
- moderator conclusion with bear/base/bull range
- consolidated monitoring checklist (the falsifiers)
- standalone disclaimer when called directly: `Not investment advice -- for your own research.`
