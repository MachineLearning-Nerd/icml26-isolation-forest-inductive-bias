#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd


def alternate_tree(values: np.ndarray, rng: np.random.Generator) -> np.ndarray:
    values = np.sort(np.asarray(values, dtype=float))
    result = np.zeros(len(values), dtype=int)
    pending = [(0, len(values) - 1, 0)]
    while pending:
        low, high, depth = pending.pop()
        if low == high:
            result[low] = depth
            continue
        split_value = rng.uniform(values[low], values[high])
        split = int(np.searchsorted(values, split_value, side="right") - 1)
        split = min(max(split, low), high - 1)
        pending.extend(
            [(low, split, depth + 1), (split + 1, high, depth + 1)]
        )
    return result


def margin(gaps: np.ndarray, separation: float, seed: int) -> float:
    values = np.r_[-separation, 0.0, np.cumsum(gaps)]
    rng = np.random.default_rng(seed)
    total = np.zeros(len(values), dtype=float)
    for _ in range(1600):
        total += alternate_tree(values, rng)
    mean = total / 1600
    return float(np.min(mean[1:]) - mean[0])


def independent_threshold(
    gaps: np.ndarray, boundary: float, seed: int
) -> float:
    low = 0.0
    high = boundary * 1.25
    while margin(gaps, high, seed) <= 0.0:
        high *= 2.0
    for _ in range(9):
        middle = (low + high) / 2.0
        if margin(gaps, middle, seed) > 0.0:
            high = middle
        else:
            low = middle
    return high


def main() -> None:
    if len(sys.argv) != 3:
        raise SystemExit(
            "usage: independent_check_claim_2_randomized.py RAW.csv OUTPUT.json"
        )
    rows = pd.read_csv(sys.argv[1])
    sample = rows[(rows.u == 1.0)].copy()
    measured = []
    for row in sample.itertuples(index=False):
        gaps = np.asarray(json.loads(row.normal_gaps_json), dtype=float)
        measured.append(
            independent_threshold(
                gaps, row.paper_boundary, row.forest_seed + 9000
            )
        )
    sample["independent_threshold"] = measured
    correlation = float(
        sample[["exact_threshold", "independent_threshold"]].corr().iloc[0, 1]
    )
    normalized_mae = float(
        (
            np.abs(sample.independent_threshold - sample.exact_threshold)
            / sample.u
        ).mean()
    )
    result = {
        "implementation": "independent uniform-split simulator",
        "rows_checked": int(len(sample)),
        "trees_per_bisection_point": 1600,
        "bisection_steps": 9,
        "independent_exact_threshold_correlation": correlation,
        "independent_exact_normalized_mae": normalized_mae,
        "threshold_rows": sample[
            [
                "kappa",
                "seed",
                "exact_threshold",
                "independent_threshold",
            ]
        ].to_dict(orient="records"),
        "passed": bool(
            len(sample) >= 12
            and correlation > 0.9
            and normalized_mae < 0.15
        ),
    }
    Path(sys.argv[2]).write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, sort_keys=True))
    if not result["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
