# Dev tests (not shipped)

Stdlib-only unit tests for the `stock-analysis` data scripts. These live in the repo root
(NOT under `stock-analysis/`) so `tools/build_claude_zips.ps1` never packages them into the
shipped skill. Run them with the system Python:

    python -m unittest discover -s tests -v

No third-party test framework is required.
