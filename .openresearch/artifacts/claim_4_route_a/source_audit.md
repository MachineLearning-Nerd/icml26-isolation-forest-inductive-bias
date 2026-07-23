# Claim 4 source audit

- Primary source: `https://ar5iv.labs.arxiv.org/html/2505.12825`
- Retrieved `2026-07-23` with a browser User-Agent
- SHA-256: `e716edebd1c4b9ee6eb33a2f996d6232decafbc753ee9eb2fcdfadf280d74cac`
- Theorem 4.8 anchor: `#S4.Thmtheorem8`
- Theorem 4.9 anchor: `#S4.Thmtheorem9`
- Proof anchors: Appendix E.1 and E.2

Theorem 4.8 assumes odd `n1`, `n1=o(n0)`, and two marginal clusters described
as `kappa`-dense. It states that the sufficient and necessary iForest
separation is `Theta(n1^2*kappa)`.

Theorem 4.9 assumes `omega(n1)<=k<=o(n0)` and two `delta`-dense clusters. It
states a sufficient and necessary k-NN separation `Theta(k*delta)`.

Appendix E instead defines `U_mg` as the maximum spacing inside the anomaly
cluster and `L_mg` as the minimum spacing inside the normal cluster. Its proof
derives `Theta(n1^2)` and `Theta(k)` after implicitly normalizing spacings,
while the theorem restores `kappa` and `delta`. Route A follows the theorem
text by making both clusters separately have minimum gap 1 and maximum gap
`kappa`; it records the appendix mismatch rather than silently adopting it.

The proof also compares extrema over different spacing assignments when
establishing sufficiency and necessity. Results are therefore reported as an
asymptotic canonical-family test, not a universal proof.
