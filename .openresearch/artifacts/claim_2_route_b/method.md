# Claim 2 randomized route method

For 36 admissible combinations of `U`, `kappa`, spacing seed, and forest seed,
the route measures the marginal separation at which the empirical mean depth
over 800 randomized iTrees becomes strictly smaller than every normal mean
depth. Nine bisection steps are paired with the exact Theorem 3.5 threshold.

An independent simulator uses uniform numeric split values rather than
categorical gap probabilities and remeasures 12 thresholds with 1,600 trees at
each of nine bisection points. It compares those thresholds to the exact
Theorem 3.5 values by correlation and normalized error rather than requiring
two noisy finite forests to cross at an identical point. Exact k-NN thresholds
and decisions at 90% of the stated necessary boundary are also recorded.
Seed-bootstrap confidence intervals quantify finite-forest uncertainty.

The existing central-anomaly regression is rerun unchanged. A separate central
geometry table is a negative control and may not satisfy the marginal verifier.
