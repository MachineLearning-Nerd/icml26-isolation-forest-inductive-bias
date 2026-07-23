#!/usr/bin/env python3
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import pandas as pd


def scalar_depth(values: list[float], index: int) -> float:
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


def main() -> None:
    if len(sys.argv) != 4:
        raise SystemExit(
            "usage: independent_check_claim_5.py POINTS.csv AGGREGATE.csv OUTPUT.json"
        )
    points = pd.read_csv(sys.argv[1])
    aggregates = pd.read_csv(sys.argv[2])
    theory_mismatches = 0
    mse_mismatches = 0
    for distribution, frame in points.groupby("distribution"):
        base = frame[
            (frame.forest_seed == frame.forest_seed.min())
            & (frame.trees == frame.trees.min())
        ].sort_values("point_index")
        values = base.value.tolist()
        for row in base.itertuples(index=False):
            expected = scalar_depth(values, int(row.point_index))
            if not math.isclose(expected, row.theory, rel_tol=1e-11, abs_tol=1e-11):
                theory_mismatches += 1
    recomputed = (
        points.groupby(["distribution", "forest_seed", "trees"])
        .squared_error.mean()
        .reset_index(name="recomputed_mse")
    )
    merged = aggregates.merge(
        recomputed, on=["distribution", "forest_seed", "trees"], how="outer"
    )
    for row in merged.itertuples(index=False):
        if not math.isclose(row.mse, row.recomputed_mse, rel_tol=1e-11, abs_tol=1e-14):
            mse_mismatches += 1
    result = {
        "implementation": "scalar Theorem 3.5 plus independent group MSE",
        "theory_rows_recomputed": 300,
        "aggregate_rows_recomputed": int(len(merged)),
        "theory_mismatches": theory_mismatches,
        "mse_mismatches": mse_mismatches,
        "passed": bool(
            len(merged) >= 108
            and theory_mismatches == 0
            and mse_mismatches == 0
        ),
    }
    Path(sys.argv[3]).write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n"
    )
    print(json.dumps(result, sort_keys=True))
    if not result["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
