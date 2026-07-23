#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path


def verify(path: Path) -> None:
    result = json.loads(path.read_text())
    failures = []
    if result.get("verdict") != "FALSIFIED":
        failures.append("verdict is not FALSIFIED")
    if not result.get("all_assumptions_valid"):
        failures.append("theorem assumptions are not all valid")
    if result.get("iforest_sufficiency_violations") != 0:
        failures.append("iForest U*kappa sufficiency has violations")
    if result.get("knn_sufficiency_violations") != 0:
        failures.append("k-NN stated boundary has sufficiency violations")
    if result.get("knn_literal_necessity_counterexamples_at_90pct_boundary", 0) < 1:
        failures.append("no below-boundary k-NN counterexample")
    if result.get("normal_configurations", 0) < 100:
        failures.append("too few normal configurations")
    if len(result.get("deterministic_seeds", [])) < 8:
        failures.append("too few deterministic seeds")
    if not result.get("central_negative_control_distinct"):
        failures.append("central negative control is not distinct")
    if failures:
        raise SystemExit("; ".join(failures))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "summary",
        nargs="?",
        type=Path,
        default=Path(".openresearch/artifacts/claim_2/summary.json"),
    )
    args = parser.parse_args()
    verify(args.summary)
    print("Claim 2 evidence package verified")


if __name__ == "__main__":
    main()
