# Claim 2 method

Route A generates 128 admissible normal-spacing configurations from four
values each of `U` and `kappa` and eight deterministic seeds. Every
configuration contains both an exact minimum spacing `L=U/kappa` and an exact
maximum spacing `U`; all satisfy Assumption 4.2.

For each configuration, bisection measures the smallest marginal separation
whose expected iForest depth is strictly below every normal depth. The same
procedure measures the separation whose paper-defined mean k-nearest-neighbor
distance is strictly above every normal score for `k` in `{1,3,5,7}`.

The run records direct thresholds, stated paper boundaries, normalized ratios,
log-linear exponents in `U` and `kappa`, seed-bootstrap 95% confidence
intervals, and decisions immediately above and below each boundary. A separate
scalar-loop implementation recomputes every row. A central-anomaly geometry
table is retained as a negative control and is never substituted for the
marginal experiment.

The verifier treats the formulas as conservative sufficient bounds. It treats
an admissible dataset detected below a boundary described literally as
“necessary” as a counterexample to that per-dataset reading. The result is
therefore allowed to be `FALSIFIED`; it is never upgraded from an
inconclusive, skipped, or toy check.
