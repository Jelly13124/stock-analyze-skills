# Migration Plan: 18 Skills → 1 Skill (Router + On-Demand Read)

**Status:** Draft for review. No files will be moved or rewritten until you approve.

**Goal:** Collapse the current 18-skill suite into a single `stock-analysis` skill, while preserving the ability to invoke any individual analytical module or investor persona by name. Installation becomes one ZIP / one folder copy.

**Pattern:** Top-level `SKILL.md` is a small router that lazily `Read`s sub-module files only when needed. Modeled on the "superpower" / Anthropic-skill pattern.

---

## 1. Before / After File Map

### 1.1 Top-level layout

| Before | After | Action |
|---|---|---|
| `stock-analysis/` (orchestrator skill) | `stock-analysis/` (single suite skill) | **Keep**, rewrite `SKILL.md`, add `modules/` |
| `stock-macro-analysis/` | `stock-analysis/modules/macro.md` + `_legacy/stock-macro-analysis/` | Move content into module; archive original |
| `stock-sector-analysis/` | `stock-analysis/modules/sector.md` + `_legacy/...` | Same |
| `stock-company-fundamentals/` | `stock-analysis/modules/company-fundamentals.md` + `_legacy/...` | Same |
| `stock-financial-statement-analysis/` | `stock-analysis/modules/financial-statements.md` + `_legacy/...` | Same |
| `stock-valuation-analysis/` | `stock-analysis/modules/valuation.md` + `_legacy/...` | Same |
| `stock-technical-analysis/` | `stock-analysis/modules/technical.md` + `_legacy/...` | Same |
| `stock-sentiment-analysis/` | `stock-analysis/modules/sentiment.md` + `_legacy/...` | Same |
| `stock-risk-position-analysis/` | `stock-analysis/modules/risk-position.md` + `_legacy/...` | Same |
| `stock-debate-panel/` | `stock-analysis/modules/debate-panel.md` + `_legacy/...` | Same |
| `stock-investor-buffett/` | `stock-analysis/modules/investors/buffett.md` + `_legacy/...` | Same |
| `stock-investor-munger/` | `stock-analysis/modules/investors/munger.md` + `_legacy/...` | Same |
| `stock-investor-graham/` | `stock-analysis/modules/investors/graham.md` + `_legacy/...` | Same |
| `stock-investor-lynch/` | `stock-analysis/modules/investors/lynch.md` + `_legacy/...` | Same |
| `stock-investor-fisher/` | `stock-analysis/modules/investors/fisher.md` + `_legacy/...` | Same |
| `stock-investor-wood/` | `stock-analysis/modules/investors/wood.md` + `_legacy/...` | Same |
| `stock-investor-druckenmiller/` | `stock-analysis/modules/investors/druckenmiller.md` + `_legacy/...` | Same |
| `stock-investor-burry/` | `stock-analysis/modules/investors/burry.md` + `_legacy/...` | Same |

### 1.2 Shared assets that need consolidating

| Before | After | Action |
|---|---|---|
| `stock-company-fundamentals/references/institutional-company-analysis-bilingual.md` | `stock-analysis/references/institutional-company-analysis-bilingual.md` | Move (single canonical copy) |
| `stock-investor-buffett/references/persona-skill-template.md` | `stock-analysis/references/persona-skill-template.md` | Move (shared by all 8 personas) |
| `stock-analysis/references/Stock_Analysis_SOP_v1.0.md` | unchanged | Keep |
| `stock-analysis/references/depth-framework.md` | unchanged | Keep |
| `stock-analysis/references/report-template.md` | unchanged | Keep |
| `stock-analysis/scripts/fetch_price_charts.py` | unchanged | Keep |
| `stock-analysis/scripts/data_provider.py` | unchanged | Keep |
| `stock-analysis/scripts/web_prefetch_helper.md` | unchanged | Keep |

### 1.3 Codex `agents/openai.yaml` files

Every sub-skill currently ships an `agents/openai.yaml` that registers a Codex slash-command (`/stock-investor-buffett`, etc.). After the merge there is only one entry point.

**Recommended:** keep only `stock-analysis/agents/openai.yaml` and update its `default_prompt` to teach users they can append a persona / module name as an argument. The 17 sub-skill yamls go to `_legacy/` along with the rest of each folder.

**Trade-off:** Codex users lose the direct `/stock-investor-buffett` slash command. They would type `/stock-analysis buffett's lens on NVDA` instead. (The same logical behavior, one extra clarifying word.)

