#!/usr/bin/env python3
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import pandas as pd


def scalar_depth_from_gaps(gaps: list[float], index: int) -> float:
    points = [0.0]
    for gap in gaps:
        points.append(points[-1] + gap)
    result = 0.0
    for j in range(1, index + 1):
        result += gaps[j - 1] / (points[index] - points[j - 1])
    for j in range(index + 1, len(points)):
        result += gaps[j - 1] / (points[j] - points[index])
    return result


def main() -> None:
    if len(sys.argv) != 3:
        raise SystemExit(
            "usage: independent_check_claim_4_varied.py RAW.csv OUTPUT.json"
        )
    rows = pd.read_csv(sys.argv[1]).drop_duplicates(["n1", "seed"])
    mismatches = 0
    maximum_difference = 0.0
    for row in rows.itertuples(index=False):
        n1, n0, seed = int(row.n1), int(row.n0), int(row.seed)
        if n0 != n1**2 or not math.isclose(row.kappa, 100.0 * n0):
            mismatches += 1
        if not row.kappa >= math.sqrt(n0 + n1 + 3):
            mismatches += 1
        positions = (0, (n1 - 2) // 2, (n1 - 1) // 2, n1 - 2)
        a_gaps = [1.0] * (n1 - 1)
        a_gaps[positions[seed]] = row.kappa
        b_gaps = [row.kappa] + [1.0] * (n0 - 2)
        anomaly_limit = (
            max(
                scalar_depth_from_gaps(a_gaps, index)
                for index in range(n1)
            )
            + 1.0
        )
        normal_limit = scalar_depth_from_gaps(b_gaps, 0) + 1.0
        margin = normal_limit - anomaly_limit
        difference = abs(margin - row.infinite_failure_margin)
        maximum_difference = max(maximum_difference, difference)
        if difference > 1e-9 or margin >= -1e-8:
            mismatches += 1
    result = {
        "implementation": "independent scalar Theorem 3.5 limit",
        "rows_recomputed": int(len(rows)),
        "mismatches": mismatches,
        "maximum_absolute_margin_difference": maximum_difference,
        "passed": bool(len(rows) >= 20 and mismatches == 0),
    }
    Path(sys.argv[2]).write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n"
    )
    print(json.dumps(result, sort_keys=True))
    if not result["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
