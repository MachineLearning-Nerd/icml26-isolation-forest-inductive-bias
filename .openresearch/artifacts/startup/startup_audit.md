# Startup audit

- Project: `99bb9f3e-f265-4e70-844e-3bde806d1d0f`
- Expected and observed starting Git SHA:
  `1898d469a34353e52958064261b317cbe724b6f2`
- Initial worktree: detached, clean.
- Baseline branch: `main`.
- Fixed inherited command:
  `python reproduction/reproduce.py --output outputs && python -m pytest -q reproduction/test_reproduction.py`
- Shared environment: repository-local `.venv`, Python 3.12; one environment
  reused across all local CPU runs.
- `orx status --json` is not supported by the installed local-mode CLI.
  `orx projects --json`, project view, experiment status, run listings, Git,
  job listings, and disk inspection were used as the recorded alternatives.
- Protected/running jobs and available disk were inspected before launch.
- Environment variable **names only** were inspected; values are intentionally
  absent from evidence.

## Primary-source freeze

- URL: `https://ar5iv.labs.arxiv.org/html/2505.12825`
- Retrieval date: `2026-07-23`
- Retrieval used a browser User-Agent.
- SHA-256:
  `e716edebd1c4b9ee6eb33a2f996d6232decafbc753ee9eb2fcdfadf280d74cac`

Recorded anchors include Proposition 3.1 (`#S3.Thmtheorem1`), Definition 4.1
(`#S4.Thmdefinition1`), Assumption 4.2 (`#S4.Thmtheorem2`), and Theorems
4.3–4.9 (`#S4.Thmtheorem3` through `#S4.Thmtheorem9`). Exact quantifiers,
assumptions, and interpretation caveats are retained in each claim's
`source_audit.md`.

## Live verdict and judged Space

The live verdict record was filtered by exact
`space_id == "DineshAI/J0y3sNbo9G"`; `orid` alone was never used. It identifies
judged Space revision
`260bbe2fb64833c38a8acc22ab01b8d67a19d928`, two verified and four
inconclusive claims, and baseline 4/12.

That exact Space revision was downloaded. Its 20-file protected manifest is
`judged_space_manifest.tsv`. The candidate tree contains every old path; all
old files except the necessarily updated `logbook.json` remain byte-identical.
