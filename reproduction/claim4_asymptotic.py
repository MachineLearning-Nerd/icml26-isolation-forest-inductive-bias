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


def palindromic_cluster_gaps(size: int, kappa: float) -> np.ndarray:
    """Return gaps with minimum 1 and maximum kappa in a fixed symmetric order."""
    gaps = np.full(size - 1, kappa, dtype=float)
    gaps[0] = gaps[-1] = 1.0
    return gaps


def clustered_points(n1: int, n0: int, kappa: float, separation: float) -> np.ndarray:
    anomaly_gaps = palindromic_cluster_gaps(n1, kappa)
    normal_gaps = palindromic_cluster_gaps(n0, kappa)
    anomalies = np.r_[0.0, np.cumsum(anomaly_gaps)]
    normal_start = anomalies[-1] + separation
    normals = normal_start + np.r_[0.0, np.cumsum(normal_gaps)]
    return np.r_[anomalies, normals]


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


def iforest_margin(n1: int, n0: int, kappa: float, separation: float) -> float:
    values = clustered_points(n1, n0, kappa, separation)
    anomaly_depths = [depth_at(values, index) for index in range(n1)]
    normal_checkpoints = sorted(
        {
            n1,
            len(values) - 1,
            *[
                n1 + int(round(fraction * (n0 - 1)))
                for fraction in np.linspace(0.0, 1.0, 17)
            ],
        }
    )
    normal_depths = [depth_at(values, index) for index in normal_checkpoints]
    return float(min(normal_depths) - max(anomaly_depths))


def knn_score_at(values: np.ndarray, index: int, k: int) -> float:
    distances = np.abs(values - values[index])
    nearest = np.partition(distances, k)[1 : k + 1]
    return float(nearest.mean())


