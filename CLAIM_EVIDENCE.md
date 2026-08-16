# Claim-to-evidence production map

This file explains how each current claim is turned into evidence. The common
path is:

paper statement → source contract → seeded producer → raw CSV/JSON → verifier
and independent check → negative control or limitation → scoped verdict

The names used inside the older Python runner predate the six-claim contract.
Where that happens, this document names both the current claim and the
historical function/output path so the mapping remains auditable.

## Summary

| Current claim | Source contract | Producer and inputs | Raw evidence | Check and control | Verdict |
|---|---|---|---|---|---|
| 1 | Theorem 3.5 | reproduction/reproduce.py, expected_depth and claim3_sweep | outputs/tree_depth_validation.csv and outputs/summary.json | Formula-versus-random-tree assertions in reproduction/test_reproduction.py; finite-tree error metrics retained | VERIFIED, scoped |
| 2 | Theorems 4.3–4.5 and Definition 4.1 | reproduction/claim2_exact.py and claim2_randomized.py | .openresearch/artifacts/claim_2 and claim_2_route_b | Independent scalar checkers, sufficient-bound checks, central negative controls, mutated-summary failures | FALSIFIED as written |
| 3 | Theorems 4.6–4.7 | reproduction/reproduce.py, historical claim1_sweep | outputs/central_thresholds.csv and outputs/summary.json | Threshold monotonicity, parameter-adaptability, and scaling assertions | VERIFIED, scoped |
| 4 | Theorems 4.8–4.9 | reproduction/claim4_varied.py and claim4_asymptotic.py | .openresearch/artifacts/claim_4_route_b and claim_4_route_a | Exact scalar limit checker, invalid-constraint control, mutation control; route A source deviation retained | FALSIFIED as written |
| 5 | Proposition 3.1 and Section 5.1 | reproduction/claim5_concentration.py | .openresearch/artifacts/claim_5 | Independent group-MSE checker, Hoeffding checks, repeated-tree flat negative control | VERIFIED, derived-rate scope |
| 6 | Section 4, Assumption 4.2, Table 1 | reproduction/claim6_openml_audit.py | .openresearch/artifacts/claim_6 | Independent parser/checker, frozen current-catalog diagnostic, expected positive-verifier failure | BLOCKED |

## Claim 1 — Theorem 3.5 expected depth

The producer computes the scalar closed-form expected depth for sorted,
unique one-dimensional observations and generates independent randomized trees.
The current source calls the tree-validation sweep claim3_sweep because it was
written before the six-claim contract was finalized; externally it is Claim 1.

- Producer: reproduction/reproduce.py
- Formula: reproduction/reproduce.py, expected_depth
- Tree generator: reproduction/reproduce.py, random_tree_depths
- Raw rows: outputs/tree_depth_validation.csv
- Summary: outputs/summary.json
- Scope: 60 configurations, 3,000 trees per configuration, 180,000 trees total
- Checks: reproduction/test_reproduction.py checks correlation, relative error,
  and the exact tree count after outputs are regenerated.
- Limitation: this is a finite numerical validation of Theorem 3.5, not a
  replacement for its proof.

## Claim 2 — marginal single anomaly

The exact producer constructs normal spacings satisfying Assumption 4.2,
computes direct iForest and k-NN thresholds, and evaluates the theorem’s
sufficient and literal necessary conditions. A second producer estimates the
iForest threshold with finite randomized forests while retaining the exact
threshold next to every empirical row.

- Exact producer: reproduction/claim2_exact.py
- Randomized producer: reproduction/claim2_randomized.py
- Contracts and source audits:
  .openresearch/artifacts/claim_2/claim_contract.json and source_audit.md
- Exact raw rows: .openresearch/artifacts/claim_2/raw_thresholds.csv
- Randomized raw rows:
  .openresearch/artifacts/claim_2_route_b/raw_forest_thresholds.csv and
  raw_knn_thresholds.csv
- Exact result: 128 normal configurations, 640 rows, eight seeds, zero
  sufficient-bound violations, 480 below-boundary literal k-NN counterexamples.
- Randomized result: 36 forest rows, 144 k-NN rows, four forest seeds, 1,600
  trees per threshold evaluation, 144 further literal counterexamples.
- Independent checks:
  reproduction/independent_check_claim_2.py and
  reproduction/independent_check_claim_2_randomized.py.
- Negative controls mutate assumptions, geometry, or exact agreement and are
  required to fail their verifiers.
- Interpretation: the two displayed expressions remain supported as uniform
  sufficient bounds; the unqualified per-dataset k-NN necessity wording does
  not survive the direct admissible cases.

## Claim 3 — central single anomaly

The historical claim1_sweep function constructs two unit-spaced normal clusters
with a symmetric central gap and measures the smallest gap that makes the
central point the unique iForest anomaly. It repeats the calculation for k-NN
and varies n0 from 20 through 640.

