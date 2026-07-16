# Isolation Forest inductive bias — ICML 2026 reproduction

Independent CPU reproduction for OpenReview `J0y3sNbo9G` / arXiv `2505.12825`.
It implements the paper's exact one-dimensional expected-depth formula, validates
it against actual randomized trees, and tests both iForest/k-NN case-study claims.

```bash
.venv/bin/python reproduction/reproduce.py --output outputs
.venv/bin/python -m pytest -q reproduction/test_reproduction.py
```

The run grows 180,000 trees over 60 configurations, evaluates central-anomaly
thresholds through 640 normal points, and fits boundary/density effects over
5,520 independently generated probe rows. No GPU or official code is used.

