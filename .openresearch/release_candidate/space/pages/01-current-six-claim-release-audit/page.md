# Current six-claim release audit

This page supersedes the older three-claim summary for the current six-claim
judge contract. The old pages remain unchanged and reachable as protected
historical evidence.

| Claim | Verdict | Reproducible basis |
|---|---|---|
| 1 — Theorem 3.5 expected depth | **VERIFIED** | 180,000 simulated trees across 60 configurations; correlation 0.999867, MAE 0.025604, maximum relative error 0.020226. |
| 2 — marginal single anomaly | **FALSIFIED** | Exact admissible marginal datasets satisfy the stated sufficient bounds, but hundreds of direct thresholds contradict Theorem 4.5's unqualified per-dataset necessity wording. |
| 3 — central single anomaly | **VERIFIED** | \(n_0=20,\ldots,640\); iForest log-log slope 0.456335 and k-NN slope approximately zero. |
| 4 — marginal clustered anomalies | **FALSIFIED** | An assumption-satisfying asymptotic family contradicts Theorem 4.8's universal sufficient-separation statement, including the infinite-separation limit. |
| 5 — concentration with tree count | **VERIFIED** | \(T=100,\ldots,30000\), six seeds and three distributions; MSE slope -0.999007 with 95% CI [-1.044882, -0.954260]. |
| 6 — OpenML dimension census | **BLOCKED** | The aggregate arithmetic is source-confirmed, but the released paper omits the historical dataset/version manifest, snapshot, feature rules, and per-dimension values needed to reproduce 930,738/930,751. |

The cumulative outcome is therefore three VERIFIED, two FALSIFIED, and one
BLOCKED. The release gate requiring a terminal VERIFIED or FALSIFIED verdict
for every claim is **not met**. This candidate has not been published and does
not claim a judge-score increase.

All terminal claims have a source audit, contract, raw machine-readable data,
executable verifier, independent checker, negative control, seeds, runtime,
environment record, and limitations. The Claim 6 positive verifier exits
nonzero because the exact historical census cannot be reconstructed.
