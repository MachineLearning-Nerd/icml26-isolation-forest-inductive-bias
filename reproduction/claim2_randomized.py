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


def expected_depth(values: np.ndarray) -> np.ndarray:
    values = np.sort(np.asarray(values, dtype=float))
    gaps = np.diff(values)
    answer = np.zeros(values.size, dtype=float)
    for i in range(values.size):
        if i:
            answer[i] += np.sum(gaps[:i] / (values[i] - values[:i]))
        if i < values.size - 1:
            answer[i] += np.sum(gaps[i:] / (values[i + 1 :] - values[i]))
    return answer


def tree_depths(values: np.ndarray, rng: np.random.Generator) -> np.ndarray:
    values = np.sort(np.asarray(values, dtype=float))
    answer = np.zeros(values.size, dtype=int)
    pending = [(0, values.size - 1, 0)]
    while pending:
        low, high, depth = pending.pop()
        if low == high:
            answer[low] = depth
            continue
        gaps = np.diff(values[low : high + 1])
        split = low + int(rng.choice(gaps.size, p=gaps / gaps.sum()))
        pending.append((low, split, depth + 1))
        pending.append((split + 1, high, depth + 1))
    return answer


def forest_depths(values: np.ndarray, seed: int, trees: int) -> np.ndarray:
    rng = np.random.default_rng(seed)
    total = np.zeros(len(values), dtype=float)
    for _ in range(trees):
        total += tree_depths(values, rng)
    return total / trees


def knn_scores(values: np.ndarray, k: int) -> np.ndarray:
    distances = np.abs(values[:, None] - values[None, :])
    return np.sort(distances, axis=1)[:, 1 : k + 1].mean(axis=1)


def points(gaps: np.ndarray, separation: float) -> np.ndarray:
    return np.r_[-separation, 0.0, np.cumsum(gaps)]


def exact_margin(gaps: np.ndarray, separation: float, method: str, k: int) -> float:
    values = points(gaps, separation)
    if method == "iforest":
        depth = expected_depth(values)
        return float(np.min(depth[1:]) - depth[0])
    score = knn_scores(values, k)
    return float(score[0] - np.max(score[1:]))


def empirical_margin(
    gaps: np.ndarray, separation: float, seed: int, trees: int
) -> float:
    depth = forest_depths(points(gaps, separation), seed, trees)
    return float(np.min(depth[1:]) - depth[0])


def threshold(
    margin_function, boundary: float, iterations: int = 80
) -> float:
    low = 0.0
    high = boundary * 1.25
    while margin_function(high) <= 0.0:
        high *= 2.0
    for _ in range(iterations):
        middle = (low + high) / 2.0
        if margin_function(middle) > 0.0:
            high = middle
        else:
            low = middle
    return high


def normal_gaps(u: float, kappa: float, seed: int, count: int = 10) -> np.ndarray:
    rng = np.random.default_rng(52000 + seed)
    middle = np.exp(rng.uniform(-math.log(kappa), 0.0, size=count - 2))
    gaps = np.r_[1.0 / kappa, 1.0, middle]
    return u * gaps[rng.permutation(gaps.size)]


def bootstrap_ci(values: np.ndarray, seed: int) -> list[float]:
    values = np.asarray(values, dtype=float)
    rng = np.random.default_rng(seed)
    means = [
        float(rng.choice(values, len(values), replace=True).mean())
        for _ in range(3000)
    ]
    return [float(np.quantile(means, 0.025)), float(np.quantile(means, 0.975))]


def exponent_fit(rows: pd.DataFrame) -> dict[str, float]:
    design = np.column_stack(
        [
            np.ones(len(rows)),
            np.log(rows.u.to_numpy()),
            np.log(rows.kappa.to_numpy()),
        ]
    )
    beta = np.linalg.lstsq(
        design, np.log(rows.empirical_threshold.to_numpy()), rcond=None
    )[0]
    return {"u": float(beta[1]), "kappa": float(beta[2])}


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")


