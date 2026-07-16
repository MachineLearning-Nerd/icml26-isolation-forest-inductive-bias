# Claim 3 - Random-walk expected depth


---
<!-- trackio-cell
{"type": "markdown", "id": "cell_3e749b5ccc9f", "created_at": "2026-07-16T16:48:55+00:00", "title": "VERIFIED independently"}
-->
## Verdict: VERIFIED

Each tree selects a gap with probability equal to gap width divided by the current
node range—the exact transition induced by Algorithm 1's uniform split. The
simulator never calls the closed form. Uniform, exponential, and two-cluster data,
n=5..80, four seeds, and 3,000 trees per configuration give 180,000 trees total.
Their empirical depths agree with Theorem 3.5 within Monte Carlo noise.
