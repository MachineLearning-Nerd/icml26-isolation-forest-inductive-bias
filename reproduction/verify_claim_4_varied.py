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
        failures.append("paper assumptions invalid")
    if not result.get("exact_density_metrics"):
        failures.append("within-cluster density metrics are not exact")
    if not result.get("asymptotic_family_valid"):
        failures.append("n1=o(n0) family invalid")
    if len(result.get("n1_values", [])) < 5:
        failures.append("counterexample sequence too short")
    if len(result.get("deterministic_seeds", [])) < 4:
        failures.append("too few counterexample arrangements")
    if result.get("counterexample_families", 0) < 20:
        failures.append("too few limiting counterexamples")
    if result.get("rows", 0) < 60:
        failures.append("too few finite separation checks")
    if not result.get("all_finite_large_separations_fail_detection"):
        failures.append("a finite large-separation check detects all anomalies")
    if not result.get("all_infinite_separation_limits_fail_detection"):
        failures.append("no infinite-separation contradiction")
    if result.get("least_absolute_infinite_failure_margin", 0.0) <= 1e-8:
        failures.append("limiting contradiction is not strict")
    if failures:
        raise SystemExit("; ".join(failures))


def main() -> None:
    path = (
        Path(sys.argv[1])
        if len(sys.argv) > 1
        else Path(".openresearch/artifacts/claim_4_route_b/summary.json")
    )
    verify(path)
    print("Claim 4 counterexample evidence verified")


if __name__ == "__main__":
    main()
