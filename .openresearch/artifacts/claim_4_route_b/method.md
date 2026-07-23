# Claim 4 route B method

Route B uses odd `n1={5,9,17,33}`, `n0=n1^2`, four deterministic seeds, and
two density levels. Each cluster contains seeded log-uniform spacings with
minimum exactly 1 and maximum exactly `kappa`, so its measured density factor
is `kappa` and density difference is `delta=kappa-1`.

The two k-NN families are `k=floor(n1^1.4)` and `k=floor(n1^1.75)`. In each
family, `k/n1` increases and `k/n0` decreases, explicitly instantiating the
theorem's asymptotic constraint. Invalid controls set `k=n1` and `k=n0`.

Threshold bisection evaluates every anomaly and every normal point. iForest
uses Theorem 3.5 directly. k-NN uses an exact vectorized merge of left and
right one-dimensional neighbor distances. Fits use a seed-cluster bootstrap;
strict confidence-interval gates decide the verdict. An independent scalar
sorted-distance implementation recomputes a subset.
