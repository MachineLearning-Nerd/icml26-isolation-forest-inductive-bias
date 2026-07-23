# Claim 4 route B method

Route B uses odd `n1={5,9,17,33,65}`, `n0=n1^2`, `kappa=100*n0`, and four
deterministic placements of the anomaly cluster's single large gap. The
normal cluster's first internal gap is `kappa`. Every other within-cluster gap
is 1, so both clusters have density factor exactly `kappa` and density
difference exactly `kappa-1`. Assumption 4.2 holds and `n1/n0=1/n1 -> 0`.

For each configuration, exact Theorem 3.5 depths provide a failure witness at
separations `1`, `10`, and `1000` times `n1^2*kappa`: one anomaly is at least
as deep as the boundary normal, so not all anomalies are detected.

The decisive check is analytic. In Theorem 3.5, as the inter-cluster gap tends
to infinity, its contribution tends to one and opposite-cluster contributions
tend to zero. Full-data depths converge to within-cluster depths plus one.
The limiting witness remains strict in every family. A separate scalar
implementation recomputes all limits. The verifier requires exact assumptions,
all finite checks, and every limiting contradiction.
