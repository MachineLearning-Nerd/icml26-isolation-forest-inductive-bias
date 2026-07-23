# Claim 2 — exact marginal single-anomaly audit

**Verdict: FALSIFIED** under the literal per-dataset necessity wording of
Theorem 4.5.

The experiment implements the marginal setting from Definition 4.1:
\(U\) is the maximum normal spacing, \(L\) the minimum, \(\kappa=U/L\), and
\(\delta=U-L\). It varies \(U,\kappa,\delta,k\), measures both thresholds
directly, uses eight deterministic seeds, and checks Assumption 4.2
\(\kappa\ge\sqrt{n+3}\).

Across 128 normal configurations and 640 rows:

- The iForest sufficient condition \(x_2-x_1>U\kappa\) had zero violations.
- The k-NN sufficient condition
  \(x_2-x_1>U+(k-1)\delta/2\) had zero violations.
- There were 480 admissible cases detected below 90% of the claimed k-NN
  boundary, contradicting an unqualified claim that the boundary is necessary
  for each dataset.
- A second randomized-tree route used 1,600 trees per evaluation, produced 36
  empirical iForest thresholds with correlation 0.994086 to exact expected
  depths, and found 144 further k-NN counterexamples.
- A central-anomaly negative control is retained and is distinct from the
  marginal construction.

The evidence supports both expressions as uniform sufficient bounds. It does
not support Theorem 4.5's literal per-dataset “necessary” wording. The source
proof extremizes the anomaly and normal endpoint over different spacing
assignments, which explains the distinction.
