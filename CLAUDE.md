# CLAUDE.md

Guidance for Claude (Claude Code / Cowork) when working on this repository.

## What this repo is

`stock-analyze-skills` ships **one** Claude Agent Skill — the `stock-analysis/` folder — an
institutional-grade US-stock research suite. `stock-analysis/SKILL.md` is a router /
orchestrator that `Read`s internal modules on demand. Everything else in the repo (docs,
design notes, READMEs, the ZIP builder) only supports that one skill.

## Repository layout

```
stock-analysis/            # the skill that ships — this is the product
  SKILL.md                 # router: Request Gate, Workflow, Scoring, Output rules
  modules/                 # 11 analytical modules + investors/ (8 personas)
  references/              # schemas + rule sets (report templates, depth framework, ...)
  scripts/                 # data_provider.py, fetch_price_charts.py, backtest.py
  agents/openai.yaml       # Codex / OpenAI agent metadata
docs/                      # cross-platform notes
tools/                     # build_claude_zips.ps1 — builds the Claude.ai upload ZIP
MIGRATION_PLAN.md          # 18->1 consolidation design (historical)
BACKTEST_DESIGN.md         # backtest v1 design (historical)
README.md / README.zh-CN.md
```

## Architecture

- **Router pattern.** `SKILL.md` is the orchestrator; it loads `modules/*.md` with the
  `Read` tool only when a request needs them. Never preload every module — token cost
  should scale with the work.
- **Modules** = 11 analytical (`macro, sector, company-fundamentals, financial-statements,
  valuation, technical, sentiment, ownership-structure, risk-position, debate-panel, backtest`) + 8 investor
  personas under `modules/investors/`.
- **References** in `references/` are shared schemas and rule sets, loaded when relevant.

## Invariants — do not break these unless the user explicitly asks

- **Output is always a single self-contained HTML file.** There is no output-format
  question. DOCX and Markdown-as-a-report were removed. Build HTML from
  `references/report-template.html` (structure + style) and `references/report-template.md`
  (content schema + Section Length Budget).
- **Build the HTML incrementally** via `Write` + repeated `Edit` calls — one major
  section at a time. NEVER assemble the entire 5–8k-word report in a single response.
  Under extended thinking at high/max effort, a single-response assembly overflows the
  thinking/output budget and the request fails silently (long spin, empty response).
  Each tool call has its own budget, so 10+ small writes succeed where one giant
  response fails.
- **Request Gate** asks one combined question for a bare ticker: (1) depth, (2) objective,
  (3) position & risk profile — total capital (总仓位, → Kelly-optimal sizing) or a fixed amount / current holding + cost basis / risk tolerance,
  (4) debate mode (full SOP only). Output format and the technical window are NEVER asked.
- **No API key required.** `scripts/data_provider.py` provider order is direct API (only
  with a key) -> `yfinance` (primary no-key source) -> prefetched JSON. The data scripts
  auto-install yfinance via `ensure_yfinance()`. Web search may fill non-price gaps, but
  every web-sourced figure needs a recency check before use.
- **Personas**: never ask the user which persona to use. The gate only toggles
  persona-vs-generic debate; Claude auto-selects the debate roster from the Persona
  Selection Table.
- **Scoring is risk-tolerance-weighted.** The `SKILL.md` Scoring Framework has
  Conservative / Balanced / Aggressive weight columns; the final /100 uses the column
  matching the user's risk tolerance (Balanced if skipped).
- **Section Length Budget** in `references/report-template.md` governs report length;
  Company Fundamentals and Financial Statement Review carry the heaviest budget.
- Every user-facing report ends with: `Not investment advice -- for your own research.`

## Consistency rule

The Request Gate / output / persona / scoring behavior is described in several files at
once. If you change one, update all that are affected:
`stock-analysis/SKILL.md`, `references/depth-framework.md`, `references/report-template.md`,
`references/report-template.html`, `modules/debate-panel.md`, `modules/risk-position.md`, `modules/ownership-structure.md`.
Keep `README.md` and `README.zh-CN.md` in sync with each other.

## Build & test

- **Build the Claude.ai upload ZIP**: run `tools/build_claude_zips.ps1` (PowerShell) ->
  `claude_web_zips/stock-analysis.zip`. The ZIP must contain the `stock-analysis/` folder
  with **forward-slash** paths — backslash paths are rejected by the claude.ai uploader.
  A `.skill` file is just that ZIP renamed.
- **Distribute via GitHub Releases**, not git: when cutting a new version, build the
  `.skill` locally, then on GitHub create a new release (tag `vX.Y.Z`), upload
  `stock-analysis.skill` as a release asset. The README's web-install link
  (`/releases/latest/download/stock-analysis.skill`) auto-points at the newest one.
  Never commit the `.skill` file to git — it goes stale the moment any skill file
  changes, and binary blobs bloat history.
- **Syntax-check scripts**: `python -m py_compile stock-analysis/scripts/*.py`.
- **Smoke-test data** (works with no key):
  `python stock-analysis/scripts/fetch_price_charts.py NFLX --output-dir ./outputs/NFLX_test --benchmark SPY --sector XLC`.

## Git

- Repo: `Jelly13124/stock-analyze-skills`, branch `main`.
- Stage files explicitly (`git add stock-analysis README.md CLAUDE.md ...`) — never
  `git add .`.
- Do NOT commit build artifacts / scratch: `1-skill`, `matt-pocock-skills/`,
  `stock-analysis.skill`, `claude_web_zips/`, `outputs/`, `prefetched_data/`.
