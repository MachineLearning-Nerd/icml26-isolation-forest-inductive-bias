#!/usr/bin/env python3
from __future__ import annotations

import csv
import hashlib
import json
import sys
from pathlib import Path


def file_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while True:
            block = handle.read(65536)
            if not block:
                break
            digest.update(block)
    return digest.hexdigest()


def quality(dataset: dict[str, object], wanted: str) -> int:
    for item in dataset.get("quality", []):
        if item.get("name") == wanted:
            return int(float(item.get("value") or 0))
    return 0


def main() -> None:
    if len(sys.argv) != 5:
        raise SystemExit(
            "usage: independent_check_claim_6.py "
            "CATALOG.json METADATA.csv SUMMARY.json OUTPUT.json"
        )
    catalog_path, metadata_path, summary_path, output_path = map(
        Path, sys.argv[1:]
    )
    catalog = json.loads(catalog_path.read_text())["data"]["dataset"]
    summary = json.loads(summary_path.read_text())
    with metadata_path.open(newline="") as handle:
        metadata = list(csv.DictReader(handle))

    feature_total = 0
    numeric_total = 0
    symbolic_total = 0
    catalog_ids = set()
    for dataset in catalog:
        catalog_ids.add(int(dataset["did"]))
        feature_total += quality(dataset, "NumberOfFeatures")
        numeric_total += quality(dataset, "NumberOfNumericFeatures")
        symbolic_total += quality(dataset, "NumberOfSymbolicFeatures")
    metadata_ids = {int(row["did"]) for row in metadata}
    current = summary["current_official_openml_snapshot"]
    checks = {
        "catalog_rows_match": len(catalog)
        == current["active_binary_datasets"]
        == 1639,
        "metadata_rows_match": len(metadata) == 1639,
        "id_sets_match": catalog_ids == metadata_ids,
        "feature_total_matches": feature_total
        == current["number_of_features_sum"]
        == 1_199_438,
        "numeric_total_matches": numeric_total
        == current["number_of_numeric_features_sum"]
        == 1_143_087,
        "symbolic_total_matches": symbolic_total
        == current["number_of_symbolic_features_sum"]
        == 27_220,
        "catalog_hash_matches": file_hash(catalog_path)
        == summary["catalog_sha256"],
        "metadata_hash_matches": file_hash(metadata_path)
        == summary["metadata_csv_sha256"],
        "paper_arithmetic_matches": (
            summary["paper_counts"]["total"]
            - summary["paper_counts"]["valid"]
            == 2689
            and summary["paper_counts"]["valid"]
            - summary["paper_counts"]["successful"]
            == 13
        ),
        "blocked_not_promoted": summary["verdict"] == "BLOCKED",
        "historical_inputs_absent": (
            not summary["exact_historical_manifest_present"]
            and not summary["full_feature_values_present"]
            and not summary["kappa_recomputed_for_historical_dimensions"]
        ),
    }
    result = {
        "implementation": (
            "independent scalar JSON/CSV parser; no imports from Claim 6 code"
        ),
        "checks": checks,
        "passed": all(checks.values()),
    }
    output_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, sort_keys=True))
    if not result["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
