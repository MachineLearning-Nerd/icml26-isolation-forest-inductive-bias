from __future__ import annotations

import csv
import hashlib
import json
import math
import os
import platform
import subprocess
import sys
import time
from pathlib import Path


PAPER_COUNTS = {
    "successful": 930_738,
    "valid": 930_751,
    "total": 933_440,
}
CATALOG_SHA256 = (
    "5485ea844e865020734edc21a48fd6ff3ef6755eb90b1cd9d75e3d0adf98e208"
)
METADATA_CSV_SHA256 = (
    "e6f817a5502dacc33b56fe3a277c47da9a237c224c4f83c31741aab107b56ff5"
)
PAPER_V1_DAY_END = "2025-05-19T23:59:59"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def qualities(dataset: dict[str, object]) -> dict[str, str]:
    return {
        str(item["name"]): str(item["value"])
        for item in dataset.get("quality", [])
    }


def integer_quality(dataset: dict[str, object], name: str) -> int:
    value = qualities(dataset).get(name, "0")
    return int(float(value or 0))


def read_metadata(path: Path) -> list[dict[str, str]]:
    with path.open(newline="") as handle:
        return list(csv.DictReader(handle))


def cumulative_cutoff(
    rows: list[dict[str, str]], field: str, cutoff: str
) -> dict[str, object]:
    selected = [row for row in rows if row["upload_date"] <= cutoff]
    return {
        "cutoff": cutoff,
        "datasets": len(selected),
        field: sum(int(row[field]) for row in selected),
    }


def closest_cumulative(
    rows: list[dict[str, str]], field: str, target: int
) -> dict[str, object]:
    running = 0
    best: dict[str, object] | None = None
    for row in sorted(rows, key=lambda item: (item["upload_date"], int(item["did"]))):
        running += int(row[field])
        candidate = {
            "absolute_difference": abs(running - target),
            "cumulative": running,
            "upload_date": row["upload_date"],
            "did": int(row["did"]),
            "name": row["name"],
        }
        if best is None or candidate["absolute_difference"] < best["absolute_difference"]:
            best = candidate
    assert best is not None
    best["exact_match"] = best["absolute_difference"] == 0
    return best


def threshold_control() -> tuple[list[dict[str, object]], dict[str, object]]:
    dimensions = {
        "wide_endpoint_gap": [0.0, 1.0, 2.0, 3.0, 10.0],
        "uniform_spacing": [0.0, 1.0, 2.0, 3.0, 4.0],
        "moderate_ratio": [0.0, 1.0, 2.0, 4.0, 8.0],
    }
    rows = []
    normal_threshold = math.sqrt(8.0)
    mutated_threshold = 2.0 * normal_threshold
    for name, values in dimensions.items():
        gaps = [right - left for left, right in zip(values, values[1:])]
        kappa = max(gaps) / min(gaps)
        rows.append(
            {
                "fixture_dimension": name,
                "n": len(values),
                "kappa": kappa,
                "paper_threshold": normal_threshold,
                "paper_threshold_pass": kappa >= normal_threshold,
                "mutated_threshold": mutated_threshold,
                "mutated_threshold_pass": kappa >= mutated_threshold,
                "scope": "control-only; not OpenML claim evidence",
            }
        )
    normal_count = sum(bool(row["paper_threshold_pass"]) for row in rows)
    mutated_count = sum(bool(row["mutated_threshold_pass"]) for row in rows)
    result = {
        "normal_threshold_pass_count": normal_count,
        "mutated_threshold_pass_count": mutated_count,
        "count_changed": normal_count != mutated_count,
        "scope": (
            "Unit-level mutation control for the threshold/counting path only. "
            "It is deliberately excluded from evidence for the OpenML census."
        ),
    }
    return rows, result


def write_json(path: Path, payload: object) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")


