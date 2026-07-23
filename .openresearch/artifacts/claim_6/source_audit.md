# Claim 6 source audit

## Primary statement

- Primary HTML: `https://ar5iv.labs.arxiv.org/html/2505.12825`
- Retrieved: `2026-07-23`, using a browser User-Agent
- SHA-256: `e716edebd1c4b9ee6eb33a2f996d6232decafbc753ee9eb2fcdfadf280d74cac`
- Assumption 4.2: `kappa >= sqrt(n+3)`
- Section 4 says it checks “all dimensions of binary classification datasets
  from the OpenML benchmark.”
- “Valid” means that a dimension has no repeated values.
- Table 1 reports 930,738 successful, 930,751 valid, and 933,440 total
  dimensions. Thus 2,689 are labeled invalid and 13 valid dimensions fail.

## Versioned source audit

All public arXiv source versions were fetched from
`https://export.arxiv.org/e-print/2505.12825vN` with a browser User-Agent:

| Version | SHA-256 |
|---|---|
| v1 | `00749d4d6606d7d578abb914a37ceda9ae35bdf94a3fd084fd34f4a8ac9cac71` |
| v2 | `1dd7a485aaa3c65909af55bf2876f1edeb401eed641f6dc70e53c7598b99f3ab` |
| v3 | `48edcf271de6d13946102b589f06031e369586a77c36468e3755880efd15457f` |

Each bundle contains the same aggregate table. None contains dataset IDs,
task IDs, versions, a snapshot date, a census script, or per-dimension output.
No code URL is present in the paper or the authors' publication listing.

The OpenReview API, PDF, and candidate supplementary-material endpoints
returned HTTP 403 challenge responses during this audit. An interactive
browser runtime was unavailable. This access limitation is recorded, but it is
not the only blocker: the complete arXiv source bundles themselves omit the
needed protocol and manifest.

## Current OpenML diagnostic

- Official endpoint:
  `https://www.openml.org/api/v1/json/data/list/number_classes/2/limit/100000`
- Retrieved: `2026-07-23T05:47:39Z`
- Frozen response:
  `openml_binary_catalog_2026-07-23.json`
- SHA-256:
  `5485ea844e865020734edc21a48fd6ff3ef6755eb90b1cd9d75e3d0adf98e208`
- It lists 1,639 currently active datasets with `NumberOfClasses=2`.

Metadata for all 1,639 dataset IDs was fetched from the official
`/api/v1/json/data/{did}` endpoint. `current_dataset_metadata.csv` records the
dataset name, version, target, upload date, dimensions, sample size, dataset
MD5, and the SHA-256 of each metadata response. The CSV SHA-256 is
`66a9346a6d95f0d42fec180033a3713fda9dc59cc1149d45bab143e85f1c7a4e`.

The current catalog has a metadata sum of 1,199,438 total features and
1,143,087 numeric features. Restricting currently active datasets by upload
date through the arXiv-v1 submission day produces neither 933,440 total nor
933,440 numeric features. This establishes catalog/protocol drift, but it does
not falsify a historical aggregate.

## Missing identifying information

The release does not specify the historical dataset/task/version IDs, snapshot
timestamp, target and ignored-column rules, feature typing, missing-value
handling, repeated-value/tie handling, unavailable-download exclusions, or
implementation. Those choices can change all three reported counts.

Verdict: **BLOCKED**. Source arithmetic is not an independent reproduction,
and a present-day catalog is not a valid replacement for the unidentified
historical population.
