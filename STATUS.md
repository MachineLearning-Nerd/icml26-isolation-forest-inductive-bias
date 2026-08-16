# Status

## Current collection

- Repository: https://github.com/MachineLearning-Nerd/icml26-isolation-forest-inductive-bias
- State: VERIFIED_SCOPED_WITH_FALSIFIED_AND_BLOCKED_CLAIMS
- Claims: 3 verified in scope, 2 falsified as literally stated, 1 blocked
- Code: independent; no official implementation was released
- Attribution target: MachineLearning-Nerd <MachineLearning-Nerd@users.noreply.github.com>

## Claim verdicts

1. Theorem 3.5 expected depth — VERIFIED, scoped to the one-dimensional
   expected-depth formula and finite randomized-tree comparison.
2. Theorems 4.3–4.5 marginal single anomaly — FALSIFIED as written for the
   literal per-dataset k-NN necessity wording; sufficient-bound checks pass.
3. Theorems 4.6–4.7 central single anomaly — VERIFIED, scoped to the committed
   central-gap construction and threshold sweep.
4. Theorems 4.8–4.9 marginal clustered anomalies — FALSIFIED as written for
   the universal iForest sufficiency component; the primary scaling route is
   separately retained as BLOCKED.
5. Proposition 3.1 concentration — VERIFIED for the observed, derived T^-1
   independent-Monte-Carlo MSE rate; this is not an equality claimed by the
   proposition itself.
6. Section 4 OpenML dimension census — BLOCKED because the exact historical
   manifest, feature values, and census protocol are absent.

## Historical evaluator boundary

- Trackio space: https://huggingface.co/spaces/DineshAI/J0y3sNbo9G
- Judged revision: 260bbe2fb64833c38a8acc22ab01b8d67a19d928
- Judged at: 2026-07-16T17:12:35+00:00
- Recorded result: 2 of 6 verified, 4 inconclusive, baseline 4/12 of 12
- Current release candidate: not published; publication gate remains closed by
  blocked Claim 6; no new judge score is claimed.

## Verification

The persisted release package is checked by
reproduction/verify_release_candidate.py. The repository-level
verify_final.py additionally checks the documentation contract, paper hash,
evidence summaries, branch inventory, remote identity, and canonical commit
attribution.
