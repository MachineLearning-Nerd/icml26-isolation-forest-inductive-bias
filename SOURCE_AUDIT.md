# Source audit

The primary source is arXiv:2505.12825. No official implementation is released;
all code is independent.

- Algorithm 1: recursively choose a split uniformly between the current minimum
  and maximum. On sorted one-dimensional data this chooses a gap with probability
  proportional to its width; the simulator implements exactly that transition.
- Theorem 3.5: expected depth is the sum of left and right adjacent-gap ratios.
- Theorems 4.6–4.7: a central anomaly requires a gap scaling as
  `Theta(sqrt(n0*kappa))` for iForest versus `Theta(k*delta)` for k-NN.
- Theorem 3.5 also exposes endpoint distances in iForest depth, whereas k-NN is
  locally density based.

The central-anomaly construction uses two unit-spaced normal clusters and varies
the symmetric anomaly gap. This satisfies the paper's one-dimensional case-study
scope. The boundary analysis uses random lognormal spacings and controls for local
gap before adding endpoint distance. Numerical evidence is not represented as a
replacement for the general proofs.

