#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path


def verify(path: Path) -> None:
    result = json.loads(path.read_text())
    failures = []
    if result.get("verdict") != "VERIFIED":
        failures.append("verdict is not VERIFIED")
    if result.get("tree_counts") != [100, 300, 1000, 3000, 10000, 30000]:
        failures.append("tree-count sweep changed")
    if result.get("ensembles", 0) < 18:
        failures.append("too few independent ensembles")
    if result.get("total_trees_generated", 0) < 540000:
        failures.append("insufficient actual trees")
    fit = result.get("fit", {})
    slope = fit.get("slope", 0.0)
    interval = fit.get("slope_ci95", [0.0, 0.0])
    if not (-1.15 < slope < -0.85 and interval[0] < -1.0 < interval[1]):
        failures.append("T^-1 MSE rate not supported")
    if fit.get("log_r2", 0.0) < 0.9:
        failures.append("MSE rate fit is weak")
    if not result.get("mean_mse_strictly_decreasing"):
        failures.append("mean MSE does not strictly decrease")
    if result.get("mse_reduction_100_to_30000", 0.0) <= 100.0:
        failures.append("MSE reduction is too small")
    if result.get("hoeffding_bound_violations") != 0:
        failures.append("observed Proposition 3.1 bound violation")
    if not result.get("negative_control_is_flat"):
        failures.append("nonconcentrating control is not flat")
    if failures:
        raise SystemExit("; ".join(failures))


def main() -> None:
    path = (
        Path(sys.argv[1])
        if len(sys.argv) > 1
        else Path(".openresearch/artifacts/claim_5/summary.json")
    )
    verify(path)
    print("Claim 5 evidence verified")


if __name__ == "__main__":
    main()
