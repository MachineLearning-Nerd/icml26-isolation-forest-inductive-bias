#!/usr/bin/env python3
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd


def depths(values: np.ndarray) -> np.ndarray:
    values = np.sort(np.asarray(values, dtype=float))
    answer = []
    for index, value in enumerate(values):
        left = sum(
            (values[j] - values[j - 1]) / (value - values[j - 1])
            for j in range(1, index + 1)
        )
        right = sum(
            (values[j] - values[j - 1]) / (values[j] - value)
            for j in range(index + 1, len(values))
        )
        answer.append(left + right)
    return np.asarray(answer)


def scores(values: np.ndarray, k: int) -> np.ndarray:
    result = []
    for i, value in enumerate(values):
        distances = sorted(
            abs(float(value) - float(other))
            for j, other in enumerate(values)
            if i != j
        )
        result.append(sum(distances[:k]) / k)
    return np.asarray(result)


def detected(gaps: np.ndarray, separation: float, method: str, k: int) -> bool:
    points = np.r_[-separation, 0.0, np.cumsum(gaps)]
    if method == "iforest":
        value = depths(points)
        return bool(value[0] < np.min(value[1:]))
    value = scores(points, k)
    return bool(value[0] > np.max(value[1:]))


def threshold(
    gaps: np.ndarray, method: str, k: int, paper_boundary: float
) -> float:
    low = 0.0
    high = paper_boundary * 1.25
    while not detected(gaps, high, method, k):
        high *= 2.0
    for _ in range(80):
        middle = (low + high) / 2.0
        if detected(gaps, middle, method, k):
            high = middle
        else:
            low = middle
    return high


def main() -> None:
    if len(sys.argv) != 3:
        raise SystemExit("usage: independent_check_claim_2.py RAW.csv OUTPUT.json")
    raw = pd.read_csv(sys.argv[1])
    mismatches = 0
    assumption_violations = 0
    sufficiency_violations = 0
    necessity_counterexamples = 0
    for row in raw.itertuples(index=False):
        gaps = np.asarray(json.loads(row.normal_gaps_json), dtype=float)
        observed_u = float(np.max(gaps))
        observed_l = float(np.min(gaps))
        observed_kappa = observed_u / observed_l
        observed_delta = observed_u - observed_l
        if not math.isclose(observed_u, row.u, rel_tol=0.0, abs_tol=1e-12):
            mismatches += 1
        if not math.isclose(observed_l, row.l, rel_tol=0.0, abs_tol=1e-12):
            mismatches += 1
        if not math.isclose(observed_kappa, row.kappa, rel_tol=1e-12):
            mismatches += 1
        if not math.isclose(observed_delta, row.delta, rel_tol=1e-12):
            mismatches += 1
        if observed_kappa < math.sqrt(row.n + 3):
            assumption_violations += 1
        expected_boundary = (
            observed_u * observed_kappa
            if row.method == "iforest"
            else observed_u + (row.k - 1) * observed_delta / 2.0
        )
        if not math.isclose(expected_boundary, row.paper_boundary, rel_tol=1e-12):
            mismatches += 1
        independent_threshold = threshold(
            gaps, row.method, int(row.k), expected_boundary
        )
        if not math.isclose(
            independent_threshold, row.direct_threshold, rel_tol=1e-9, abs_tol=1e-10
        ):
            mismatches += 1
        if not detected(
            gaps, 1.001 * expected_boundary, row.method, int(row.k)
        ):
            sufficiency_violations += 1
        if row.method == "knn" and detected(
            gaps, 0.9 * expected_boundary, row.method, int(row.k)
        ):
            necessity_counterexamples += 1
    result = {
        "rows_recomputed": int(len(raw)),
        "mismatches": mismatches,
        "assumption_violations": assumption_violations,
        "sufficiency_violations": sufficiency_violations,
        "knn_literal_necessity_counterexamples_at_90pct_boundary": (
            necessity_counterexamples
        ),
        "implementation": "independent scalar loops; no imports from claim2_exact",
        "passed": bool(
            mismatches == 0
            and assumption_violations == 0
            and sufficiency_violations == 0
            and necessity_counterexamples > 0
        ),
    }
    Path(sys.argv[2]).write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, sort_keys=True))
    if not result["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
