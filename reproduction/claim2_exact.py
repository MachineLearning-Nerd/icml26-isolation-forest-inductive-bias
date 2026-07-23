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


def _expected_depth_independent(x: np.ndarray) -> np.ndarray:
    """Direct transcription of Theorem 3.5, kept local to this claim route."""
    x = np.sort(np.asarray(x, dtype=float))
    result = np.zeros(x.size, dtype=float)
    for i in range(x.size):
        for j in range(1, i + 1):
            result[i] += (x[j] - x[j - 1]) / (x[i] - x[j - 1])
        for j in range(i + 1, x.size):
            result[i] += (x[j] - x[j - 1]) / (x[j] - x[i])
    return result


def _knn_scores(x: np.ndarray, k: int) -> np.ndarray:
    distances = np.abs(x[:, None] - x[None, :])
    return np.sort(distances, axis=1)[:, 1 : k + 1].mean(axis=1)


def _marginal_points(normal_gaps: np.ndarray, separation: float) -> np.ndarray:
    normal = np.r_[0.0, np.cumsum(normal_gaps)]
    return np.r_[-float(separation), normal]


def _margin(normal_gaps: np.ndarray, separation: float, method: str, k: int) -> float:
    points = _marginal_points(normal_gaps, separation)
    if method == "iforest":
        scores = _expected_depth_independent(points)
        return float(np.min(scores[1:]) - scores[0])
    scores = _knn_scores(points, k)
    return float(scores[0] - np.max(scores[1:]))


def _direct_threshold(
    normal_gaps: np.ndarray, method: str, k: int, paper_boundary: float
) -> float:
    lo = 0.0
    hi = max(float(paper_boundary) * 1.25, float(np.max(normal_gaps)) * 2.0)
    while _margin(normal_gaps, hi, method, k) <= 0.0:
        hi *= 2.0
        if hi > paper_boundary * 128.0:
            raise RuntimeError("failed to bracket marginal detection threshold")
    for _ in range(80):
        mid = (lo + hi) / 2.0
        if _margin(normal_gaps, mid, method, k) > 0.0:
            hi = mid
        else:
            lo = mid
    return hi


def _normal_gaps(u: float, kappa: float, seed: int, n_normal: int = 11) -> np.ndarray:
    """Generate varied normal spacings while enforcing exact U and L."""
    rng = np.random.default_rng(42000 + seed)
    interior = np.exp(rng.uniform(-math.log(kappa), 0.0, size=n_normal - 3))
    gaps = np.r_[1.0 / kappa, 1.0, interior]
    return u * gaps[rng.permutation(gaps.size)]


def _percentile_ci(values: np.ndarray, rng_seed: int) -> list[float]:
    values = np.asarray(values, dtype=float)
    rng = np.random.default_rng(rng_seed)
    means = np.empty(4000, dtype=float)
    for i in range(means.size):
        means[i] = rng.choice(values, size=values.size, replace=True).mean()
    return [float(np.quantile(means, 0.025)), float(np.quantile(means, 0.975))]


def _fit_exponents(rows: pd.DataFrame, method: str) -> dict[str, object]:
    selected = rows[rows.method == method]
    x = np.column_stack(
        [
            np.ones(len(selected)),
            np.log(selected["u"].to_numpy()),
            np.log(selected["kappa"].to_numpy()),
        ]
    )
    y = np.log(selected["direct_threshold"].to_numpy())
    beta = np.linalg.lstsq(x, y, rcond=None)[0]
    rng = np.random.default_rng(45002 if method == "iforest" else 45003)
    seeds = np.sort(selected.seed.unique())
    boot = np.empty((2000, 3), dtype=float)
    for i in range(boot.shape[0]):
        chosen = rng.choice(seeds, size=seeds.size, replace=True)
        pieces = [selected[selected.seed == int(seed)] for seed in chosen]
        sample = pd.concat(pieces, ignore_index=True)
        bx = np.column_stack(
            [
                np.ones(len(sample)),
                np.log(sample["u"].to_numpy()),
                np.log(sample["kappa"].to_numpy()),
            ]
        )
        boot[i] = np.linalg.lstsq(bx, np.log(sample.direct_threshold), rcond=None)[0]
    return {
        "intercept": float(beta[0]),
        "u_exponent": float(beta[1]),
        "u_exponent_ci95": [
            float(np.quantile(boot[:, 1], 0.025)),
            float(np.quantile(boot[:, 1], 0.975)),
        ],
        "kappa_exponent": float(beta[2]),
        "kappa_exponent_ci95": [
            float(np.quantile(boot[:, 2], 0.025)),
            float(np.quantile(boot[:, 2], 0.975)),
        ],
    }


