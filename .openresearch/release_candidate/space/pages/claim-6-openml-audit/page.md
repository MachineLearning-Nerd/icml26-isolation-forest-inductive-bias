# Claim 6 — OpenML dimension audit

**Verdict: BLOCKED.**

Section 4 and Assumption 4.2 report that 930,738 of 930,751 valid dimensions
meet \(\kappa\ge\sqrt{n+3}\), from 933,440 total dimensions. The arithmetic is
internally consistent: 2,689 dimensions are labeled invalid and 13 valid
dimensions fail.

All three public arXiv source bundles were audited. None supplies dataset or
task IDs, versions, a historical snapshot timestamp, target/ignored-column
rules, feature typing, missing-value and tie handling, unavailable-dataset
exclusions, per-dimension values, or the census implementation.

As a drift diagnostic, the official current OpenML binary-dataset endpoint was
frozen on 2026-07-23 (SHA-256
`5485ea844e865020734edc21a48fd6ff3ef6755eb90b1cd9d75e3d0adf98e208`).
Metadata for all 1,639 active binary datasets was independently recorded. It
contains 1,199,438 total features and 1,143,087 numeric features; filtering
the current catalog by the arXiv-v1 date also does not recover 933,440. This
shows protocol/catalog drift, but it cannot falsify an unidentified historical
census.

The independent audit passes, confirming that the evidence is genuinely
underidentified. The positive claim verifier exits nonzero. A mutated-threshold
unit control changes its synthetic count, proving that the counting path is
sensitive, but it is explicitly excluded from evidence for the historical
OpenML population.

No replacement dataset was substituted, and the published numerator and
denominator were not labeled reproduced.