### 1.4 Final tree

```
stock-analysis/
├── SKILL.md                                   ← rewritten (router + SOP)
├── agents/
│   └── openai.yaml                            ← updated default_prompt
├── modules/
│   ├── macro.md
│   ├── sector.md
│   ├── company-fundamentals.md
│   ├── financial-statements.md
│   ├── valuation.md
│   ├── technical.md
│   ├── sentiment.md
│   ├── risk-position.md
│   ├── debate-panel.md
│   └── investors/
│       ├── buffett.md
│       ├── munger.md
│       ├── graham.md
│       ├── lynch.md
│       ├── fisher.md
│       ├── wood.md
│       ├── druckenmiller.md
│       └── burry.md
├── references/
│   ├── Stock_Analysis_SOP_v1.0.md             (existing)
│   ├── depth-framework.md                     (existing)
│   ├── report-template.md                     (existing)
│   ├── institutional-company-analysis-bilingual.md  (moved here)
│   └── persona-skill-template.md              (moved here)
└── scripts/
    ├── fetch_price_charts.py
    ├── data_provider.py
    └── web_prefetch_helper.md

_legacy/                                       ← archived backups
├── stock-macro-analysis/
├── stock-sector-analysis/
├── ...                                        (all 17 original folders)
└── README.md                                  ← note explaining rollback

docs/CROSS_PLATFORM.md                         ← updated (single-zip flow)
tools/build_claude_zips.ps1                    ← simplified (one zip)
README.md                                      ← updated (one-skill install)
README.zh-CN.md                                ← updated
```

---

## 2. Per-Module Edit Rule

Every module file (e.g. `modules/macro.md`) is the **body** of the corresponding old `SKILL.md` with the frontmatter stripped. Concretely:

**Before** (`stock-macro-analysis/SKILL.md`):
```markdown
---
name: stock-macro-analysis
description: Use when stock or ETF analysis needs macro regime, Fed policy, rates, ...
---

# Stock Macro Analysis

## Overview
...
```

**After** (`stock-analysis/modules/macro.md`):
```markdown
# Macro Module

> Internal module of stock-analysis. Loaded on demand by the orchestrator
> when the report requires a macro section, or when the user asks for a
> macro-only sub-report.

## Overview
...
```

Mechanical edits per file:
1. Delete the `---...---` YAML frontmatter block.
2. Replace `# Stock <X> Analysis` with `# <X> Module`.
3. Add the two-line "Internal module of stock-analysis" banner.
4. Find/replace internal references: `the main stock-analysis skill` → `the orchestrator (this skill's SKILL.md)`; `If the main \`stock-analysis\` skill is active` → `When invoked by the orchestrator`.
5. Find/replace skill cross-references: `the \`stock-debate-panel\` skill` → `\`modules/debate-panel.md\``, etc.

The actual analytical content (Standalone Markdown Report Mode, Procedure, Required Output Elements, Conflict And Pass Rules for personas, Subagent Dispatch Protocol for debate, etc.) is **preserved verbatim**. The Sub-Skill Contract becomes the Module Contract; the wording inside it is unchanged because the contract still applies — modules still return a Markdown section with conclusion, dates, table, bull/bear/neutral, and missing data when invoked.

---

## 3. New Top-Level `stock-analysis/SKILL.md` (Full Draft)

This is the file the user will review most carefully. Annotated with `<!-- NOTE -->` comments where behavior changes.

````markdown
---
name: stock-analysis
description: Use when analyzing stocks, ETFs, tickers, target prices, trade strategy, valuation, DCF, technicals, KDJ/RSI/MACD/Bollinger Bands, support/resistance, breakout, earnings, 10-K/10-Q, fundamentals, sector/peer comparison, macro regime, sentiment, position sizing, stop loss, bull/bear debate, investment committee review, investor personas (Buffett/Munger/Graham/Lynch/Fisher/Wood/Druckenmiller/Burry), or Markdown/DOCX stock reports.
---

# Stock Analysis Suite

## Overview

Single-skill SOP-driven US stock analysis suite. This skill contains the
orchestrator and 17 internal modules (9 analytical + 8 investor personas)
under `modules/`. Read the relevant module file on demand; do not preload
modules that the current request does not need.

Always treat financial facts as time-sensitive. Fetch current market data,
filings, earnings dates, guidance, news, analyst estimates, macro data, and
technical prices when tools or browsing are available. If live data cannot
be fetched, state the data limitation clearly and avoid pretending the
report is current.

