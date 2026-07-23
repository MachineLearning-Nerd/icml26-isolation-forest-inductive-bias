# Claim 4 — marginal clustered anomalies

**Verdict: FALSIFIED** for Theorem 4.8's universal iForest sufficiency claim.

The primary sweep used geometrically spaced \(n_1\), varied \(n_0\) and
\(\kappa\), enforced \(\omega(n_1)\le k\le o(n_0)\), measured iForest and k-NN
thresholds, reported bootstrap uncertainty, and included invalid-constraint
controls. Its fitted exponents were directionally consistent but not precise
enough for a terminal scaling verdict, so that route remains explicitly
BLOCKED.

The decisive route is an exact counterexample family satisfying the theorem's
literal assumptions:

- \(n_1\in\{5,9,17,33,65\}\), \(n_0=n_1^2\), hence \(n_1/n_0\to0\).
- \(\kappa=100n_0\), with exact density-factor checks.
- Four deterministic seeds and separations
  \(\{1,10,1000\}\,n_1^2\kappa\), for 60 finite checks.
- Every finite check fails to rank all anomalies shallower than every normal
  point.
- The exact Theorem 3.5 limit as separation tends to infinity also fails for
  every family member; the weakest failure margin is 1.990844.

Thus no constant hidden inside \(\Theta(n_1^2\kappa)\) repairs the universal
sufficient-separation statement for this admissible family. The verifier and
independent checker pass; a mutated witness fails as intended.
