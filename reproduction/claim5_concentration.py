from __future__ import annotations

import json
import math
import os
import platform
import subprocess
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd

TREE_COUNTS = (100, 300, 1000, 3000, 10000, 30000)
DISTRIBUTIONS = ("normal", "uniform", "exponential")
FOREST_SEEDS = tuple(range(6))
POINTS = 100
ALPHA = 0.05


def theoretical_depths(values: np.ndarray) -> np.ndarray:
    values = np.sort(np.asarray(values, dtype=float))
    gaps = np.diff(values)
    result = np.zeros(len(values), dtype=float)
    for index, value in enumerate(values):
        if index:
            result[index] += np.sum(
                gaps[:index] / (value - values[:index])
            )
        if index < len(values) - 1:
            result[index] += np.sum(
                gaps[index:] / (values[index + 1 :] - value)
            )
    return result


def random_tree_depths(values: np.ndarray, rng: np.random.Generator) -> np.ndarray:
    values = np.sort(np.asarray(values, dtype=float))
    depths = np.zeros(len(values), dtype=np.int16)
    stack = [(0, len(values) - 1, 0)]
    while stack:
        low, high, depth = stack.pop()
        if low == high:
            depths[low] = depth
            continue
        threshold = rng.uniform(values[low], values[high])
        split = int(np.searchsorted(values, threshold, side="right") - 1)
        split = min(max(split, low), high - 1)
        stack.append((low, split, depth + 1))
        stack.append((split + 1, high, depth + 1))
    return depths


def dataset(distribution: str) -> np.ndarray:
    seed = 55100 + DISTRIBUTIONS.index(distribution)
    rng = np.random.default_rng(seed)
    if distribution == "normal":
        values = rng.normal(size=POINTS)
    elif distribution == "uniform":
        values = rng.uniform(size=POINTS)
    elif distribution == "exponential":
        values = rng.exponential(size=POINTS)
    else:
        raise ValueError(distribution)
    return np.sort(values)


def run_ensemble(task: tuple[str, int]) -> tuple[list[dict], list[dict], list[dict]]:
    distribution, forest_seed = task
    values = dataset(distribution)
    theory = theoretical_depths(values)
    rng = np.random.default_rng(56000 + 100 * forest_seed + DISTRIBUTIONS.index(distribution))
    cumulative = np.zeros(POINTS, dtype=float)
    first_tree = None
    aggregate_rows: list[dict] = []
    point_rows: list[dict] = []
    negative_rows: list[dict] = []
    checkpoint_set = set(TREE_COUNTS)
    for tree_index in range(1, TREE_COUNTS[-1] + 1):
        depths = random_tree_depths(values, rng).astype(float)
        if first_tree is None:
            first_tree = depths.copy()
        cumulative += depths
        if tree_index not in checkpoint_set:
            continue
        empirical = cumulative / tree_index
        squared_error = (empirical - theory) ** 2
        epsilon = POINTS * math.sqrt(
            math.log(2.0 / ALPHA) / (2.0 * tree_index)
        )
        aggregate_rows.append(
            {
                "distribution": distribution,
                "forest_seed": forest_seed,
                "trees": tree_index,
                "mse": float(squared_error.mean()),
                "mae": float(np.abs(empirical - theory).mean()),
                "max_abs_error": float(np.abs(empirical - theory).max()),
                "hoeffding_epsilon_alpha_0_05": epsilon,
                "hoeffding_violations": int(
                    (np.abs(empirical - theory) >= epsilon).sum()
                ),
            }
        )
        negative_mse = float(np.mean((first_tree - theory) ** 2))
        negative_rows.append(
            {
                "distribution": distribution,
                "forest_seed": forest_seed,
                "trees": tree_index,
                "mse": negative_mse,
                "control": "repeat one perfectly correlated tree",
            }
        )
        for point_index in range(POINTS):
            point_rows.append(
                {
                    "distribution": distribution,
                    "forest_seed": forest_seed,
                    "trees": tree_index,
                    "point_index": point_index,
                    "value": float(values[point_index]),
                    "theory": float(theory[point_index]),
                    "empirical": float(empirical[point_index]),
                    "squared_error": float(squared_error[point_index]),
                    "hoeffding_epsilon_alpha_0_05": epsilon,
                }
            )
    return aggregate_rows, point_rows, negative_rows