End user-facing reports with: `Not investment advice -- for your own research.`

## Claude.ai Web Compatibility

[unchanged from current SKILL.md — key.txt lookup order, prefetch fallback,
provider disclosure rules]

## Request Gate

[unchanged — combined clarification question for vague tickers, depth
selection, output format, objective, technical window]

## Report Depth Matrix

[unchanged — basic / standard / full SOP table]

## Report Format Gate

[unchanged — Markdown default vs. DOCX, DOCX checklist]

## Module Routing                                              <!-- NEW SECTION -->

Modules are internal instruction files in `modules/`. Load them with the
`Read` tool only when the current request requires them. Do NOT inline the
contents of every module into your context.

### Analytical modules

| Trigger | Read this module | Required for depth |
|---|---|---|
| Macro regime, Fed, rates, yield curve, CPI, VIX, liquidity | `modules/macro.md` | standard, full SOP |
| Sector / GICS / peer comparison / sector ETF strength | `modules/sector.md` | standard, full SOP |
| Business model, moat, TAM, management, capital allocation | `modules/company-fundamentals.md` | standard, full SOP |
| 10-K / 10-Q, income / balance / cash flow, earnings quality | `modules/financial-statements.md` | standard, full SOP |
| Valuation, DCF, target price, intrinsic value, multiples | `modules/valuation.md` | all depths |
| Charts, KDJ, RSI, MACD, BB, ATR, support/resistance, trend | `modules/technical.md` | all depths |
| Insider trades, news flow, EPS revisions, short interest | `modules/sentiment.md` | standard, full SOP (skip basic unless asked) |
| Position sizing, stop loss, R:R, event risk, sector cap | `modules/risk-position.md` | all depths |
| Bull/bear debate, investment committee, persona showdown | `modules/debate-panel.md` | full SOP, or when explicitly requested |

### Investor persona modules

Persona modules are NOT loaded by depth. Load `modules/investors/<persona>.md`
only when the user (a) names that persona, (b) asks for "X's lens on
<TICKER>", or (c) requests a debate that substitutes that persona into the
Bull or Bear slot.

| Persona | File |
|---|---|
| Warren Buffett | `modules/investors/buffett.md` |
| Charlie Munger | `modules/investors/munger.md` |
| Benjamin Graham | `modules/investors/graham.md` |
| Peter Lynch | `modules/investors/lynch.md` |
| Phil Fisher | `modules/investors/fisher.md` |
| Cathie Wood | `modules/investors/wood.md` |
| Stanley Druckenmiller | `modules/investors/druckenmiller.md` |
| Michael Burry | `modules/investors/burry.md` |

When a persona is dispatched as a debate subagent per the Subagent Dispatch
Protocol in `modules/debate-panel.md`, copy the full content of that
persona's module inline into the subagent prompt. Do not rely on the
subagent loading the file itself.

## Workflow

1. Resolve the ticker, exchange, company name, sector, industry, and report language.
2. Confirm depth and user objective via the Request Gate.
3. Collect source data with dates: [unchanged list — quote, filings, estimates, macro, sector, technical]
4. Fetch API-based daily, weekly, and requested intraday charts via
   `scripts/fetch_price_charts.py`. [unchanged usage notes — intraday-source
   default, KDJ data quality framing, chart contents, no-recommendation rule]
5. **Read the modules required by depth (Module Routing table above).** For
   each loaded module, apply its methodology to produce that section of the
   report. The module's "Standalone Markdown Report Mode" structure becomes
   the report section structure when invoked by the orchestrator.            <!-- CHANGED from "Invoke sub-skills" -->
6. For `full SOP` AND when the `Agent` tool is available, the debate is run
   as real parallel subagents per `modules/debate-panel.md`'s Subagent
   Dispatch Protocol. The orchestrator copies the relevant persona module
   content inline into each subagent prompt.                                  <!-- CHANGED -->
7. For `full SOP`, the company-fundamentals section must follow
   `references/institutional-company-analysis-bilingual.md`.
8. Build an evidence ledger: bullish facts, bearish facts, uncertain/missing
   data, catalysts, invalidation points.
9. Produce the requested Markdown or DOCX report using
   `references/report-template.md`.

## Data Failure and Fallback Rules

[unchanged — all 9 bullet rules from current SKILL.md]

## Event Risk Check

[unchanged]

## Target Price Discipline

[unchanged]

## Scoring Framework

[unchanged]

