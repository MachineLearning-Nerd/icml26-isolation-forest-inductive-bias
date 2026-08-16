# Paper source audit

## Primary source

- Title: Theoretical Investigation on Inductive Bias of Isolation Forest
- Authors: Qin-Cheng Zheng; Shao-Qun Zhang; Shen-Huan Lyu; Yuan Jiang;
  Zhi-Hua Zhou
- arXiv: https://arxiv.org/abs/2505.12825
- Version used for the local paper copy: v3, 27 January 2026
- Local PDF SHA-256: 95df6b6b38e6c65cd16d701175e354736e2fe772496010d57ba26a158f4c1fca
- Browser-readable source: https://ar5iv.labs.arxiv.org/html/2505.12825
- Browser-readable source SHA-256: e716edebd1c4b9ee6eb33a2f996d6232decafbc753ee9eb2fcdfadf280d74cac

The paper copy has 25 pages and states that no implementation or code URL is
provided. All code in this repository is therefore independent.

## Contract anchors

- Proposition 3.1: pointwise Hoeffding concentration of empirical tree depth.
- Theorem 3.5: the closed-form expected depth as left- and right-side
  adjacent-gap ratios.
- Definition 4.1: U is the maximum adjacent spacing, L the minimum,
  κ = U/L, and δ = U − L.
- Assumption 4.2: κ ≥ sqrt(n + 3).
- Theorems 4.3–4.5: marginal single-anomaly iForest and k-NN bounds.
- Theorems 4.6–4.7: central single-anomaly thresholds
  Theta(sqrt(n0 κ)) and Theta(kδ).
- Theorems 4.8–4.9: marginal clustered-anomaly thresholds
  Theta(n1²κ) and Theta(kδ).
- Section 4 / Table 1: 930,738 successful, 930,751 valid, 933,440 total
  OpenML dimensions.

The claim-specific source anchors, quantifier interpretations, and known
definition/proof mismatches are preserved in the corresponding files under
.openresearch/artifacts/.

## Version audit for the OpenML statement

The public arXiv e-print bundles were independently hashed:

| Source | SHA-256 |
|---|---|
| arXiv v1 e-print | 00749d4d6606d7d578abb914a37ceda9ae35bdf94a3fd084fd34f4a8ac9cac71 |
| arXiv v2 e-print | 1dd7a485aaa3c65909af55bf2876f1edeb401eed641f6dc70e53c7598b99f3ab |
| arXiv v3 e-print | 48edcf271de6d13946102b589f06031e369586a77c36468e3755880efd15457f |

None contains dataset IDs, task IDs, versions, a census implementation, a
snapshot timestamp, or per-dimension output. The missing information is why
Claim 6 is blocked instead of being labeled reproduced or falsified.