def slope_fit(rows: pd.DataFrame, seed: int) -> dict[str, object]:
    x = np.log(rows.trees.to_numpy(dtype=float))
    y = np.log(rows.mse.to_numpy(dtype=float))
    design = np.column_stack([np.ones(len(rows)), x])
    beta = np.linalg.lstsq(design, y, rcond=None)[0]
    prediction = design @ beta
    residual = y - prediction
    r2 = 1.0 - float(
        np.sum(residual**2) / np.sum((y - y.mean()) ** 2)
    )
    ensembles = rows[["distribution", "forest_seed"]].drop_duplicates()
    rng = np.random.default_rng(seed)
    bootstrap = np.empty(4000, dtype=float)
    for index in range(len(bootstrap)):
        chosen = rng.choice(len(ensembles), size=len(ensembles), replace=True)
        pieces = []
        for chosen_index in chosen:
            item = ensembles.iloc[int(chosen_index)]
            pieces.append(
                rows[
                    (rows.distribution == item.distribution)
                    & (rows.forest_seed == item.forest_seed)
                ]
            )
        sample = pd.concat(pieces, ignore_index=True)
        bx = np.log(sample.trees.to_numpy(dtype=float))
        by = np.log(sample.mse.to_numpy(dtype=float))
        bootstrap[index] = np.polyfit(bx, by, 1)[0]
    return {
        "slope": float(beta[1]),
        "slope_ci95": [
            float(np.quantile(bootstrap, 0.025)),
            float(np.quantile(bootstrap, 0.975)),
        ],
        "intercept": float(beta[0]),
        "log_r2": r2,
        "residual_mean": float(residual.mean()),
        "residual_std": float(residual.std(ddof=1)),
        "residual_max_abs": float(np.abs(residual).max()),
    }


def mean_curve(rows: pd.DataFrame) -> list[dict[str, float]]:
    result = []
    rng = np.random.default_rng(57005)
    for trees, group in rows.groupby("trees", sort=True):
        values = group.mse.to_numpy(dtype=float)
        means = np.empty(4000, dtype=float)
        for index in range(len(means)):
            means[index] = rng.choice(
                values, size=len(values), replace=True
            ).mean()
        result.append(
            {
                "trees": int(trees),
                "mean_mse": float(values.mean()),
                "ci95_low": float(np.quantile(means, 0.025)),
                "ci95_high": float(np.quantile(means, 0.975)),
            }
        )
    return result


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")


