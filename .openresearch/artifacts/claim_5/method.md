# Claim 5 method

One deterministic 100-point dataset is sampled from each distribution in
Section 5.1. Six independent forest seeds generate cumulative ensembles of
30,000 trees. The same cumulative stream is evaluated at
`T={100,300,1000,3000,10000,30000}`, preventing cross-T dataset or seed noise
from masquerading as concentration.

For every point, empirical mean depth is compared with Theorem 3.5. Raw
pointwise errors and aggregate MSE are stored. A cluster bootstrap over the 18
independent distribution/forest ensembles gives the log-MSE versus log-T
slope interval. The Proposition 3.1 epsilon boundary at alpha 0.05 is checked
directly.

The negative control repeats one tree instead of drawing independent trees;
its MSE is exactly flat in T and must be rejected by the same verifier. A
second scalar implementation recomputes all 300 unique theoretical depths and
all 108 aggregate MSE values.