- Producer: reproduction/reproduce.py, claim1_sweep and find_threshold
- Raw rows: outputs/central_thresholds.csv
- Summary: outputs/summary.json
- Metrics: iForest slope 0.456335; k-NN slope approximately zero; iForest
  threshold parameter CV 0; k-NN parameter CV 0.4682895715.
- Checks: reproduction/test_reproduction.py checks monotonic iForest thresholds,
  k-NN parameter behavior, and the expected scaling ranges.
- Limitation: this is the committed one-dimensional construction and does not
  independently re-prove the theorem for every admissible dataset.

## Claim 4 — marginal clustered anomalies

The primary scaling route tests the paper’s asymptotic family and is retained
as a blocked route because Appendix E uses cross-cluster extrema that do not
match Definition 4.1’s within-dataset density metrics. The decisive route
instead tests the universal iForest sufficiency statement directly with an
exact, assumption-satisfying family.

- Primary route: reproduction/claim4_asymptotic.py and
  .openresearch/artifacts/claim_4_route_a
- Decisive route: reproduction/claim4_varied.py and
  .openresearch/artifacts/claim_4_route_b
- Family: n1 in {5, 9, 17, 33, 65}; n0 = n1²; κ = 100n0; four placements;
  finite separations {1, 10, 1000}n1²κ.
- Raw evidence: claim_4_route_b/raw_counterexamples.csv; 60 finite checks
  summarized across 20 counterexample families.
- Independent check: reproduction/independent_check_claim_4_varied.py
  recomputes the exact Theorem 3.5 infinite-separation limit; 20 rows and zero
  mismatches.
- Verifier: reproduction/verify_claim_4_varied.py. The route-A verifier is
  intentionally nonterminal because its source convention is documented as a
  deviation.
- Result: every finite large-separation check fails to rank all anomalies
  shallower than all normals, and every infinite-separation limit fails; the
  weakest strict limiting failure margin is 1.990844.
- Interpretation: a universal sufficient-separation statement is falsified by
  the exact family. The result is stronger than an inconclusive scaling fit.

## Claim 5 — concentration with tree count

The producer evaluates pointwise empirical depths over independent forests and
compares them to the Theorem 3.5 expectation for normal, uniform, and
exponential samples.

- Producer: reproduction/claim5_concentration.py
- Raw point rows: .openresearch/artifacts/claim_5/point_depths.csv
- Aggregates: .openresearch/artifacts/claim_5/aggregate_mse.csv
- Independent checker: reproduction/independent_check_claim_5.py
- Verifier: reproduction/verify_claim_5.py
- Design: tree counts 100, 300, 1,000, 3,000, 10,000, 30,000; six forest
  seeds; 18 ensembles; 108 aggregate rows; 10,800 point rows; 540,000 trees.
- Result: mean MSE decreases strictly, the fitted slope is −0.999007 with
  95% CI [−1.044882, −0.954260], and no Hoeffding-bound check fails.
- Negative control: a repeated single-tree curve has an approximately flat
  slope and is rejected by the positive verifier.
- Limitation: the T^-1 MSE behavior is labeled a derived independent Monte
  Carlo rate, not a claim that Proposition 3.1 itself states an MSE equality.

## Claim 6 — OpenML dimension census

The audit separates source arithmetic from source-faithful reproduction. It
checks the paper’s published counts, freezes a current official OpenML
catalog as a diagnostic, and records every protocol field needed to rerun the
historical census.

- Producer: reproduction/claim6_openml_audit.py
- Source and version audit:
  .openresearch/artifacts/claim_6/source_audit.md and
  source_versions_manifest.json
- Current catalog: openml_binary_catalog_2026-07-23.json
- Current metadata: current_dataset_metadata.csv
- Protocol contract: claim_contract.json
- Independent check: reproduction/independent_check_claim_6.py
- Positive verifier: reproduction/verify_claim_6.py
- Expected failure record: verifier_expected_failure.json
- Results: paper arithmetic matches 930,738 / 930,751 / 933,440; the current
  catalog has 1,639 active binary datasets, 1,199,438 total-feature metadata
  sum, and 1,143,087 numeric-feature sum; no historical manifest or
  per-dimension values are present.
- Limitation: the current catalog is not substituted for the historical
  population, and the unit-level threshold mutation is not counted as census
  evidence.
- Verdict: BLOCKED rather than VERIFIED or FALSIFIED.

## Release gate

reproduction/verify_release_candidate.py checks the protected historical
release tree, additive current pages, text-only upload allowlist, hashes, and
secret scan. It accepts the six statuses
VERIFIED, FALSIFIED, VERIFIED, FALSIFIED, VERIFIED, BLOCKED and therefore
keeps publication_authorized false. That blocked gate is intentional and is
reported in README.md and STATUS.md.