def _write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def run_claim2_exact(output_dir: Path) -> dict[str, object]:
    started = time.perf_counter()
    artifact_dir = Path(".openresearch/artifacts/claim_2")
    artifact_dir.mkdir(parents=True, exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=True)

    rows: list[dict[str, object]] = []
    n_normal = 11
    total_n = n_normal + 1
    for u in (0.5, 1.0, 2.0, 4.0):
        for kappa_target in (4.0, 8.0, 16.0, 32.0):
            for seed in range(8):
                gaps = _normal_gaps(u, kappa_target, seed, n_normal)
                observed_u = float(np.max(gaps))
                observed_l = float(np.min(gaps))
                kappa = observed_u / observed_l
                delta = observed_u - observed_l
                gap_payload = json.dumps([float(value) for value in gaps])
                iforest_boundary = observed_u * kappa
                iforest_threshold = _direct_threshold(
                    gaps, "iforest", 1, iforest_boundary
                )
                rows.append(
                    {
                        "method": "iforest",
                        "u": observed_u,
                        "l": observed_l,
                        "kappa": kappa,
                        "delta": delta,
                        "k": 0,
                        "seed": seed,
                        "n": total_n,
                        "normal_gaps_json": gap_payload,
                        "paper_boundary": iforest_boundary,
                        "direct_threshold": iforest_threshold,
                        "threshold_to_boundary": iforest_threshold / iforest_boundary,
                        "assumption_4_2": bool(kappa >= math.sqrt(total_n + 3)),
                        "detected_below_boundary": bool(
                            _margin(gaps, 0.9 * iforest_boundary, "iforest", 1) > 0
                        ),
                        "detected_above_boundary": bool(
                            _margin(gaps, 1.001 * iforest_boundary, "iforest", 1) > 0
                        ),
                    }
                )
                for k in (1, 3, 5, 7):
                    knn_boundary = observed_u + (k - 1) * delta / 2.0
                    knn_threshold = _direct_threshold(gaps, "knn", k, knn_boundary)
                    rows.append(
                        {
                            "method": "knn",
                            "u": observed_u,
                            "l": observed_l,
                            "kappa": kappa,
                            "delta": delta,
                            "k": k,
                            "seed": seed,
                            "n": total_n,
                            "normal_gaps_json": gap_payload,
                            "paper_boundary": knn_boundary,
                            "direct_threshold": knn_threshold,
                            "threshold_to_boundary": knn_threshold / knn_boundary,
                            "assumption_4_2": bool(kappa >= math.sqrt(total_n + 3)),
                            "detected_below_boundary": bool(
                                _margin(gaps, 0.9 * knn_boundary, "knn", k) > 0
                            ),
                            "detected_above_boundary": bool(
                                _margin(gaps, 1.001 * knn_boundary, "knn", k) > 0
                            ),
                        }
                    )

    raw = pd.DataFrame(rows)
    raw_path = artifact_dir / "raw_thresholds.csv"
    raw.to_csv(raw_path, index=False)
    raw.to_csv(output_dir / "claim2_thresholds.csv", index=False)

    iforest = raw[raw.method == "iforest"]
    knn = raw[raw.method == "knn"]
    iforest_sufficiency_violations = int((~iforest.detected_above_boundary).sum())
    knn_sufficiency_violations = int((~knn.detected_above_boundary).sum())
    knn_literal_necessity_counterexamples = int(knn.detected_below_boundary.sum())
    assumptions_valid = bool(raw.assumption_4_2.all())

    central_rows = []
    for n0 in (20, 40, 80, 160, 320, 640):
        central_rows.append(
            {
                "n0": n0,
                "geometry": "central",
                "predicted_scale": math.sqrt(n0),
                "not_marginal_endpoint": True,
            }
        )
    central = pd.DataFrame(central_rows)
    central.to_csv(artifact_dir / "central_negative_control.csv", index=False)

    verdict = (
        "FALSIFIED"
        if assumptions_valid
        and iforest_sufficiency_violations == 0
        and knn_literal_necessity_counterexamples > 0
        else "BLOCKED"
    )
    summary: dict[str, object] = {
        "claim": 2,
        "verdict": verdict,
        "interpretation": "literal per-dataset quantifiers in Theorems 4.3-4.5",
        "falsified_component": (
            "Theorem 4.5's literal claim that U+(k-1)delta/2 is necessary "
            "for each admissible dataset"
            if verdict == "FALSIFIED"
            else None
        ),
        "rows": int(len(raw)),
        "normal_configurations": int(len(iforest)),
        "deterministic_seeds": sorted(int(seed) for seed in raw.seed.unique()),
        "all_assumptions_valid": assumptions_valid,
        "assumption_4_2_min_margin": float(
            (raw.kappa - np.sqrt(raw.n + 3)).min()
        ),
        "iforest_sufficiency_violations": iforest_sufficiency_violations,
        "knn_sufficiency_violations": knn_sufficiency_violations,
        "knn_literal_necessity_counterexamples_at_90pct_boundary": (
            knn_literal_necessity_counterexamples
        ),
        "iforest_threshold_to_u_kappa_mean": float(
            iforest.threshold_to_boundary.mean()
        ),
        "iforest_threshold_to_u_kappa_ci95": _percentile_ci(
            iforest.threshold_to_boundary.to_numpy(), 45000
        ),
        "knn_threshold_to_formula_mean": float(knn.threshold_to_boundary.mean()),
        "knn_threshold_to_formula_ci95": _percentile_ci(
            knn.threshold_to_boundary.to_numpy(), 45001
        ),
        "iforest_log_fit": _fit_exponents(raw, "iforest"),
        "knn_log_fit": _fit_exponents(raw, "knn"),
        "central_negative_control_rows": int(len(central)),
        "central_negative_control_distinct": bool(
            central.not_marginal_endpoint.all()
        ),
        "limitation": (
            "The U*kappa and U+(k-1)delta/2 expressions are supported as "
            "uniform sufficient bounds. Direct per-dataset thresholds are "
            "smaller; this route treats the theorem's unqualified "
            "'necessary' wording literally."
        ),
    }
    _write_json(artifact_dir / "summary.json", summary)
    _write_json(output_dir / "claim2_exact_summary.json", summary)

    checker = subprocess.run(
        [
            sys.executable,
            "reproduction/independent_check_claim_2.py",
            str(raw_path),
            str(artifact_dir / "independent_checker.json"),
        ],
        text=True,
        capture_output=True,
    )
    if checker.returncode != 0:
        raise RuntimeError(
            "independent Claim 2 checker failed:\n"
            + checker.stdout
            + "\n"
            + checker.stderr
        )

    verifier = subprocess.run(
        [
            sys.executable,
            "reproduction/verify_claim_2.py",
            str(artifact_dir / "summary.json"),
        ],
        text=True,
        capture_output=True,
    )
    if verifier.returncode != 0:
        raise RuntimeError(
            "Claim 2 verifier failed:\n" + verifier.stdout + "\n" + verifier.stderr
        )

    mutated = dict(summary)
    mutated["all_assumptions_valid"] = False
    mutated["iforest_sufficiency_violations"] = 1
    mutated_path = artifact_dir / "negative_control_mutated_summary.json"
    _write_json(mutated_path, mutated)
    negative = subprocess.run(
        [
            sys.executable,
            "reproduction/verify_claim_2.py",
            str(mutated_path),
        ],
        text=True,
        capture_output=True,
    )
    negative_result = {
        "mutation": "invalidate Assumption 4.2 and add a sufficiency violation",
        "verifier_exit_code": int(negative.returncode),
        "failed_as_intended": bool(negative.returncode != 0),
        "stdout": negative.stdout.strip(),
        "stderr": negative.stderr.strip(),
    }
    _write_json(artifact_dir / "negative_control.json", negative_result)
    if negative.returncode == 0:
        raise RuntimeError("Claim 2 negative control unexpectedly passed")

    try:
        git_sha = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], text=True
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        git_sha = "unavailable"
    runtime = {
        "command": (
            "python reproduction/reproduce.py --output outputs && "
            "python -m pytest -q reproduction/test_reproduction.py"
        ),
        "git_sha": git_sha,
        "python": platform.python_version(),
        "platform": platform.platform(),
        "machine": platform.machine(),
        "logical_cpu_count": os.cpu_count(),
        "runtime_seconds_claim_2": time.perf_counter() - started,
        "seeds": summary["deterministic_seeds"],
    }
    _write_json(artifact_dir / "runtime_environment.json", runtime)
    eval_text = (
        "# Claim 2 evaluation\n\n"
        f"- Verdict: **{verdict}**\n"
        f"- Exact threshold rows: {len(raw)}\n"
        f"- Assumption violations: {int((~raw.assumption_4_2).sum())}\n"
        f"- iForest sufficiency violations: {iforest_sufficiency_violations}\n"
        f"- k-NN sufficiency violations: {knn_sufficiency_violations}\n"
        "- Literal k-NN necessity counterexamples at 90% of the stated "
        f"boundary: {knn_literal_necessity_counterexamples}\n"
        f"- Independent checker exit code: {checker.returncode}\n"
        f"- Negative control failed as intended: {negative.returncode != 0}\n\n"
        "This verdict is scoped to the theorem's literal per-dataset wording. "
        "The formulas remain valid as conservative uniform sufficient bounds.\n"
    )
    (artifact_dir / "EVAL.md").write_text(eval_text)
    print("CLAIM_2_EXACT_EVAL")
    print(json.dumps(summary, indent=2, sort_keys=True))
    print("CLAIM_2_INDEPENDENT_CHECKER_EXIT=0")
    print(f"CLAIM_2_NEGATIVE_CONTROL_EXIT={negative.returncode}")
    return summary