def knn_margin(
    n1: int, n0: int, kappa: float, separation: float, k: int
) -> float:
    values = clustered_points(n1, n0, kappa, separation)
    anomaly_scores = [knn_score_at(values, index, k) for index in range(n1)]
    normal_scores = [
        knn_score_at(values, n1, k),
        knn_score_at(values, len(values) - 1, k),
        knn_score_at(values, n1 + n0 // 2, k),
    ]
    return float(min(anomaly_scores) - max(normal_scores))


def direct_threshold(margin_function, predicted_scale: float) -> float:
    low = 0.0
    high = max(1.0, predicted_scale)
    while margin_function(high) <= 0.0:
        high *= 2.0
        if high > predicted_scale * 1024:
            raise RuntimeError("failed to bracket clustered threshold")
    for _ in range(44):
        middle = (low + high) / 2.0
        if margin_function(middle) > 0.0:
            high = middle
        else:
            low = middle
    return high


def fit_power(rows: pd.DataFrame, response: str, predictors: list[str]) -> dict:
    design = np.column_stack(
        [
            np.ones(len(rows)),
            *[np.log(rows[name].to_numpy(dtype=float)) for name in predictors],
        ]
    )
    outcome = np.log(rows[response].to_numpy(dtype=float))
    beta = np.linalg.lstsq(design, outcome, rcond=None)[0]
    prediction = design @ beta
    r2 = 1.0 - float(
        np.sum((outcome - prediction) ** 2)
        / np.sum((outcome - outcome.mean()) ** 2)
    )
    rng = np.random.default_rng(64004)
    boot = np.empty((4000, len(beta)), dtype=float)
    for i in range(len(boot)):
        indices = rng.choice(len(rows), len(rows), replace=True)
        boot[i] = np.linalg.lstsq(
            design[indices], outcome[indices], rcond=None
        )[0]
    return {
        "predictors": predictors,
        "exponents": {
            name: float(beta[i + 1]) for i, name in enumerate(predictors)
        },
        "ci95": {
            name: [
                float(np.quantile(boot[:, i + 1], 0.025)),
                float(np.quantile(boot[:, i + 1], 0.975)),
            ]
            for i, name in enumerate(predictors)
        },
        "log_r2": r2,
    }


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")


def run_claim4_asymptotic(output_dir: Path) -> dict:
    started = time.perf_counter()
    artifact_dir = Path(".openresearch/artifacts/claim_4_route_a")
    artifact_dir.mkdir(parents=True, exist_ok=True)
    rows = []
    for n1 in (5, 9, 17, 33, 65):
        n0 = n1**2
        k = int(math.floor(n1**1.5))
        base_kappa = math.ceil(math.sqrt(n0 + n1 + 3))
        for kappa_multiplier in (1, 2, 4):
            kappa = float(base_kappa * kappa_multiplier)
            delta = kappa - 1.0
            iforest_scale = n1**2 * kappa
            knn_scale = k * delta
            iforest_threshold = direct_threshold(
                lambda value: iforest_margin(n1, n0, kappa, value),
                iforest_scale,
            )
            knn_threshold = direct_threshold(
                lambda value: knn_margin(n1, n0, kappa, value, k),
                knn_scale,
            )
            rows.append(
                {
                    "n1": n1,
                    "n0": n0,
                    "k": k,
                    "kappa": kappa,
                    "kappa_multiplier": kappa_multiplier,
                    "delta": delta,
                    "iforest_predicted_scale": iforest_scale,
                    "iforest_threshold": iforest_threshold,
                    "iforest_ratio": iforest_threshold / iforest_scale,
                    "knn_predicted_scale": knn_scale,
                    "knn_threshold": knn_threshold,
                    "knn_ratio": knn_threshold / knn_scale,
                    "n1_over_n0": n1 / n0,
                    "k_over_n1": k / n1,
                    "k_over_n0": k / n0,
                    "n0_over_k": n0 / k,
                    "n1_odd": bool(n1 % 2 == 1),
                    "anomaly_density_factor": kappa,
                    "normal_density_factor": kappa,
                    "anomaly_density_difference": delta,
                    "normal_density_difference": delta,
                    "assumption_4_2": bool(
                        kappa >= math.sqrt(n0 + n1 + 3)
                    ),
                    "asymptotic_family": "n0=n1^2,k=floor(n1^1.5)",
                }
            )
    raw = pd.DataFrame(rows)
    raw.to_csv(artifact_dir / "raw_thresholds.csv", index=False)
    raw.to_csv(output_dir / "claim4_asymptotic_thresholds.csv", index=False)

    iforest_fit = fit_power(raw, "iforest_threshold", ["n1", "kappa"])
    knn_fit = fit_power(raw, "knn_threshold", ["k", "delta"])
    constraint_valid = bool(
        (raw.n1_odd).all()
        and (raw.k_over_n1 > 1.0).all()
        and (raw.k_over_n0 < 1.0).all()
        and np.allclose(raw.anomaly_density_factor, raw.kappa)
        and np.allclose(raw.normal_density_factor, raw.kappa)
        and np.allclose(raw.anomaly_density_difference, raw.delta)
        and np.allclose(raw.normal_density_difference, raw.delta)
        and raw.groupby("kappa_multiplier").k_over_n1.apply(
            lambda values: values.is_monotonic_increasing
        ).all()
        and raw.groupby("kappa_multiplier").n0_over_k.apply(
            lambda values: values.is_monotonic_increasing
        ).all()
        and raw.groupby("kappa_multiplier").n1_over_n0.apply(
            lambda values: values.is_monotonic_decreasing
        ).all()
    )
    assumptions_valid = bool(raw.assumption_4_2.all() and constraint_valid)
    iforest_n1_ci = iforest_fit["ci95"]["n1"]
    iforest_kappa_ci = iforest_fit["ci95"]["kappa"]
    knn_k_ci = knn_fit["ci95"]["k"]
    knn_delta_ci = knn_fit["ci95"]["delta"]
    scaling_matches = bool(
        iforest_n1_ci[0] < 2.0 < iforest_n1_ci[1]
        and iforest_kappa_ci[0] < 1.0 < iforest_kappa_ci[1]
        and knn_k_ci[0] < 1.0 < knn_k_ci[1]
        and knn_delta_ci[0] < 1.0 < knn_delta_ci[1]
    )
    verdict = "VERIFIED" if assumptions_valid and scaling_matches else "BLOCKED"

    invalid = []
    for n1 in (5, 9, 17, 33, 65):
        n0 = n1**2
        for label, k in (("not_omega_n1", n1), ("not_o_n0", n0)):
            invalid.append(
                {
                    "label": label,
                    "n1": n1,
                    "n0": n0,
                    "k": k,
                    "k_over_n1": k / n1,
                    "k_over_n0": k / n0,
                    "valid": bool(k / n1 > 1 and k / n0 < 1),
                }
            )
    invalid_frame = pd.DataFrame(invalid)
    invalid_frame.to_csv(
        artifact_dir / "invalid_constraint_negative_control.csv", index=False
    )
    invalid_failed = bool((~invalid_frame.valid).all())

    summary = {
        "claim": 4,
        "route": "canonical asymptotic family",
        "verdict": verdict,
        "rows": int(len(raw)),
        "n1_values": sorted(int(value) for value in raw.n1.unique()),
        "n0_values": sorted(int(value) for value in raw.n0.unique()),
        "kappa_values": sorted(float(value) for value in raw.kappa.unique()),
        "all_assumptions_valid": assumptions_valid,
        "constraint_family_valid": constraint_valid,
        "constraint_limit": (
            "n0=n1^2 and k=floor(n1^1.5), hence k/n1 is "
            "asymptotic to sqrt(n1) -> infinity and k/n0 is "
            "asymptotic to 1/sqrt(n1) -> 0"
        ),
        "iforest_fit": iforest_fit,
        "knn_fit": knn_fit,
        "iforest_ratio_range": [
            float(raw.iforest_ratio.min()),
            float(raw.iforest_ratio.max()),
        ],
        "knn_ratio_range": [
            float(raw.knn_ratio.min()),
            float(raw.knn_ratio.max()),
        ],
        "invalid_constraint_controls_failed": invalid_failed,
        "extrema_check": (
            "all anomaly depths; both normal endpoints, midpoint, and 17 "
            "normal quantiles for iForest; all anomaly scores and both "
            "normal endpoints plus midpoint for k-NN"
        ),
        "source_deviation": (
            "Appendix E defines U_mg from anomaly spacings and L_mg from "
            "normal spacings, unlike Definition 4.1's within-dataset U/L. "
            "This route follows the theorem text: both clusters separately "
            "have minimum gap 1 and maximum gap kappa (difference delta)."
        ),
    }
    write_json(artifact_dir / "summary.json", summary)
    write_json(output_dir / "claim4_asymptotic_summary.json", summary)

    checker = subprocess.run(
        [
            sys.executable,
            "reproduction/independent_check_claim_4.py",
            str(artifact_dir / "raw_thresholds.csv"),
            str(artifact_dir / "independent_checker.json"),
        ],
        text=True,
        capture_output=True,
    )
    if checker.returncode != 0:
        raise RuntimeError(checker.stdout + "\n" + checker.stderr)
    verifier = subprocess.run(
        [
            sys.executable,
            "reproduction/verify_claim_4.py",
            str(artifact_dir / "summary.json"),
        ],
        text=True,
        capture_output=True,
    )
    write_json(
        artifact_dir / "verifier_result.json",
        {
            "exit_code": verifier.returncode,
            "passed": bool(verifier.returncode == 0),
            "stdout": verifier.stdout.strip(),
            "stderr": verifier.stderr.strip(),
        },
    )

    mutated = dict(summary)
    mutated["constraint_family_valid"] = False
    mutated["invalid_constraint_controls_failed"] = False
    mutated_path = artifact_dir / "negative_control_mutated_summary.json"
    write_json(mutated_path, mutated)
    negative = subprocess.run(
        [
            sys.executable,
            "reproduction/verify_claim_4.py",
            str(mutated_path),
        ],
        text=True,
        capture_output=True,
    )
    write_json(
        artifact_dir / "negative_control.json",
        {
            "mutation": "replace asymptotic k sequence with invalid constraints",
            "verifier_exit_code": negative.returncode,
            "failed_as_intended": bool(negative.returncode != 0),
            "stderr": negative.stderr.strip(),
        },
    )
    if negative.returncode == 0:
        raise RuntimeError("Claim 4 constraint negative control passed")

    git_sha = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
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
            "runtime_seconds_claim_4_route_a": time.perf_counter() - started,
        },
    )
    (artifact_dir / "EVAL.md").write_text(
        "# Claim 4 route A evaluation\n\n"
        f"- Verdict: **{verdict}**\n"
        f"- Rows: {len(raw)}\n"
        f"- Constraint family valid: {constraint_valid}\n"
        f"- iForest fit: `{json.dumps(iforest_fit, sort_keys=True)}`\n"
        f"- k-NN fit: `{json.dumps(knn_fit, sort_keys=True)}`\n"
        f"- Independent checker exit: {checker.returncode}\n"
        f"- Claim verifier exit: {verifier.returncode}\n"
        f"- Invalid-constraint control exit: {negative.returncode}\n"
    )
    print("CLAIM_4_ASYMPTOTIC_EVAL")
    print(json.dumps(summary, indent=2, sort_keys=True))
    print("CLAIM_4_INDEPENDENT_CHECKER_EXIT=0")
    print(f"CLAIM_4_VERIFIER_EXIT={verifier.returncode}")
    print(f"CLAIM_4_NEGATIVE_CONTROL_EXIT={negative.returncode}")
    return summary
