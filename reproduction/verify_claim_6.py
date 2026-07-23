#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path


def verify(path: Path) -> None:
    result = json.loads(path.read_text())
    failures = []
    if result.get("verdict") not in ("VERIFIED", "FALSIFIED"):
        failures.append("claim has no VERIFIED/FALSIFIED verdict")
    if not result.get("exact_historical_manifest_present"):
        failures.append("exact historical OpenML manifest is absent")
    if not result.get("full_feature_values_present"):
        failures.append("historical feature values are absent")
    if not result.get("kappa_recomputed_for_historical_dimensions"):
        failures.append("historical per-dimension kappa was not recomputed")
    if result.get("verdict") == "VERIFIED":
        counts = result.get("recomputed_counts", {})
        if counts != {"successful": 930738, "valid": 930751, "total": 933440}:
            failures.append("the exact published counts were not reproduced")
    if result.get("verdict") == "FALSIFIED":
        if not result.get("assumption_satisfying_counterexample"):
            failures.append("no assumption-satisfying contradiction is present")
    if failures:
        raise SystemExit("; ".join(failures))


def main() -> None:
    path = (
        Path(sys.argv[1])
        if len(sys.argv) > 1
        else Path(".openresearch/artifacts/claim_6/summary.json")
    )
    verify(path)
    print("Claim 6 evidence verified")


if __name__ == "__main__":
    main()
