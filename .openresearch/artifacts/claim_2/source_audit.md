# Claim 2 source audit

- Source URL: `https://ar5iv.labs.arxiv.org/html/2505.12825`
- Retrieved with a browser User-Agent on: `2026-07-23` (Asia/Kolkata)
- SHA-256: `e716edebd1c4b9ee6eb33a2f996d6232decafbc753ee9eb2fcdfadf280d74cac`
- Definition 4.1 anchor: `#S4.Thmdefinition1`
- Assumption 4.2 anchor: `#S4.Thmtheorem2`
- Theorem anchors: `#S4.Thmtheorem3`, `#S4.Thmtheorem4`, `#S4.Thmtheorem5`

Definition 4.1 takes the maximum and minimum spacing over the normal points
`x2:n`: `U=max_{i>=2}(x_{i+1}-x_i)`, `L=min_{i>=2}(x_{i+1}-x_i)`,
`kappa=U/L`, and `delta=U-L`. Assumption 4.2 states
`kappa>=sqrt(n+3)`.

Theorem 4.3 is universally quantified over datasets whose normal points have
the recorded density factor. Its strict sufficient condition is
`x2-x1 > U*kappa`; the conclusion is `hbar(x1)<hbar(xj)` for every `j>1`.

Theorem 4.4 uses an existential conclusion: for `n>4` and a separation in
`(U,U*kappa]`, there exists an assignment for which `x1` is not strictly the
shallowest point. The appendix construction records spacings
`(U+epsilon,U/2,U,...,U)`. This construction has density factor 2 and therefore
does not itself satisfy Assumption 4.2 for `n>4`; this mismatch is retained as a
source limitation rather than silently repaired.

Theorem 4.5 states without an explicit minimax qualifier that the sufficient
and necessary k-NN condition is
`x2-x1 > U+(k-1)*delta/2`. Appendix C.3 proves a uniform extremal comparison by
placing the infimum for the anomaly and supremum for a normal endpoint on
different spacing assignments. This route reports both interpretations:
the formula as a uniform sufficient bound, and the theorem's literal
per-dataset “necessary” wording.
