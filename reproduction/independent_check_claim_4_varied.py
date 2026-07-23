#!/usr/bin/env python3
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd


def scalar_knn(values: np.ndarray, index: int, k: int) -> float:
    distances = sorted(
        abs(float(values[index] - values[j]))
        for j in range(len(values))
        if j != index
    )
    return sum(distances[:k]) / k


def main() -> None:
    if len(sys.argv) != 3:
        raise SystemExit(
            "usage: independent_check_claim_4_varied.py RAW.csv OUTPUT.json"
        )
    rows = pd.read_csv(sys.argv[1])
    sample = rows[
        (rows.method == "knn")
        & (rows.n1 <= 9)
        & (rows.seed == 0)
    ]
    mismatches = 0
    for row in sample.itertuples(index=False):
        if not row.kappa >= math.sqrt(row.n0 + row.n1 + 3):
            mismatches += 1
        if not (row.k / row.n1 > 1.0 and row.k / row.n0 < 1.0):
            mismatches += 1
        # Reconstruct the separately seeded clusters without importing route B.
        def gaps(size: int, stream: int) -> np.ndarray:
            rng = np.random.default_rng(74000 + 101 * int(row.seed) + stream)
            values = np.exp(
                rng.uniform(0.0, math.log(row.kappa), size=size - 1)
            )
            values[0], values[1] = 1.0, row.kappa
            return values[rng.permutation(size - 1)]

        anomaly = np.r_[0.0, np.cumsum(gaps(int(row.n1), 1))]
        normal = anomaly[-1] + row.direct_threshold + np.r_[
            0.0, np.cumsum(gaps(int(row.n0), 2))
        ]
        points = np.r_[anomaly, normal]
        anomaly_min = min(
            scalar_knn(points, index, int(row.k))
            for index in range(int(row.n1))
        )
        normal_max = max(
            scalar_knn(points, index, int(row.k))
            for index in range(int(row.n1), len(points))
        )
        if anomaly_min + 1e-6 < normal_max:
            mismatches += 1
    result = {
        "implementation": "independent scalar sorted-distance k-NN",
        "rows_recomputed": int(len(sample)),
        "mismatches": mismatches,
        "passed": bool(len(sample) >= 8 and mismatches == 0),
    }
    Path(sys.argv[2]).write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n"
    )
    print(json.dumps(result, sort_keys=True))
    if not result["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
