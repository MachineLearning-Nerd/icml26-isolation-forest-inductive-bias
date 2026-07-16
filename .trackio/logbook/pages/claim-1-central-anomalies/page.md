# Claim 1 - Central anomalies


---
<!-- trackio-cell
{"type": "markdown", "id": "cell_8e11f8ebfe8e", "created_at": "2026-07-16T16:48:53+00:00", "title": "VERIFIED at theorem scale"}
-->
## Verdict: VERIFIED

Two unit-spaced normal clusters surround one central anomaly. The exact anomaly
gap required by iForest grows from 5.5 to 26.5 as n0 grows 20 to 640, recovering
the square-root law. For k-NN with k=5 it remains exactly 2.5. Sweeping k changes
k-NN substantially, whereas the expected iForest depth has no tuned neighborhood
parameter. This directly checks sensitivity and adaptability without sklearn's
subsampling confound.
