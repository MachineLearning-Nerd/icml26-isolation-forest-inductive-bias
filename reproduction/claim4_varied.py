from __future__ import annotations

import json
import math
import os
import platform
import subprocess
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd


def anomaly_gaps(n1: int, kappa: float, seed: int) -> np.ndarray:
    """Exact-kappa anomaly spacings with four deterministic arrangements."""
    gaps = np.ones(n1 - 1, dtype=float)
    positions = (0, (n1 - 2) // 2, (n1 - 1) // 2, n1 - 2)
    gaps[positions[seed]] = kappa
    return gaps


def normal_gaps(n0: int, kappa: float) -> np.ndarray:
    """Isolate the boundary normal while retaining exact density factor kappa."""
    gaps = np.ones(n0 - 1, dtype=float)
    gaps[0] = kappa
    return gaps


def depth_at(values: np.ndarray, index: int) -> float:
    gaps = np.diff(values)
    value = values[index]
    left = (
        float(np.sum(gaps[:index] / (value - values[:index])))
        if index
        else 0.0
    )
    right = (
        float(np.sum(gaps[index:] / (values[index + 1 :] - value)))
        if index < len(values) - 1
        else 0.0
    )
    return left + right


def finite_failure_certificate(
    n1: int, n0: int, kappa: float, seed: int, separation: float
) -> dict[str, float]:
    a_gaps = anomaly_gaps(n1, kappa, seed)
    b_gaps = normal_gaps(n0, kappa)
    anomaly = np.r_[0.0, np.cumsum(a_gaps)]
    normal = anomaly[-1] + separation + np.r_[0.0, np.cumsum(b_gaps)]
    values = np.r_[anomaly, normal]
    anomaly_depths = np.array(
        [depth_at(values, index) for index in range(n1)]
    )
    witness_index = int(np.argmax(anomaly_depths))
    witness_depth = float(anomaly_depths[witness_index])
    boundary_normal_depth = depth_at(values, n1)
    return {
        "anomaly_witness_index": witness_index,
        "anomaly_witness_depth": witness_depth,
        "normal_witness_index": n1,
        "normal_witness_depth": boundary_normal_depth,
        "failure_margin": boundary_normal_depth - witness_depth,
    }


def infinite_failure_certificate(
    n1: int, n0: int, kappa: float, seed: int
) -> dict[str, float]:
    """Exact theta->infinity limit: each detached cluster depth gains one."""
    anomaly = np.r_[0.0, np.cumsum(anomaly_gaps(n1, kappa, seed))]
    normal = np.r_[0.0, np.cumsum(normal_gaps(n0, kappa))]
    anomaly_internal = np.array(
        [depth_at(anomaly, index) for index in range(n1)]
    )
    witness_index = int(np.argmax(anomaly_internal))
    anomaly_limit = float(anomaly_internal[witness_index] + 1.0)
    normal_limit = float(depth_at(normal, 0) + 1.0)
    return {
        "anomaly_witness_index": witness_index,
        "anomaly_limit_depth": anomaly_limit,
        "normal_witness_index": n1,
        "normal_limit_depth": normal_limit,
        "infinite_failure_margin": normal_limit - anomaly_limit,
    }


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")


def run_claim4_varied(output_dir: Path) -> dict[str, object]:
    started = time.perf_counter()
    artifact_dir = Path(".openresearch/artifacts/claim_4_route_b")
    artifact_dir.mkdir(parents=True, exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, object]] = []
    for n1 in (5, 9, 17, 33, 65):
        n0 = n1**2
        kappa = float(100 * n0)
        predicted_scale = n1**2 * kappa
        for seed in range(4):
            limit = infinite_failure_certificate(n1, n0, kappa, seed)
            for separation_multiplier in (1.0, 10.0, 1000.0):
                separation = separation_multiplier * predicted_scale
                finite = finite_failure_certificate(
                    n1, n0, kappa, seed, separation
                )
                rows.append(
                    {
                        "n1": n1,
                        "n0": n0,
                        "kappa": kappa,
                        "delta": kappa - 1.0,
                        "seed": seed,
                        "large_gap_position": int(
                            np.argmax(anomaly_gaps(n1, kappa, seed))
                        ),
                        "separation_multiplier": separation_multiplier,
                        "predicted_scale": predicted_scale,
                        "separation": separation,
                        "anomaly_gap_min": float(
                            anomaly_gaps(n1, kappa, seed).min()
                        ),
                        "anomaly_gap_max": float(
                            anomaly_gaps(n1, kappa, seed).max()
                        ),
                        "normal_gap_min": float(normal_gaps(n0, kappa).min()),
                        "normal_gap_max": float(normal_gaps(n0, kappa).max()),
                        "assumption_4_2": bool(
                            kappa >= math.sqrt(n0 + n1 + 3)
                        ),
                        "n1_over_n0": n1 / n0,
                        **finite,
                        **limit,
                    }
                )
            print(
                "CLAIM_4_COUNTEREXAMPLE_PROGRESS "
                f"n1={n1} n0={n0} kappa={kappa:.9g} seed={seed} "
                f"infinite_margin={limit['infinite_failure_margin']:.9g}",
                flush=True,
            )
    raw = pd.DataFrame(rows)
    raw.to_csv(artifact_dir / "raw_counterexamples.csv", index=False)
    raw.to_csv(output_dir / "claim4_counterexamples.csv", index=False)

    exact_density = bool(
        np.allclose(raw.anomaly_gap_min, 1.0)
        and np.allclose(raw.normal_gap_min, 1.0)
        and np.allclose(raw.anomaly_gap_max, raw.kappa)
        and np.allclose(raw.normal_gap_max, raw.kappa)
    )
    asymptotic_family = bool(
        raw.groupby(["seed", "separation_multiplier"]).n1_over_n0.apply(
            lambda values: values.is_monotonic_decreasing
        ).all()
        and np.allclose(raw.n1_over_n0, 1.0 / raw.n1)
    )
    assumptions_valid = bool(
        raw.assumption_4_2.all() and exact_density and asymptotic_family
    )
    finite_failures = bool((raw.failure_margin < -1e-8).all())
    limit_rows = raw.drop_duplicates(["n1", "seed"])
    infinite_failures = bool(
        (limit_rows.infinite_failure_margin < -1e-8).all()
    )
    strict_margin = float(-limit_rows.infinite_failure_margin.max())
    verdict = (
        "FALSIFIED"
        if assumptions_valid
        and finite_failures
        and infinite_failures
        and strict_margin > 1e-8
        else "BLOCKED"
    )
    summary = {
        "claim": 4,
        "route": "explicit no-threshold counterexample family",
        "verdict": verdict,
        "falsified_component": (
            "Theorem 4.8's universal sufficient-separation statement for "
            "iForest clustered marginal anomalies"
        ),
        "rows": int(len(raw)),
        "counterexample_families": int(len(limit_rows)),
        "n1_values": sorted(int(value) for value in raw.n1.unique()),
        "n0_rule": "n0=n1^2, hence n1/n0=1/n1 -> 0",
        "kappa_rule": "kappa=100*n0",
        "separation_multipliers": sorted(
            float(value) for value in raw.separation_multiplier.unique()
        ),
        "deterministic_seeds": sorted(int(value) for value in raw.seed.unique()),
        "all_assumptions_valid": assumptions_valid,
        "exact_density_metrics": exact_density,
        "asymptotic_family_valid": asymptotic_family,
        "all_finite_large_separations_fail_detection": finite_failures,
        "all_infinite_separation_limits_fail_detection": infinite_failures,
        "least_absolute_infinite_failure_margin": strict_margin,
        "infinite_limit_derivation": (
            "By Theorem 3.5, as the inter-cluster gap theta tends to "
            "infinity, its contribution tends to one and every spacing in "
            "the opposite cluster contributes zero. Each full-data depth "
            "therefore tends to its within-cluster expected depth plus one."
        ),
        "failure_witness": (
            "For every row, one anomaly has depth at least that of the "
            "first normal point. Therefore max anomaly depth is not below "
            "min normal depth, so not all anomalies are detected."
        ),
        "claim_scope": (
            "Falsification of the iForest component is sufficient to "
            "falsify the combined Claim 4. Route A separately retains the "
            "measured k-NN comparison and invalid-k controls."
        ),
    }
    write_json(artifact_dir / "summary.json", summary)
    write_json(output_dir / "claim4_varied_summary.json", summary)

    independent = subprocess.run(
        [
            sys.executable,
            "reproduction/independent_check_claim_4_varied.py",
            str(artifact_dir / "raw_counterexamples.csv"),
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
            "reproduction/verify_claim_4_varied.py",
            str(artifact_dir / "summary.json"),
        ],
        text=True,
        capture_output=True,
    )
    if verifier.returncode != 0:
        raise RuntimeError(verifier.stdout + "\n" + verifier.stderr)
    write_json(
        artifact_dir / "verifier_result.json",
        {
            "exit_code": verifier.returncode,
            "passed": True,
            "stdout": verifier.stdout.strip(),
            "stderr": verifier.stderr.strip(),
        },
    )
    mutated = dict(summary)
    mutated["verdict"] = "FALSIFIED"
    mutated["all_infinite_separation_limits_fail_detection"] = False
    mutation_path = artifact_dir / "negative_control_mutated_summary.json"
    write_json(mutation_path, mutated)
    negative = subprocess.run(
        [
            sys.executable,
            "reproduction/verify_claim_4_varied.py",
            str(mutation_path),
        ],
        text=True,
        capture_output=True,
    )
    write_json(
        artifact_dir / "negative_control.json",
        {
            "mutation": "remove the infinite-separation contradiction",
            "verifier_exit_code": negative.returncode,
            "failed_as_intended": bool(negative.returncode != 0),
            "stderr": negative.stderr.strip(),
        },
    )
    if negative.returncode == 0:
        raise RuntimeError("Claim 4 counterexample negative control passed")
    git_sha = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], text=True
    ).strip()
    runtime = time.perf_counter() - started
    write_json(
        artifact_dir / "runtime_environment.json",
        {
            "command": (
                "python reproduction/reproduce.py --output outputs && "
                "python -m pytest -q reproduction/test_reproduction.py"
            ),
            "git_sha": git_sha,
            "python": platform.python_version(),
            "platform": platform.platform(),
            "machine": platform.machine(),
            "logical_cpu_count": os.cpu_count(),
            "runtime_seconds_claim_4_route_b": runtime,
        },
    )
    (artifact_dir / "EVAL.md").write_text(
        "# Claim 4 route B evaluation\n\n"
        f"- Verdict: **{verdict}**\n"
        f"- Counterexample rows: {len(raw)}\n"
        f"- Asymptotic families: {len(limit_rows)}\n"
        f"- Least absolute limiting contradiction margin: {strict_margin}\n"
        f"- Independent checker exit: {independent.returncode}\n"
        f"- Claim verifier exit: {verifier.returncode}\n"
        f"- Negative-control exit: {negative.returncode}\n"
    )
    print("CLAIM_4_VARIED_EVAL")
    print(json.dumps(summary, indent=2, sort_keys=True))
    print("CLAIM_4_VARIED_INDEPENDENT_CHECKER_EXIT=0")
    print("CLAIM_4_VARIED_VERIFIER_EXIT=0")
    print(f"CLAIM_4_VARIED_NEGATIVE_CONTROL_EXIT={negative.returncode}")
    return summary
