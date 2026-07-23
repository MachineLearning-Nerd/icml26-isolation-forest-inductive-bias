# Claim 5 source audit

- Primary source: `https://ar5iv.labs.arxiv.org/html/2505.12825`
- Retrieved `2026-07-23` with a browser User-Agent
- SHA-256: `e716edebd1c4b9ee6eb33a2f996d6232decafbc753ee9eb2fcdfadf280d74cac`
- Proposition 3.1 anchor: `#S3.Thmtheorem1`
- Section 5.1 anchor: `#S5.SS1`

For any positive epsilon, Proposition 3.1 bounds the probability that the
empirical depth from `M` independent iTrees differs from expected depth by at
least epsilon by `2*exp(-2*epsilon^2*M/n^2)`. This is a pointwise tail bound.
It does not state an exact MSE slope.

Section 5.1 samples 100 points from standard normal, uniform, and exponential
distributions, uses subsamples of 100, varies the number of iTrees from 100 to
1000, repeats each setup 10 times, and reports decreasing depth MSE. This
reproduction extends the geometric tree-count range to 30,000. The `T^-1`
MSE rate is identified explicitly as a derived independent-Monte-Carlo rate,
not wording quoted from Proposition 3.1.
