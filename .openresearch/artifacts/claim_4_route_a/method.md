# Claim 4 route A method

The geometric odd cluster sizes are `n1={5,9,17,33,65}`. For every size,
`n0=n1^2` and `k=floor(n1^1.5)`, an explicit asymptotic sequence satisfying
`k/n1 ~ sqrt(n1) -> infinity` and `k/n0 ~ 1/sqrt(n1) -> 0`. Three density
levels start at `ceil(sqrt(n0+n1+3))`, preserving Assumption 4.2.

Within each cluster, palindromic spacings have minimum 1 and maximum `kappa`.
Thus both clusters separately have density factor exactly `kappa` and density
difference exactly `delta=kappa-1`, as required by the theorem text. Exact
Theorem 3.5 depths are evaluated for every anomaly and for normal endpoints,
midpoint, and 17 quantiles. Exact paper-defined k-NN scores are evaluated for
every anomaly and the two normal endpoints plus midpoint. Bisection directly
measures both detection thresholds.

Log-linear fits estimate the exponents of `n1`, `kappa`, `k`, and `delta`.
Configuration bootstrap intervals are reported. Invalid controls set `k=n1`
or `k=n0`; both must be rejected. A scalar-loop implementation independently
remeasures all tractable rows.
