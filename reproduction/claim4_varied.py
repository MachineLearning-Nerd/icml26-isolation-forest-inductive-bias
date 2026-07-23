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


def cluster_gaps(size: int, kappa: float, seed: int, stream: int) -> np.ndarray:
    """Seeded spacings with exact minimum 1 and maximum kappa."""
    rng = np.random.default_rng(74000 + 101 * seed + stream)
    gaps = np.exp(rng.uniform(0.0, math.log(kappa), size=size - 1))
    gaps[0] = 1.0
    gaps[1] = kappa
    return gaps[rng.permutation(size - 1)]


def clustered_points(
    n1: int, n0: int, kappa: float, separation: float, seed: int
) -> np.ndarray:
    anomaly_gaps = cluster_gaps(n1, kappa, seed, 1)
    normal_gaps = cluster_gaps(n0, kappa, seed, 2)
    anomalies = np.r_[0.0, np.cumsum(anomaly_gaps)]
    normals = anomalies[-1] + separation + np.r_[0.0, np.cumsum(normal_gaps)]
    return np.r_[anomalies, normals]


def expected_depths(values: np.ndarray) -> np.ndarray:
    """Theorem 3.5 for every point, without an extrema shortcut."""
    gaps = np.diff(values)
    result = np.zeros(len(values), dtype=float)
    for index, value in enumerate(values):
        if index:
            result[index] += np.sum(gaps[:index] / (value - values[:index]))
        if index < len(values) - 1:
            result[index] += np.sum(
                gaps[index:] / (values[index + 1 :] - value)
            )
    return result


def knn_scores_1d(values: np.ndarray, k: int) -> np.ndarray:
    """Exact mean k-nearest distance using the two sorted 1-D directions."""
    count = len(values)
    row = np.arange(count)[:, None]
    offsets = np.arange(1, k + 1)[None, :]
    left_index = np.maximum(row - offsets, 0)
    right_index = np.minimum(row + offsets, count - 1)
    left = values[row] - values[left_index]
    right = values[right_index] - values[row]
    left[row - offsets < 0] = np.inf
    right[row + offsets >= count] = np.inf
    candidates = np.concatenate([left, right], axis=1)
    nearest = np.partition(candidates, k - 1, axis=1)[:, :k]
    return nearest.mean(axis=1)


def detection_margin(
    n1: int,
    n0: int,
    kappa: float,
    separation: float,
    seed: int,
    method: str,
    k: int,
) -> float:
    values = clustered_points(n1, n0, kappa, separation, seed)
    if method == "iforest":
        scores = expected_depths(values)
        return float(np.min(scores[n1:]) - np.max(scores[:n1]))
    scores = knn_scores_1d(values, k)
    return float(np.min(scores[:n1]) - np.max(scores[n1:]))


def direct_threshold(
    n1: int,
    n0: int,
    kappa: float,
    seed: int,
    method: str,
    k: int,
    predicted_scale: float,
) -> float:
    low = np.finfo(float).eps
    high = max(1.0, predicted_scale)
    margin = lambda value: detection_margin(
        n1, n0, kappa, value, seed, method, k
    )
    while margin(high) <= 0.0:
        high *= 2.0
        if high > predicted_scale * 1.0e12:
            raise RuntimeError(
                "failed to bracket varied-cluster threshold: "
                f"method={method}, n1={n1}, n0={n0}, kappa={kappa}, "
                f"seed={seed}, k={k}, high={high}"
            )
    for _ in range(30):
        middle = (low + high) / 2.0
        if margin(middle) > 0.0:
            high = middle
        else:
            low = middle
    return high