def run_claim6_audit(output_dir: Path) -> dict[str, object]:
    started = time.perf_counter()
    artifact_dir = Path(".openresearch/artifacts/claim_6")
    catalog_path = artifact_dir / "openml_binary_catalog_2026-07-23.json"
    metadata_path = artifact_dir / "current_dataset_metadata.csv"
    output_dir.mkdir(parents=True, exist_ok=True)

    catalog_hash = sha256(catalog_path)
    metadata_hash = sha256(metadata_path)
    catalog = json.loads(catalog_path.read_text())["data"]["dataset"]
    metadata = read_metadata(metadata_path)
    catalog_ids = {int(row["did"]) for row in catalog}
    metadata_ids = {int(row["did"]) for row in metadata}

    current = {
        "active_binary_datasets": len(catalog),
        "number_of_features_sum": sum(
            integer_quality(row, "NumberOfFeatures") for row in catalog
        ),
        "number_of_numeric_features_sum": sum(
            integer_quality(row, "NumberOfNumericFeatures") for row in catalog
        ),
        "number_of_symbolic_features_sum": sum(
            integer_quality(row, "NumberOfSymbolicFeatures") for row in catalog
        ),
        "number_of_instances_sum": sum(
            integer_quality(row, "NumberOfInstances") for row in catalog
        ),
        "all_status_active": all(row.get("status") == "active" for row in catalog),
        "all_number_of_classes_two": all(
            integer_quality(row, "NumberOfClasses") == 2 for row in catalog
        ),
        "metadata_id_set_matches_catalog": catalog_ids == metadata_ids,
    }
    cutoffs = [
        cumulative_cutoff(metadata, "NumberOfFeatures", PAPER_V1_DAY_END),
        cumulative_cutoff(metadata, "NumberOfNumericFeatures", PAPER_V1_DAY_END),
    ]
    closest = {
        "NumberOfFeatures": closest_cumulative(
            metadata, "NumberOfFeatures", PAPER_COUNTS["total"]
        ),
        "NumberOfNumericFeatures": closest_cumulative(
            metadata, "NumberOfNumericFeatures", PAPER_COUNTS["total"]
        ),
    }
    fixture_rows, mutation = threshold_control()
    with (artifact_dir / "threshold_mutation_control.csv").open(
        "w", newline=""
    ) as handle:
        writer = csv.DictWriter(handle, fieldnames=list(fixture_rows[0]))
        writer.writeheader()
        writer.writerows(fixture_rows)
    write_json(artifact_dir / "threshold_mutation_result.json", mutation)
    write_json(artifact_dir / "historical_cutoff_checks.json", cutoffs)

    missing_protocol = [
        "historical dataset/task/version identifiers",
        "snapshot retrieval timestamp",
        "target-column and ignored-column rules",
        "numeric versus symbolic feature inclusion rule",
        "missing-value handling",
        "repeated-value and floating-point tie handling",
        "download-failure and unavailable-dataset exclusions",
        "census implementation",
    ]
    summary: dict[str, object] = {
        "claim": 6,
        "verdict": "BLOCKED",
        "paper_counts": PAPER_COUNTS,
        "paper_arithmetic": {
            "invalid_dimensions": PAPER_COUNTS["total"] - PAPER_COUNTS["valid"],
            "failed_valid_dimensions": (
                PAPER_COUNTS["valid"] - PAPER_COUNTS["successful"]
            ),
            "valid_success_fraction": (
                PAPER_COUNTS["successful"] / PAPER_COUNTS["valid"]
            ),
        },
        "current_official_openml_snapshot": current,
        "current_snapshot_url": (
            "https://www.openml.org/api/v1/json/data/list/"
            "number_classes/2/limit/100000"
        ),
        "current_snapshot_retrieved_utc": "2026-07-23T05:47:39Z",
        "catalog_sha256": catalog_hash,
        "metadata_csv_sha256": metadata_hash,
        "catalog_hash_matches_frozen_contract": catalog_hash == CATALOG_SHA256,
        "metadata_hash_matches_frozen_contract": metadata_hash
        == METADATA_CSV_SHA256,
        "paper_v1_day_cutoff_checks_on_currently_active_catalog": cutoffs,
        "closest_upload_order_prefixes": closest,
        "exact_historical_manifest_present": False,
        "full_feature_values_present": False,
        "kappa_recomputed_for_historical_dimensions": False,
        "missing_protocol_fields": missing_protocol,
        "threshold_mutation_control": mutation,
        "interpretation": (
            "The paper's arithmetic is source-confirmed, but its historical "
            "OpenML census is not identified by the released materials. The "
            "current official catalog is a drift diagnostic, not a substitute "
            "dataset and not a falsification of the historical aggregate."
        ),
        "blocking_condition": (
            "No released dataset manifest or snapshot and no feature-value "
            "census implementation; therefore neither VERIFIED nor FALSIFIED "
            "is supportable for the exact 930738/930751 statement."
        ),
    }
    write_json(artifact_dir / "summary.json", summary)
    write_json(output_dir / "claim6_summary.json", summary)

    independent = subprocess.run(
        [
            sys.executable,
            "reproduction/independent_check_claim_6.py",
            str(catalog_path),
            str(metadata_path),
            str(artifact_dir / "summary.json"),
            str(artifact_dir / "independent_checker.json"),
        ],
        text=True,
        capture_output=True,
    )
    if independent.returncode != 0:
        raise RuntimeError(independent.stdout + "\n" + independent.stderr)

    verifier = subprocess.run(
        [
            sys.executable,
            "reproduction/verify_claim_6.py",
            str(artifact_dir / "summary.json"),
        ],
        text=True,
        capture_output=True,
    )
    verifier_result = {
        "expected_exit_code": "nonzero",
        "actual_exit_code": verifier.returncode,
        "failed_as_intended": verifier.returncode != 0,
        "stdout": verifier.stdout.strip(),
        "stderr": verifier.stderr.strip(),
        "reason": (
            "The positive Claim 6 verifier must reject BLOCKED evidence and "
            "cannot be satisfied by source arithmetic or a current-catalog proxy."
        ),
    }
    write_json(artifact_dir / "verifier_expected_failure.json", verifier_result)
    if verifier.returncode == 0:
        raise RuntimeError("Claim 6 positive verifier accepted blocked evidence")

    runtime = time.perf_counter() - started
    git_sha = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], text=True
    ).strip()
    runtime_record = {
        "command": (
            "python reproduction/reproduce.py --output outputs && "
            "python -m pytest -q reproduction/test_reproduction.py"
        ),
        "git_sha": git_sha,
        "python": platform.python_version(),
        "platform": platform.platform(),
        "machine": platform.machine(),
        "logical_cpu_count": os.cpu_count(),
        "runtime_seconds_claim_6": runtime,
        "network_during_fixed_run": False,
        "seeds": [],
    }
    write_json(artifact_dir / "runtime_environment.json", runtime_record)
    (artifact_dir / "EVAL.md").write_text(
        "# Claim 6 evaluation\n\n"
        "- Verdict: **BLOCKED**\n"
        f"- Paper arithmetic: {PAPER_COUNTS['successful']:,} successful / "
        f"{PAPER_COUNTS['valid']:,} valid / {PAPER_COUNTS['total']:,} total\n"
        f"- Frozen current catalog: {len(catalog):,} active binary datasets; "
        f"{current['number_of_features_sum']:,} total-feature metadata sum\n"
        f"- Independent checker exit: {independent.returncode}\n"
        f"- Positive verifier exit: {verifier.returncode} (nonzero as required)\n"
        "- Release impact: the all-claims terminal gate is not met.\n"
    )
    print("CLAIM_6_OPENML_AUDIT")
    print(json.dumps(summary, indent=2, sort_keys=True))
    print("CLAIM_6_INDEPENDENT_CHECKER_EXIT=0")
    print(f"CLAIM_6_POSITIVE_VERIFIER_EXIT={verifier.returncode}")
    return summary
