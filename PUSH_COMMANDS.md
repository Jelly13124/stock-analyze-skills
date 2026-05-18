# Push commands — your situation

**State of play:**
- Remote `github.com/Jelly13124/stock-analyze-skills` has older code that diverges a lot from what's now in this folder.
- This folder has never been `git init`'d locally — it's a fresh working copy.
- Goal: overwrite the remote with the current local state, but preserve the old remote history in a backup branch first (so nothing is lost forever).

Run these in PowerShell from `C:\Users\Jerry\Desktop\stock_analyze\`.

---

## Prerequisite — GitHub credentials

Before pushing, make sure you can authenticate to GitHub. Pick whichever you already use:

- **GitHub CLI** (recommended): `gh auth status` — if it says "Logged in", you're set.
- **Credential manager** (Windows default): if you've pushed from this machine before with HTTPS, your credentials should be stored already.
- **SSH key**: works if you've set one up on github.com.
- **Personal Access Token**: paste it as the password when git prompts.

---

## The push (one-shot, safe version)

```powershell
cd C:\Users\Jerry\Desktop\stock_analyze

# 1. Initialize git on main
git init -b main

# 2. Point at your GitHub repo
git remote add origin https://github.com/Jelly13124/stock-analyze-skills.git

# 3. Fetch the remote so we can back up its current state
git fetch origin

# 4. Save whatever's currently on remote main into a backup branch on GitHub.
#    Replace 'main' with 'master' if your remote default is master.
git push origin origin/main:refs/heads/pre-consolidation-backup
# If that errors with "src refspec origin/main does not match any", try:
#   git push origin origin/master:refs/heads/pre-consolidation-backup
# If BOTH error, the remote default branch is something else — run
# `git ls-remote --heads origin` to see all remote branches.

# 5. Sanity check what's about to be committed
git add -A
git status                                # confirm no key.txt, no outputs/

# If key.txt or anything sensitive shows up as staged, run:
#   git restore --staged key.txt
# before continuing.

# 6. Commit
git commit -m "Add stock-backtest v1 and consolidate 18 skills into one stock-analysis suite

stock-backtest v1
- Single-ticker historical backtest engine; stdlib + pandas
- Three modes: indicator strategy (KDJ / SMA50-200 / RSI / Bollinger / MACD),
  signal validation event-study, persona allocation (Lynch / Graham / Burry /
  Druckenmiller-lite; Buffett / Munger / Fisher / Wood return data_insufficient,
  deferred to v2)
- Outputs equity curve PNG, trades CSV, JSON metrics with in-sample vs
  out-of-sample split and overfit diagnostic
- Integrity rules baked in: no same-bar entry, 60-day filing-date embargo,
  per-side costs, zero-cost runs flagged 'frictionless backtest'
- New get_fundamentals_history() in data_provider.py
- Smoke-tested on NVDA 2020-2025

18-skill -> 1-skill consolidation (superpower pattern)
- All 17 prior stock-* sub-skills + stock-backtest become 18 modules under
  stock-analysis/modules/, loaded on demand via Read
- Top-level SKILL.md rewritten as router: broadened description, Module
  Routing table, Investor Persona Routing, Backtest Routing
- Shared references centralized in stock-analysis/references/
- Cross-references updated to the new layout
- 18 originals archived under _legacy/ for rollback
- tools/build_claude_zips.ps1 simplified to single-zip output
- docs/CROSS_PLATFORM.md and both READMEs rewritten for single-skill install

Design docs in MIGRATION_PLAN.md and BACKTEST_DESIGN.md.

Note: this commit consolidates substantial divergence from the prior remote
state. The previous remote main is preserved on branch pre-consolidation-backup.
"

# 7. Force-push the new main (overwrites remote with current local state)
git push -u origin main --force-with-lease
```

---

## What just happened

1. The remote now has **two branches**:
   - `main` — your new consolidated single-skill state
   - `pre-consolidation-backup` — exactly what was on `main` before you pushed
2. Local `main` tracks remote `main` (the `-u` flag).
3. If anything's wrong, you can restore the old code with:
   ```powershell
   git fetch origin
   git checkout pre-consolidation-backup
   ```
4. Once you're happy and don't need the backup anymore:
   ```powershell
   git push origin --delete pre-consolidation-backup
   ```

---

## If something goes wrong

**`fatal: refusing to update ref` on the backup push (step 4)** — the branch already exists. Either pick a different name (`pre-consolidation-backup-2`) or skip step 4 if you don't care about the old code.

**`The current branch main has no upstream branch` on push** — your local default isn't `main`. Run `git branch -M main` first, then retry the push.

**Push asks for credentials and you don't know the password** — generate a Personal Access Token at https://github.com/settings/tokens (scope: `repo`), paste it as the password.

**Push rejected (non-fast-forward) even with --force-with-lease** — your local fetch is out of date. Run `git fetch origin` again, then retry the push.

---

After the push works, `PUSH_COMMANDS.md` can be deleted — it was just the handoff.