## Module Contract                                            <!-- RENAMED from Sub-Skill Contract -->

Modules are loaded on demand by the orchestrator and can also be invoked
directly by user request ("just run the technical module on NVDA"). When
loaded by the orchestrator, each module must return a Markdown section
that can be merged into the final report. When invoked standalone, the
module produces a self-contained Markdown sub-report in the user's language.

Required for both modes:
- section title and one-sentence conclusion
- data timestamp and source dates
- 2-5 analytical paragraphs for `full SOP`; 1-3 for `standard`; compact bullets only for `basic`
- at least one table when the section is metric-heavy
- bullish interpretation, bearish interpretation, and neutral/uncertain evidence
- explicit implication for the user's objective
- missing data, low-confidence assumptions, and what would change the conclusion

Standalone sub-reports end with `Not investment advice -- for your own research.`.

## Investor Persona Routing                                   <!-- CHANGED -->

The eight `modules/investors/*.md` files are NOT loaded automatically by
report depth. Three invocation patterns:

1. **Solo persona conversation** — user names a persona ("analyze NVDA
   through Buffett's lens"). Read only `modules/investors/buffett.md`. The
   entire conversation runs in that persona's voice. Output the persona's
   standalone Markdown report.
2. **Persona second opinion alongside the SOP** — after a `standard` or
   `full SOP` report, user asks for a single persona's read. Read the
   persona module against the same evidence ledger; surface its scoring
   breakdown and conviction band as an appendix.
3. **Persona as debate participant** — user requests a debate with
   substitution ("Buffett vs Wood"). Read `modules/debate-panel.md` first,
   then dispatch each persona as a parallel subagent with the persona
   module content copied inline into the subagent prompt.

Each persona has explicit Conflict And Pass Rules; respect them — a Buffett
persona refusing to opine on a pre-profit biotech is correct behavior, not
a failure to analyze.

## Output Rules

[unchanged — match user language, professional Markdown/DOCX, full SOP QA
gate, chart inclusion, no fabrication, conditional recommendations]
````

Sections marked `[unchanged]` are copied byte-for-byte from the existing
`stock-analysis/SKILL.md`. The new content is the **Module Routing**
section and the rewording of Workflow step 5/6 and the Investor Persona
section to use `Read modules/X.md` language instead of "invoke sub-skill".

---

## 4. Build Script Change

`tools/build_claude_zips.ps1` shrinks from "iterate every `stock-*` folder"
to "package the one `stock-analysis/` folder". Draft:

```powershell
param(
    [string]$OutputDir = "claude_web_zips"
)

$ErrorActionPreference = "Stop"

$RepoRoot   = Resolve-Path (Join-Path $PSScriptRoot "..")
$OutputPath = Join-Path $RepoRoot $OutputDir
$TempRoot   = Join-Path ([System.IO.Path]::GetTempPath()) ("stock-analyze-suite-" + [System.Guid]::NewGuid().ToString("N"))
$SkillName  = "stock-analysis"

New-Item -ItemType Directory -Force -Path $OutputPath | Out-Null
Get-ChildItem -Path $OutputPath -Filter "*.zip" -File -ErrorAction SilentlyContinue | Remove-Item -Force
New-Item -ItemType Directory -Force -Path $TempRoot | Out-Null

try {
    $staged = Join-Path $TempRoot $SkillName
    Copy-Item -Path (Join-Path $RepoRoot $SkillName) -Destination $staged -Recurse -Force

    Get-ChildItem -Path $staged -Recurse -Force -Directory -Filter "__pycache__" | Remove-Item -Recurse -Force
    Get-ChildItem -Path $staged -Recurse -Force -File -Include "*.pyc", ".DS_Store", "key.txt", "keys.txt", "api_keys.txt", ".env" | Remove-Item -Force
    Get-ChildItem -Path $staged -Recurse -Force -File | Where-Object { $_.Name -like ".env.*" -or $_.Name -like "*.pem" -or $_.Name -like "*.key" } | Remove-Item -Force

    $zip = Join-Path $OutputPath ($SkillName + ".zip")
    Compress-Archive -Path $staged -DestinationPath $zip -Force

    Write-Host ("Built {0} in {1}" -f (Split-Path $zip -Leaf), $OutputPath)
}
finally {
    if (Test-Path $TempRoot) {
        Remove-Item -Path $TempRoot -Recurse -Force
    }
}
```

Output: one `claude_web_zips/stock-analysis.zip` containing the full suite.

---

## 5. `docs/CROSS_PLATFORM.md` Change

Replace the "Build ZIP Files" / "Upload To Claude.ai" sections with a
single-zip flow:

```markdown
## Build the ZIP

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
    references/
    scripts/
```

## Upload to Claude.ai

1. Open Claude.ai.
2. Enable Code execution and file creation in Settings / Capabilities.
3. Go to Customize / Skills.
4. Upload `stock-analysis.zip`. That is the only upload.
5. Toggle it on.
```

The API keys, prefetch helper, and quick-test sections stay as-is.

---

## 6. `README.md` / `README.zh-CN.md` Changes

| Section | Action |
|---|---|
| `![Skills](https://img.shields.io/badge/skills-18-blue)` | Change to `skills-1-blue` (or remove the badge — the count is misleading once they're modules). |
| **Skill Map** table | Replace with **Module Map** — same rows, but the first column shows `modules/X.md` paths instead of skill names, and the table is presented as "what lives inside the one skill". |
| **Quick Install / Claude Code** | `Copy-Item .\stock-* "$env:USERPROFILE\.claude\skills\" -Recurse -Force` → `Copy-Item .\stock-analysis "$env:USERPROFILE\.claude\skills\" -Recurse -Force` |
| **Quick Install / Codex** | Same one-folder copy. |
| **Quick Install / Claude Desktop** | Single import: just `stock-analysis`. |
| **Quick Install / Claude.ai Web** | Single zip upload. |
| **Usage / Mode 2 — Single sub-skill** | Rephrase: "Tell the orchestrator to run a single module — e.g. *'just run the technical module on NFLX, intraday 5m'*". Slash commands like `/stock-valuation-analysis` no longer exist. |
| **Usage / Mode 3 — Persona conversation** | Rephrase: "Ask the orchestrator for a persona's voice — e.g. *'/stock-analysis Talk to me as Buffett about NVDA at current price'*". |
| **Usage / Mode 4 — Debate** | Rephrase: "Ask the orchestrator for a debate — e.g. *'/stock-analysis Run a 2-round Buffett vs Wood debate on TSLA'*". |
| **Repository Layout** | Replace tree with the layout in §1.4 above. |

---

## 7. `_legacy/` Backup

After moving content into `stock-analysis/modules/`, **copy** (not move,
until verification passes) each original folder into `_legacy/`:

```
_legacy/
├── README.md                       ← explains rollback procedure
├── stock-macro-analysis/
├── stock-sector-analysis/
├── stock-company-fundamentals/
├── stock-financial-statement-analysis/
├── stock-valuation-analysis/
├── stock-technical-analysis/
├── stock-sentiment-analysis/
├── stock-risk-position-analysis/
├── stock-debate-panel/
├── stock-investor-buffett/
├── stock-investor-munger/
├── stock-investor-graham/
├── stock-investor-lynch/
├── stock-investor-fisher/
├── stock-investor-wood/
├── stock-investor-druckenmiller/
└── stock-investor-burry/
```

`_legacy/README.md` contents:

```markdown
# Legacy skill folders

These are the 17 original sibling skill folders, archived on <DATE> when
the suite was consolidated into a single `stock-analysis/` skill.

To roll back:

1. Move every `stock-*` folder back to the repo root.
2. Restore the previous `stock-analysis/SKILL.md` (in git history) and
   delete `stock-analysis/modules/`.
3. Restore the previous `tools/build_claude_zips.ps1` (it iterates every
   `stock-*` folder).
4. Restore the previous `docs/CROSS_PLATFORM.md` and README files.

`stock-*` folders are not scanned by Claude when nested under `_legacy/`,
so they will not double-trigger alongside the consolidated skill.
```

Only after the consolidated skill passes a smoke test (see §9) is it safe
to delete the source `stock-*` folders. Until then they coexist with
`_legacy/` as identical copies, then the originals get removed.

---

## 8. Behavior Changes the User Should Know About

| Old behavior | New behavior | Impact |
|---|---|---|
| 18 separate `description:` strings, each triggers its own skill. | 1 description on `stock-analysis` that must cover all keywords. | If the new description doesn't include a specific phrase (e.g. "Bollinger Bands"), the skill won't auto-trigger on that phrase alone. Mitigated by the broadened description in §3. |
| `/stock-investor-buffett` as a Codex slash command. | `/stock-analysis` with a persona phrase in the prompt. | One extra word from the user. The orchestrator routes via the Investor Persona Routing block. |
| Each sub-skill self-described to Claude in the registry. | Only `stock-analysis` is in the registry. | Discovery via "what skills do I have?" lists 1 item, not 18. |
| Sub-skill `references/` lived inside each folder. | All references in `stock-analysis/references/`. | One canonical copy of `institutional-company-analysis-bilingual.md` and `persona-skill-template.md`. |
| 18 zips to upload to Claude.ai web. | 1 zip. | The main win. |
| Each sub-skill could be toggled on/off independently in Claude Desktop. | All-or-nothing toggle. | Acceptable for this suite since the modules are meant to work together. |

---

## 9. Smoke Test (Run Before Deleting Originals)

After the migration, verify by reading the new `stock-analysis/SKILL.md`
end-to-end and walking through these scenarios on paper:

1. **Bare ticker** — `NVDA` → does the Request Gate still ask for depth /
   format / objective / window?
2. **Full SOP** — `give me a full SOP report on TSLA, DOCX, intraday 5m`
   → does the Module Routing table tell Claude to Read macro + sector +
   fundamentals + financials + valuation + technical + sentiment + risk +
   debate, in that order?
3. **Persona solo** — `analyze NVDA through Buffett's lens` → does the
   Investor Persona Routing point to `modules/investors/buffett.md`?
4. **Persona debate** — `run a 2-round Buffett vs Wood debate on TSLA` →
   does Workflow step 6 instruct Claude to Read `modules/debate-panel.md`
   first, then dispatch persona subagents with their module content
   inlined?
5. **Standalone module** — `just run the technical module on AAPL, daily
   swing` → does the Module Contract section cover the standalone case?

If any scenario reads ambiguously, fix the SKILL.md wording before
deleting `stock-*` source folders.

---

## 10. Open Questions for You

Items I'd like your input on before I touch any files:

1. **Codex slash commands** — confirm you're OK losing `/stock-investor-buffett`,
   `/stock-valuation-analysis`, etc. as direct slash commands. If you want
   to keep them, we can leave one-line shim `agents/openai.yaml` files in
   `_legacy/` that don't actually do anything, but that's vestigial. The
   clean answer is: lose the shortcuts, gain the single install.

2. **Module file naming** — I proposed `financial-statements.md` instead of
   `financial-statement-analysis.md` (shorter). Same for `risk-position.md`
   vs `risk-position-analysis.md`. OK, or do you want to keep the longer
   names that mirror the old folder names exactly?

3. **`stock-` prefix on module files** — I dropped it (`macro.md`, not
   `stock-macro.md`) because we're already inside `stock-analysis/`. OK?

4. **Description length** — the new top-level description is long (one
   sentence packed with trigger keywords). Some platforms cap description
   length. Want me to verify the limit, or are you fine with whatever the
   platforms accept?

5. **Smoke test depth** — paper walkthrough only, or do you want me to
   actually run the consolidated skill against one ticker (e.g. NFLX,
   `basic` depth) end-to-end to verify it produces a report identical
   to the current setup?

6. **README badges** — keep the `skills-18` badge for historical context
   (with a note), or drop it? Same for the persona count badge.

---

## 11. Execution Order (When You Approve)

Step-by-step so you can interrupt at any point:

1. Create `_legacy/` and copy all 17 sibling folders into it. Verify
   structure.
2. Create `stock-analysis/modules/` and `stock-analysis/modules/investors/`.
3. For each of the 17 sub-skills: copy SKILL.md body into the corresponding
   module file with the edit rule in §2 applied. Verify no broken internal
   links.
4. Move shared references (`institutional-company-analysis-bilingual.md`,
   `persona-skill-template.md`) into `stock-analysis/references/`.
5. Rewrite `stock-analysis/SKILL.md` with the §3 draft.
6. Update `stock-analysis/agents/openai.yaml` `default_prompt`.
7. Rewrite `tools/build_claude_zips.ps1` with the §4 draft.
8. Rewrite `docs/CROSS_PLATFORM.md` per §5.
9. Rewrite `README.md` and `README.zh-CN.md` per §6.
10. Run smoke test (§9). If it passes, delete the 17 original `stock-*`
    sibling folders. `_legacy/` keeps the backup.
11. (Optional) Build the ZIP and verify structure: `tools\build_claude_zips.ps1`.

Estimated edit count: ~20 file rewrites + ~17 file moves + 1 new `_legacy/`
README. Most file content is preserved verbatim — the bulk of the work is
copy + small header edit, not rewriting analytical content.
