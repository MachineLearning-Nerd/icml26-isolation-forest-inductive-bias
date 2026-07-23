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
    if not result.get("constraint_family_valid"):
        failures.append("omega(n1)<=k<=o(n0) family invalid")
    if len(result.get("n1_values", [])) < 5:
        failures.append("n1 sweep is too small")
    if result.get("rows", 0) < 15:
        failures.append("too few threshold rows")
    if not result.get("invalid_constraint_controls_failed"):
        failures.append("invalid constraint controls did not fail")
    if result.get("iforest_fit", {}).get("log_r2", 0.0) < 0.95:
        failures.append("iForest scaling fit is weak")
    if result.get("knn_fit", {}).get("log_r2", 0.0) < 0.95:
        failures.append("k-NN scaling fit is weak")
    if failures:
        raise SystemExit("; ".join(failures))


def main() -> None:
    path = (
        Path(sys.argv[1])
        if len(sys.argv) > 1
        else Path(".openresearch/artifacts/claim_4_route_a/summary.json")
    )
    verify(path)
    print("Claim 4 evidence verified")


if __name__ == "__main__":
    main()