def run_claim5_concentration(output_dir: Path) -> dict[str, object]:
    started = time.perf_counter()
    artifact_dir = Path(".openresearch/artifacts/claim_5")
    artifact_dir.mkdir(parents=True, exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=True)
    tasks = [
        (distribution, seed)
        for distribution in DISTRIBUTIONS
        for seed in FOREST_SEEDS
    ]
    worker_count = min(6, len(tasks), os.cpu_count() or 1)
    with ProcessPoolExecutor(max_workers=worker_count) as executor:
        results = list(executor.map(run_ensemble, tasks))
    aggregates = pd.DataFrame(
        [row for result in results for row in result[0]]
    )
    points = pd.DataFrame([row for result in results for row in result[1]])
    negative = pd.DataFrame([row for result in results for row in result[2]])
    aggregates.to_csv(artifact_dir / "aggregate_mse.csv", index=False)
    points.to_csv(artifact_dir / "point_depths.csv", index=False)
    negative.to_csv(
        artifact_dir / "nonconcentrating_negative_control.csv", index=False
    )
    aggregates.to_csv(output_dir / "claim5_aggregate_mse.csv", index=False)
    fit = slope_fit(aggregates, 57001)
    negative_fit = slope_fit(negative, 57002)
    curve = mean_curve(aggregates)
    mean_values = np.array([row["mean_mse"] for row in curve])
    slope_ci = fit["slope_ci95"]
    rate_matches = bool(
        slope_ci[0] < -1.0 < slope_ci[1]
        and -1.15 < fit["slope"] < -0.85
        and fit["log_r2"] > 0.9
    )
    monotonic = bool(np.all(np.diff(mean_values) < 0.0))
    reduction = float(mean_values[0] / mean_values[-1])
    bound_violations = int(aggregates.hoeffding_violations.sum())
    negative_flat = bool(
        abs(negative_fit["slope"]) < 1e-10
        and negative.groupby(["distribution", "forest_seed"]).mse.nunique().eq(1).all()
    )
    verdict = (
        "VERIFIED"
        if rate_matches
        and monotonic
        and reduction > 100.0
        and bound_violations == 0
        and negative_flat
        else "BLOCKED"
    )
    summary = {
        "claim": 5,
        "verdict": verdict,
        "tree_counts": list(TREE_COUNTS),
        "distributions": list(DISTRIBUTIONS),
        "forest_seeds": list(FOREST_SEEDS),
        "ensembles": len(tasks),
        "aggregate_rows": int(len(aggregates)),
        "point_rows": int(len(points)),
        "total_trees_generated": int(len(tasks) * TREE_COUNTS[-1]),
        "fit": fit,
        "mean_mse_curve": curve,
        "mean_mse_strictly_decreasing": monotonic,
        "mse_reduction_100_to_30000": reduction,
        "hoeffding_alpha": ALPHA,
        "hoeffding_bound_violations": bound_violations,
        "negative_control_fit": negative_fit,
        "negative_control_is_flat": negative_flat,
        "proposition_3_1_scope": (
            "Proposition 3.1 states a pointwise Hoeffding tail bound, not an "
            "MSE equality. The fitted T^-1 MSE rate is the corresponding "
            "independent Monte Carlo variance rate and is labeled derived."
        ),
    }
    write_json(artifact_dir / "summary.json", summary)
    write_json(output_dir / "claim5_summary.json", summary)
    independent = subprocess.run(
        [
            sys.executable,
            "reproduction/independent_check_claim_5.py",
            str(artifact_dir / "point_depths.csv"),
            str(artifact_dir / "aggregate_mse.csv"),
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
            "reproduction/verify_claim_5.py",
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
    mutated["verdict"] = "VERIFIED"
    mutated["fit"] = dict(fit)
    mutated["fit"]["slope"] = negative_fit["slope"]
    mutated["fit"]["slope_ci95"] = [-0.01, 0.01]
    mutated["mean_mse_strictly_decreasing"] = False
    mutation_path = artifact_dir / "negative_control_mutated_summary.json"
    write_json(mutation_path, mutated)
    negative_verifier = subprocess.run(
        [
            sys.executable,
            "reproduction/verify_claim_5.py",
            str(mutation_path),
        ],
        text=True,
        capture_output=True,
    )
    write_json(
        artifact_dir / "negative_control_verifier.json",
        {
            "mutation": "substitute perfectly correlated repeated-tree curve",
            "verifier_exit_code": negative_verifier.returncode,
            "failed_as_intended": bool(negative_verifier.returncode != 0),
            "stderr": negative_verifier.stderr.strip(),
        },
    )
    if negative_verifier.returncode == 0:
        raise RuntimeError("Claim 5 nonconcentrating control passed")
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
            "worker_processes": worker_count,
            "runtime_seconds_claim_5": runtime,
        },
    )
    (artifact_dir / "EVAL.md").write_text(
        "# Claim 5 evaluation\n\n"
        f"- Verdict: **{verdict}**\n"
        f"- Ensembles: {len(tasks)}; trees: {len(tasks) * TREE_COUNTS[-1]}\n"
        f"- MSE slope: {fit['slope']} (95% CI {fit['slope_ci95']})\n"
        f"- MSE reduction: {reduction}\n"
        f"- Hoeffding violations: {bound_violations}\n"
        f"- Independent checker exit: {independent.returncode}\n"
        f"- Negative-control verifier exit: {negative_verifier.returncode}\n"
    )
    print("CLAIM_5_CONCENTRATION_EVAL")
    print(json.dumps(summary, indent=2, sort_keys=True))
    print("CLAIM_5_INDEPENDENT_CHECKER_EXIT=0")
    print(f"CLAIM_5_NEGATIVE_CONTROL_EXIT={negative_verifier.returncode}")
    return summary
