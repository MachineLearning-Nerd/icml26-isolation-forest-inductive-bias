# Claim 6 method

The audit separates three questions that must not be conflated:

1. Does the paper state the aggregate? Yes; all arXiv source versions report
   930,738 successful, 930,751 valid, and 933,440 total dimensions.
2. Can the released protocol identify the historical dimension population?
   No; the dataset manifest and preprocessing/counting rules are absent.
3. Does today's official OpenML catalog reproduce the denominator under
   obvious metadata interpretations? No; it has drifted and is used only as a
   diagnostic.

The fixed run is offline. It hashes and independently parses a frozen official
binary-dataset listing and a 1,639-row metadata manifest. Two implementations
recompute present-day dataset and feature totals. Upload-date prefix checks
test the arXiv-v1 date without treating a fitted cutoff as evidence.

The positive verifier requires the exact historical manifest, feature values,
per-dimension kappa recomputation, and either exact counts (verification) or an
assumption-satisfying contradiction (falsification). It must exit nonzero for
the present BLOCKED package.

A three-dimension synthetic fixture mutates the threshold from `sqrt(n+3)` to
`2*sqrt(n+3)` and confirms that the pass count changes. This is strictly a
negative control for the threshold/counting path; it is not OpenML evidence
and cannot affect the verdict.
