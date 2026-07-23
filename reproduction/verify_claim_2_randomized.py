#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path


def verify(path: Path) -> None:
    result = json.loads(path.read_text())
    failures = []
    if result.get("verdict") != "FALSIFIED":
        failures.append("verdict is not FALSIFIED")
    if not result.get("all_assumptions_valid"):
        failures.append("assumptions invalid")
    if result.get("forest_rows", 0) < 30:
        failures.append("too few randomized forest thresholds")
    if len(result.get("forest_seeds", [])) < 4:
        failures.append("too few forest seeds")
    if result.get("empirical_exact_threshold_correlation", 0.0) <= 0.98:
        failures.append("random forests do not reproduce exact thresholds")
    if result.get("empirical_exact_normalized_mae", 1.0) >= 0.15:
        failures.append("random forest threshold error is too large")
    if result.get("knn_literal_necessity_counterexamples_at_90pct_boundary", 0) < 1:
        failures.append("no literal k-NN necessity counterexample")
    if not result.get("central_negative_control_distinct"):
        failures.append("central negative control substituted for marginal geometry")
    if failures:
        raise SystemExit("; ".join(failures))


def main() -> None:
    path = (
        Path(sys.argv[1])
        if len(sys.argv) > 1
        else Path(".openresearch/artifacts/claim_2_route_b/summary.json")
    )
    verify(path)
    print("Randomized Claim 2 evidence verified")


if __name__ == "__main__":
    main()
