# Six-claim audit contract

The claim numbers below are the current collection contract. They are
deliberately separated from the older three-claim judge surface preserved in
.trackio and outputs.

## Claim 1 — Theorem 3.5 expected depth

The paper gives a closed-form expected depth for every unique one-dimensional
point under the random-split Isolation Forest process. The audit compares that
formula with 180,000 generated trees across 60 configurations.

Verdict: VERIFIED, scoped. Correlation is 0.999867, mean absolute error is
0.025604, and maximum relative error is 0.020226.

## Claim 2 — marginal single anomaly

Theorems 4.3–4.5 use the density ratio κ = U/L and difference δ = U − L.
The exact route checks the stated iForest and k-NN sufficient bounds under
Assumption 4.2, then tests the theorem’s literal per-dataset necessity
wording.

Verdict: FALSIFIED as written. There are zero sufficient-bound violations but
480 admissible exact k-NN counterexamples below 90% of the stated boundary.
The randomized-tree route independently adds 144 such counterexamples.

## Claim 3 — central single anomaly

Theorems 4.6–4.7 predict a central iForest gap threshold of order
Theta(sqrt(n0 κ)) and a k-NN threshold of order Theta(kδ). The committed
central construction sweeps n0 from 20 through 640 and compares k-NN settings.

Verdict: VERIFIED, scoped to this one-dimensional construction. The iForest
log-log slope is 0.456335 and the k-NN slope is approximately zero.

## Claim 4 — marginal clustered anomalies

Theorem 4.8 claims universal iForest detection when the inter-cluster
separation is of order Theta(n1²κ); Theorem 4.9 gives the k-NN comparison.

Verdict: FALSIFIED as written for the universal iForest sufficiency component.
The decisive route uses n1 in {5, 9, 17, 33, 65}, n0 = n1², κ = 100n0,
four placements, and finite separations {1, 10, 1000}n1²κ. Every finite check
and the exact infinite-separation limit fails to detect all anomalies. The
separate asymptotic scaling route remains BLOCKED because its Appendix E
spacing convention differs from Definition 4.1.

## Claim 5 — concentration with tree count

Proposition 3.1 gives a Hoeffding tail bound for empirical depth. The audit
tests the derived independent-Monte-Carlo MSE rate, not an exact MSE equality.

Verdict: VERIFIED, derived-rate scope. It uses 100 through 30,000 trees,
three distributions, six seeds, 18 ensembles, 10,800 point comparisons, and
540,000 generated trees. The fitted MSE slope is −0.999007 with 95% CI
[−1.044882, −0.954260], with zero bound violations.

## Claim 6 — OpenML dimension census

Section 4 and Assumption 4.2 report 930,738 successful, 930,751 valid, and
933,440 total dimensions, with validity defined by no repeated values.

Verdict: BLOCKED. The arithmetic is internally consistent and source-confirmed,
but the paper and all three public arXiv source bundles omit the historical
dataset/task/version manifest, snapshot, feature rules, missing-value and tie
handling, exclusions, census code, and per-dimension values. A current OpenML
catalog is retained only as a drift diagnostic.