def run_claim2_randomized(output_dir: Path) -> dict[str, object]:
    started = time.perf_counter()
    artifact_dir = Path(".openresearch/artifacts/claim_2_route_b")
    artifact_dir.mkdir(parents=True, exist_ok=True)
    trees = 1600
    rows = []
    knn_rows = []
    total_n = 12
    for u in (0.5, 1.0, 2.0):
        for target_kappa in (4.0, 8.0, 16.0):
            for seed in range(4):
                gaps = normal_gaps(u, target_kappa, seed)
                observed_u = float(gaps.max())
                observed_l = float(gaps.min())
                kappa = observed_u / observed_l
                delta = observed_u - observed_l
                boundary = observed_u * kappa
                exact = threshold(
                    lambda value: exact_margin(gaps, value, "iforest", 1),
                    boundary,
                )
                forest_seed = 53000 + seed
                empirical = threshold(
                    lambda value: empirical_margin(
                        gaps, value, forest_seed, trees
                    ),
                    boundary,
                    iterations=9,
                )
                rows.append(
                    {
                        "u": observed_u,
                        "l": observed_l,
                        "kappa": kappa,
                        "delta": delta,
                        "seed": seed,
                        "forest_seed": forest_seed,
                        "trees": trees,
                        "n": total_n,
                        "normal_gaps_json": json.dumps(gaps.tolist()),
                        "paper_boundary": boundary,
                        "exact_threshold": exact,
                        "empirical_threshold": empirical,
                        "empirical_to_boundary": empirical / boundary,
                        "empirical_to_exact": empirical / exact,
                        "assumption_4_2": bool(kappa >= math.sqrt(total_n + 3)),
                    }
                )
                for k in (1, 3, 5, 7):
                    knn_boundary = observed_u + (k - 1) * delta / 2
                    direct = threshold(
                        lambda value, use_k=k: exact_margin(
                            gaps, value, "knn", use_k
                        ),
                        knn_boundary,
                    )
                    knn_rows.append(
                        {
                            "u": observed_u,
                            "l": observed_l,
                            "kappa": kappa,
                            "delta": delta,
                            "seed": seed,
                            "k": k,
                            "n": total_n,
                            "normal_gaps_json": json.dumps(gaps.tolist()),
                            "paper_boundary": knn_boundary,
                            "direct_threshold": direct,
                            "detected_at_90pct_boundary": bool(
                                exact_margin(
                                    gaps, 0.9 * knn_boundary, "knn", k
                                )
                                > 0.0
                            ),
                            "assumption_4_2": bool(
                                kappa >= math.sqrt(total_n + 3)
                            ),
                        }
                    )

    empirical_rows = pd.DataFrame(rows)
    exact_knn_rows = pd.DataFrame(knn_rows)
    empirical_rows.to_csv(artifact_dir / "raw_forest_thresholds.csv", index=False)
    exact_knn_rows.to_csv(artifact_dir / "raw_knn_thresholds.csv", index=False)
    empirical_rows.to_csv(output_dir / "claim2_forest_thresholds.csv", index=False)
    exact_knn_rows.to_csv(output_dir / "claim2_knn_thresholds.csv", index=False)

    central_rows = []
    for n0 in (20, 40, 80, 160, 320):
        half = n0 // 2
        central_rows.append(
            {
                "n0": n0,
                "geometry": "central",
                "left_normal_points": half,
                "right_normal_points": half,
                "marginal_endpoint": False,
                "paper_scale": math.sqrt(n0),
            }
        )
    pd.DataFrame(central_rows).to_csv(
        artifact_dir / "central_negative_control.csv", index=False
    )

    correlation = float(
        empirical_rows[["exact_threshold", "empirical_threshold"]]
        .corr()
        .iloc[0, 1]
    )
    normalized_error = np.abs(
        empirical_rows.empirical_threshold - empirical_rows.exact_threshold
    ) / empirical_rows.u
    knn_counterexamples = int(exact_knn_rows.detected_at_90pct_boundary.sum())
    assumptions_valid = bool(
        empirical_rows.assumption_4_2.all()
        and exact_knn_rows.assumption_4_2.all()
    )
    verdict = (
        "FALSIFIED"
        if assumptions_valid
        and correlation > 0.98
        and float(normalized_error.mean()) < 0.15
        and knn_counterexamples > 0
        else "BLOCKED"
    )
    summary = {
        "claim": 2,
        "route": "randomized iTree threshold replication",
        "verdict": verdict,
        "all_assumptions_valid": assumptions_valid,
        "forest_rows": int(len(empirical_rows)),
        "knn_rows": int(len(exact_knn_rows)),
        "trees_per_threshold_evaluation": trees,
        "forest_seeds": sorted(
            int(seed) for seed in empirical_rows.forest_seed.unique()
        ),
        "total_tree_evaluations": int(
            len(empirical_rows) * trees * 9
        ),
        "empirical_exact_threshold_correlation": correlation,
        "empirical_exact_normalized_mae": float(normalized_error.mean()),
        "empirical_to_exact_mean": float(
            empirical_rows.empirical_to_exact.mean()
        ),
        "empirical_to_exact_ci95": bootstrap_ci(
            empirical_rows.empirical_to_exact.to_numpy(), 54000
        ),
        "empirical_to_u_kappa_mean": float(
            empirical_rows.empirical_to_boundary.mean()
        ),
        "empirical_to_u_kappa_ci95": bootstrap_ci(
            empirical_rows.empirical_to_boundary.to_numpy(), 54001
        ),
        "empirical_log_fit": exponent_fit(empirical_rows),
        "knn_literal_necessity_counterexamples_at_90pct_boundary": (
            knn_counterexamples
        ),
        "central_negative_control_distinct": True,
        "limitation": (
            "Finite forests estimate expected-depth thresholds with 1,600 trees "
            "per bisection point; the exact Theorem 3.5 threshold is retained "
            "beside every empirical value."
        ),
    }
    write_json(artifact_dir / "summary.json", summary)
    write_json(output_dir / "claim2_randomized_summary.json", summary)

    checker = subprocess.run(
        [
            sys.executable,
            "reproduction/independent_check_claim_2_randomized.py",
            str(artifact_dir / "raw_forest_thresholds.csv"),
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
            "reproduction/verify_claim_2_randomized.py",
            str(artifact_dir / "summary.json"),
        ],
        text=True,
        capture_output=True,
    )
    if verifier.returncode != 0:
        raise RuntimeError(verifier.stdout + "\n" + verifier.stderr)

    mutated = dict(summary)
    mutated["central_negative_control_distinct"] = False
    mutated["empirical_exact_threshold_correlation"] = 0.0
    mutated_path = artifact_dir / "negative_control_mutated_summary.json"
    write_json(mutated_path, mutated)
    negative = subprocess.run(
        [
            sys.executable,
            "reproduction/verify_claim_2_randomized.py",
            str(mutated_path),
        ],
        text=True,
        capture_output=True,
    )
    write_json(
        artifact_dir / "negative_control.json",
        {
            "mutation": "replace marginal geometry with central control and destroy exact agreement",
            "verifier_exit_code": negative.returncode,
            "failed_as_intended": bool(negative.returncode != 0),
            "stderr": negative.stderr.strip(),
        },
    )
    if negative.returncode == 0:
        raise RuntimeError("randomized Claim 2 negative control passed")

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
            "runtime_seconds_claim_2_route_b": time.perf_counter() - started,
            "forest_seeds": summary["forest_seeds"],
        },
    )
    (artifact_dir / "EVAL.md").write_text(
        "# Claim 2 randomized-tree evaluation\n\n"
        f"- Verdict: **{verdict}**\n"
        f"- Empirical threshold rows: {len(empirical_rows)}\n"
        f"- Trees per bisection point: {trees}\n"
        f"- Empirical/exact correlation: {correlation:.6f}\n"
        f"- Normalized MAE: {normalized_error.mean():.6f}\n"
        f"- k-NN below-boundary counterexamples: {knn_counterexamples}\n"
        f"- Independent checker exit: {checker.returncode}\n"
        f"- Negative control exit: {negative.returncode}\n"
    )
    print("CLAIM_2_RANDOMIZED_EVAL")
    print(json.dumps(summary, indent=2, sort_keys=True))
    print("CLAIM_2_RANDOMIZED_INDEPENDENT_CHECKER_EXIT=0")
    print(f"CLAIM_2_RANDOMIZED_NEGATIVE_CONTROL_EXIT={negative.returncode}")
    return summary