def clustered_bootstrap_fit(
    rows: pd.DataFrame, response: str, predictors: list[str], seed: int
) -> dict[str, object]:
    def design(frame: pd.DataFrame) -> np.ndarray:
        return np.column_stack(
            [
                np.ones(len(frame)),
                *[
                    np.log(frame[name].to_numpy(dtype=float))
                    for name in predictors
                ],
            ]
        )

    matrix = design(rows)
    outcome = np.log(rows[response].to_numpy(dtype=float))
    beta = np.linalg.lstsq(matrix, outcome, rcond=None)[0]
    prediction = matrix @ beta
    log_r2 = 1.0 - float(
        np.sum((outcome - prediction) ** 2)
        / np.sum((outcome - outcome.mean()) ** 2)
    )
    seeds = np.sort(rows.seed.unique())
    rng = np.random.default_rng(seed)
    bootstrap = np.empty((2000, len(beta)), dtype=float)
    for index in range(len(bootstrap)):
        chosen = rng.choice(seeds, size=len(seeds), replace=True)
        sample = pd.concat(
            [rows[rows.seed == int(item)] for item in chosen],
            ignore_index=True,
        )
        bootstrap[index] = np.linalg.lstsq(
            design(sample),
            np.log(sample[response].to_numpy(dtype=float)),
            rcond=None,
        )[0]
    return {
        "predictors": predictors,
        "exponents": {
            name: float(beta[index + 1])
            for index, name in enumerate(predictors)
        },
        "ci95": {
            name: [
                float(np.quantile(bootstrap[:, index + 1], 0.025)),
                float(np.quantile(bootstrap[:, index + 1], 0.975)),
            ]
            for index, name in enumerate(predictors)
        },
        "log_r2": log_r2,
    }


