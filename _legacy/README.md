# Legacy skill folders

These are the 18 original sibling skill folders, archived on 2026-05-18 when the suite was consolidated into a single `stock-analysis/` skill (the "superpower" structure). The 17 original sub-skills plus the newer `stock-backtest/` all live here as backups.

## Why archived, not deleted

So you can roll back. The new structure is `stock-analysis/modules/<name>.md` for analytical sub-skills and `stock-analysis/modules/investors/<name>.md` for investor personas. Their analytical content lives in those module files now; this folder preserves the original SKILL.md frontmatter + folder structure exactly as it was.

## To roll back

1. Move every `stock-*` folder back to the repo root:
   ```powershell
   Get-ChildItem _legacy\stock-* | Move-Item -Destination .
   ```
2. Restore the previous `stock-analysis/SKILL.md` from git history (`git checkout <pre-merge-sha> -- stock-analysis/SKILL.md`) and delete `stock-analysis/modules/`.
3. Restore the previous `tools/build_claude_zips.ps1` (it iterates every `stock-*` folder).
4. Restore the previous `docs/CROSS_PLATFORM.md` and the two README files.

## Why these don't double-trigger

`stock-*` folders nested under `_legacy/` are not scanned by Claude's skill discovery — the skill loader only sees top-level `stock-*` folders in the repo root. So the merged skill and the archive coexist without conflict.
