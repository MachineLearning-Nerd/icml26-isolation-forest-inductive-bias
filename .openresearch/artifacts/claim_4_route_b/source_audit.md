# Claim 4 route B source audit

- Primary source: `https://ar5iv.labs.arxiv.org/html/2505.12825`
- Retrieved `2026-07-23` with a browser User-Agent
- SHA-256: `e716edebd1c4b9ee6eb33a2f996d6232decafbc753ee9eb2fcdfadf280d74cac`
- Theorem 4.8 anchor: `#S4.Thmtheorem8`
- Theorem 4.9 anchor: `#S4.Thmtheorem9`
- Proof anchors: Appendix E.1 and E.2

Theorem 4.8 quantifies over datasets whose odd anomaly cluster and normal
cluster each satisfy the density-factor condition, with `n1=o(n0)`. It calls
`Theta(n1^2*kappa)` both sufficient and necessary for detecting every anomaly.

Theorem 4.9 requires `omega(n1)<=k<=o(n0)` and the density-difference
condition in both clusters. It calls `Theta(k*delta)` sufficient and necessary.

Definition 4.1 makes `kappa=U/L` and `delta=U-L`. Appendix E instead combines
the maximum anomaly spacing `U_mg` with the minimum normal spacing `L_mg`.
This route implements the theorem and Definition 4.1 literally in each
cluster. It tests the universal sufficiency claim by constructing a sequence
where the inter-cluster separation can tend to infinity but one normal point
remains shallower than an anomaly. The Appendix E proof's cross-cluster
extremization does not rule out this construction.
