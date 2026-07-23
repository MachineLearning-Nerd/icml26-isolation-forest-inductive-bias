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
    if not result.get("all_assumptions_valid"):
        failures.append("assumptions invalid")
    if not result.get("constraint_families_valid"):
        failures.append("asymptotic k families invalid")
    if result.get("iforest_rows", 0) < 32:
        failures.append("too few iForest rows")
    if result.get("knn_rows", 0) < 64:
        failures.append("too few k-NN rows")
    if len(result.get("seeds", [])) < 4:
        failures.append("too few deterministic seeds")
    if len(result.get("n1_values", [])) < 4:
        failures.append("n1 sweep too small")
    if not result.get("full_extrema_evaluated"):
        failures.append("not all point extrema were evaluated")
    if not result.get("invalid_constraint_controls_failed"):
        failures.append("constraint controls did not fail")
    if result.get("iforest_fixed_prediction", {}).get("log_r2", 0.0) < 0.9:
        failures.append("fixed n1^2*kappa prediction is weak")
    if result.get("knn_fixed_prediction", {}).get("log_r2", 0.0) < 0.9:
        failures.append("fixed k*delta prediction is weak")
    if failures:
        raise SystemExit("; ".join(failures))


def main() -> None:
    path = (
        Path(sys.argv[1])
        if len(sys.argv) > 1
        else Path(".openresearch/artifacts/claim_4_route_b/summary.json")
    )
    verify(path)
    print("Claim 4 varied evidence verified")


if __name__ == "__main__":
    main()
