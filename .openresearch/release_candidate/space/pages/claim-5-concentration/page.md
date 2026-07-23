# Claim 5 — concentration with tree count

**Verdict: VERIFIED.**

The experiment directly sweeps independent iTree counts
\(T\in\{100,300,1000,3000,10000,30000\}\) for normal, uniform, and
exponential samples. Six independent forest seeds give 18 ensembles, 108
aggregates, 10,800 point-level comparisons, and 540,000 generated trees.

Mean squared error falls strictly at every step, from 0.0498071 at 100 trees
to 0.000160659 at 30,000 trees, a 310.018-fold reduction. The fitted log-log
slope is -0.999007 (95% CI [-1.044882, -0.954260], \(R^2=0.960125\)).
There are zero violations of the Proposition 3.1 Hoeffding bound at the stated
test level.

Proposition 3.1 itself is a pointwise exponential tail bound, not an exact MSE
equality. The observed \(T^{-1}\) MSE rate is reported as the derived
independent-Monte-Carlo variance rate. A repeated-single-tree control is flat
and its positive verifier exits nonzero, as intended.