def predicted_model(rows: pd.DataFrame, response: str, scale: str) -> dict:
    residual = np.log(rows[response].to_numpy()) - np.log(
        rows[scale].to_numpy()
    )
    prediction = np.log(rows[scale].to_numpy()) + residual.mean()
    outcome = np.log(rows[response].to_numpy())
    return {
        "log_r2": 1.0
        - float(
            np.sum((outcome - prediction) ** 2)
            / np.sum((outcome - outcome.mean()) ** 2)
        ),
        "residual_mean": float(residual.mean()),
        "residual_std": float(residual.std(ddof=1)),
        "ratio_min": float(np.exp(residual).min()),
        "ratio_max": float(np.exp(residual).max()),
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
    for n1 in (5, 9, 17, 33):
        n0 = n1**2
        base_kappa = math.ceil(math.sqrt(n0 + n1 + 3))
        for multiplier in (1, 3):
            kappa = float(base_kappa * multiplier)
            delta = kappa - 1.0
            for seed in range(4):
                iforest_scale = n1**2 * kappa
                threshold = direct_threshold(
                    n1, n0, kappa, seed, "iforest", 1, iforest_scale
                )
                print(
                    "CLAIM_4_ROUTE_B_PROGRESS "
                    f"method=iforest n1={n1} kappa={kappa} seed={seed} "
                    f"threshold={threshold:.9g}",
                    flush=True,
                )
                rows.append(
                    {
                        "method": "iforest",
                        "n1": n1,
                        "n0": n0,
                        "k": 0,
                        "k_family_exponent": 0.0,
                        "kappa": kappa,
                        "kappa_multiplier": multiplier,
                        "delta": delta,
                        "seed": seed,
                        "predicted_scale": iforest_scale,
                        "direct_threshold": threshold,
                        "ratio": threshold / iforest_scale,
                        "assumption_4_2": bool(
                            kappa >= math.sqrt(n0 + n1 + 3)
                        ),
                        "anomaly_gap_min": float(
                            cluster_gaps(n1, kappa, seed, 1).min()
                        ),
                        "anomaly_gap_max": float(
                            cluster_gaps(n1, kappa, seed, 1).max()
                        ),
                        "normal_gap_min": float(
                            cluster_gaps(n0, kappa, seed, 2).min()
                        ),
                        "normal_gap_max": float(
                            cluster_gaps(n0, kappa, seed, 2).max()
                        ),
                        "n1_over_n0": n1 / n0,
                        "k_over_n1": 0.0,
                        "k_over_n0": 0.0,
                    }
                )
                for exponent in (1.4, 1.75):
                    k = int(math.floor(n1**exponent))
                    knn_scale = k * delta
                    threshold = direct_threshold(
                        n1, n0, kappa, seed, "knn", k, knn_scale
                    )
                    print(
                        "CLAIM_4_ROUTE_B_PROGRESS "
                        f"method=knn n1={n1} kappa={kappa} seed={seed} "
                        f"k={k} threshold={threshold:.9g}",
                        flush=True,
                    )
                    rows.append(
                        {
                            "method": "knn",
                            "n1": n1,
                            "n0": n0,
                            "k": k,
                            "k_family_exponent": exponent,
                            "kappa": kappa,
                            "kappa_multiplier": multiplier,
                            "delta": delta,
                            "seed": seed,
                            "predicted_scale": knn_scale,
                            "direct_threshold": threshold,
                            "ratio": threshold / knn_scale,
                            "assumption_4_2": bool(
                                kappa >= math.sqrt(n0 + n1 + 3)
                            ),
                            "anomaly_gap_min": float(
                                cluster_gaps(n1, kappa, seed, 1).min()
                            ),
                            "anomaly_gap_max": float(
                                cluster_gaps(n1, kappa, seed, 1).max()
                            ),
                            "normal_gap_min": float(
                                cluster_gaps(n0, kappa, seed, 2).min()
                            ),
                            "normal_gap_max": float(
                                cluster_gaps(n0, kappa, seed, 2).max()
                            ),
                            "n1_over_n0": n1 / n0,
                            "k_over_n1": k / n1,
                            "k_over_n0": k / n0,
                        }
                    )
    raw = pd.DataFrame(rows)
    raw.to_csv(artifact_dir / "raw_thresholds.csv", index=False)
    raw.to_csv(output_dir / "claim4_varied_thresholds.csv", index=False)
    iforest = raw[raw.method == "iforest"].copy()
    knn = raw[raw.method == "knn"].copy()
    iforest_fit = clustered_bootstrap_fit(
        iforest, "direct_threshold", ["n1", "kappa"], 74100
    )
    knn_fit = clustered_bootstrap_fit(
        knn, "direct_threshold", ["k", "delta", "n1"], 74101
    )
    iforest_predicted = predicted_model(
        iforest, "direct_threshold", "predicted_scale"
    )
    knn_predicted = predicted_model(knn, "direct_threshold", "predicted_scale")
    constraints_valid = bool(
        (knn.k_over_n1 > 1.0).all()
        and (knn.k_over_n0 < 1.0).all()
        and knn.groupby(
            ["seed", "kappa_multiplier", "k_family_exponent"]
        ).k_over_n1.apply(
            lambda values: values.is_monotonic_increasing
        ).all()
        and knn.groupby(
            ["seed", "kappa_multiplier", "k_family_exponent"]
        ).k_over_n0.apply(
            lambda values: values.is_monotonic_decreasing
        ).all()
        and np.allclose(raw.anomaly_gap_min, 1.0)
        and np.allclose(raw.normal_gap_min, 1.0)
        and np.allclose(raw.anomaly_gap_max, raw.kappa)
        and np.allclose(raw.normal_gap_max, raw.kappa)
    )
    i_n1_ci = iforest_fit["ci95"]["n1"]
    i_kappa_ci = iforest_fit["ci95"]["kappa"]
    k_ci = knn_fit["ci95"]["k"]
    delta_ci = knn_fit["ci95"]["delta"]
    exact_exponents_match = bool(
        i_n1_ci[0] < 2.0 < i_n1_ci[1]
        and i_kappa_ci[0] < 1.0 < i_kappa_ci[1]
        and k_ci[0] < 1.0 < k_ci[1]
        and delta_ci[0] < 1.0 < delta_ci[1]
    )
    assumptions_valid = bool(raw.assumption_4_2.all() and constraints_valid)
    verdict = (
        "VERIFIED" if assumptions_valid and exact_exponents_match else "BLOCKED"
    )
    invalid = [
        {"label": "not_omega_n1", "n1": n1, "n0": n1**2, "k": n1}
        for n1 in (5, 9, 17, 33)
    ] + [
        {"label": "not_o_n0", "n1": n1, "n0": n1**2, "k": n1**2}
        for n1 in (5, 9, 17, 33)
    ]
    invalid_frame = pd.DataFrame(invalid)
    invalid_frame["valid"] = (
        (invalid_frame.k / invalid_frame.n1 > 1.0)
        & (invalid_frame.k / invalid_frame.n0 < 1.0)
    )
    invalid_frame.to_csv(
        artifact_dir / "invalid_constraint_negative_control.csv", index=False
    )
    invalid_failed = bool((~invalid_frame.valid).all())
    summary = {
        "claim": 4,
        "route": "seeded varied within-cluster spacings",
        "verdict": verdict,
        "rows": int(len(raw)),
        "iforest_rows": int(len(iforest)),
        "knn_rows": int(len(knn)),
        "seeds": sorted(int(value) for value in raw.seed.unique()),
        "n1_values": sorted(int(value) for value in raw.n1.unique()),
        "k_family_exponents": sorted(
            float(value) for value in knn.k_family_exponent.unique()
        ),
        "all_assumptions_valid": assumptions_valid,
        "constraint_families_valid": constraints_valid,
        "exact_density_metrics": (
            "each seeded cluster has minimum gap 1, maximum gap kappa, "
            "and density difference delta=kappa-1"
        ),
        "iforest_fit": iforest_fit,
        "knn_fit_with_n1_nuisance": knn_fit,
        "iforest_fixed_prediction": iforest_predicted,
        "knn_fixed_prediction": knn_predicted,
        "invalid_constraint_controls_failed": invalid_failed,
        "full_extrema_evaluated": True,
        "limitation": (
            "This finite seeded family is an empirical scaling test, not a "
            "universal proof of the asymptotic theorem. Strict exponent-CI "
            "gates prevent finite trend agreement from becoming VERIFIED."
        ),
    }
    write_json(artifact_dir / "summary.json", summary)
    write_json(output_dir / "claim4_varied_summary.json", summary)
    independent = subprocess.run(
        [
            sys.executable,
            "reproduction/independent_check_claim_4_varied.py",
            str(artifact_dir / "raw_thresholds.csv"),
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
    mutated["all_assumptions_valid"] = False
    mutated["constraint_families_valid"] = False
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
            "mutation": "invalidate omega(n1)<=k<=o(n0) families",
            "verifier_exit_code": negative.returncode,
            "failed_as_intended": bool(negative.returncode != 0),
            "stderr": negative.stderr.strip(),
        },
    )
    if negative.returncode == 0:
        raise RuntimeError("Claim 4 varied negative control passed")
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
        f"- Rows: {len(raw)} over seeds {summary['seeds']}\n"
        f"- iForest fit: `{json.dumps(iforest_fit, sort_keys=True)}`\n"
        f"- k-NN fit: `{json.dumps(knn_fit, sort_keys=True)}`\n"
        f"- Independent checker exit: {independent.returncode}\n"
        f"- Claim verifier exit: {verifier.returncode}\n"
        f"- Negative-control exit: {negative.returncode}\n"
    )
    print("CLAIM_4_VARIED_EVAL")
    print(json.dumps(summary, indent=2, sort_keys=True))
    print("CLAIM_4_VARIED_INDEPENDENT_CHECKER_EXIT=0")
    print(f"CLAIM_4_VARIED_VERIFIER_EXIT={verifier.returncode}")
    print(f"CLAIM_4_VARIED_NEGATIVE_CONTROL_EXIT={negative.returncode}")
    return summary
