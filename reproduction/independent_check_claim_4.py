#!/usr/bin/env python3
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd


def scalar_depth(values: np.ndarray, index: int) -> float:
    result = 0.0
    for j in range(1, index + 1):
        result += (values[j] - values[j - 1]) / (
            values[index] - values[j - 1]
        )
    for j in range(index + 1, len(values)):
        result += (values[j] - values[j - 1]) / (
            values[j] - values[index]
        )
    return result


def iforest_margin(n1: int, n0: int, kappa: float, separation: float) -> float:
    anomaly_gaps = np.full(n1 - 1, kappa, dtype=float)
    anomaly_gaps[0] = anomaly_gaps[-1] = 1.0
    normal_gaps = np.full(n0 - 1, kappa, dtype=float)
    normal_gaps[0] = normal_gaps[-1] = 1.0
    anomalies = np.r_[0.0, np.cumsum(anomaly_gaps)]
    normals = anomalies[-1] + separation + np.r_[0.0, np.cumsum(normal_gaps)]
    values = np.r_[anomalies, normals]
    anomaly_max = max(scalar_depth(values, i) for i in range(n1))
    normal_min = min(
        scalar_depth(values, i) for i in (n1, len(values) - 1)
    )
    return normal_min - anomaly_max


def threshold(n1: int, n0: int, kappa: float, scale: float) -> float:
    low, high = 0.0, scale
    while iforest_margin(n1, n0, kappa, high) <= 0.0:
        high *= 2.0
    for _ in range(44):
        middle = (low + high) / 2.0
        if iforest_margin(n1, n0, kappa, middle) > 0.0:
            high = middle
        else:
            low = middle
    return high


def main() -> None:
    if len(sys.argv) != 3:
        raise SystemExit("usage: independent_check_claim_4.py RAW.csv OUTPUT.json")
    rows = pd.read_csv(sys.argv[1])
    sample = rows[rows.n1 <= 33]
    mismatches = 0
    for row in sample.itertuples(index=False):
        if row.k != math.floor(row.n1**1.5) or row.n0 != row.n1**2:
            mismatches += 1
        if not row.kappa >= math.sqrt(row.n0 + row.n1 + 3):
            mismatches += 1
        measured = threshold(
            int(row.n1),
            int(row.n0),
            float(row.kappa),
            float(row.iforest_predicted_scale),
        )
        if not math.isclose(
            measured,
            row.iforest_threshold,
            rel_tol=1e-9,
            abs_tol=1e-8,
        ):
            mismatches += 1
    result = {
        "implementation": "independent scalar Theorem 3.5 loops",
        "rows_recomputed": int(len(sample)),
        "mismatches": mismatches,
        "passed": bool(len(sample) >= 12 and mismatches == 0),
    }
    Path(sys.argv[2]).write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, sort_keys=True))
    if not result["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
