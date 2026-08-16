#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parent
EXPECTED_REPOSITORY = "MachineLearning-Nerd/icml26-isolation-forest-inductive-bias"
EXPECTED_IDENTITY = "MachineLearning-Nerd <MachineLearning-Nerd@users.noreply.github.com>"
EXPECTED_PDF_SHA256 = "95df6b6b38e6c65cd16d701175e354736e2fe772496010d57ba26a158f4c1fca"
EXPECTED_BRANCHES = {
    "main",
    "baseline/judged-4-of-12",
    "audit/claim-2-falsification",
    "audit/claim-2-exact-route",
    "experiment/claim-2-randomized-route",
    "audit/claim-4-falsification",
    "experiment/claim-4-asymptotic-route",
    "audit/claim-4-counterexample",
    "experiment/claim-5-concentration",
    "audit/claim-6-openml-protocol",
    "release/cumulative-evidence",
}
EXPECTED_STATUSES = {
    "claim_1": "VERIFIED_SCOPED",
    "claim_2": "FALSIFIED_AS_WRITTEN",
    "claim_3": "VERIFIED_SCOPED",
    "claim_4": "FALSIFIED_AS_WRITTEN",
    "claim_5": "VERIFIED_SCOPED_DERIVED_RATE",
    "claim_6": "BLOCKED_REPRODUCTION_REQUIRED",
}
CURRENT_DOCS = [
    "README.md",
    "STATUS.md",
    "claims.md",
    "CLAIM_EVIDENCE.md",
    "SOURCE_AUDIT.md",
    "SOURCE_MANIFEST.md",
    "ENVIRONMENT.md",
    "CITATION.cff",
]


def run(*args: str) -> str:
    return subprocess.check_output(args, cwd=ROOT, text=True).strip()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_json(relative: str) -> dict:
    return json.loads((ROOT / relative).read_text())


def ref_branch_names() -> set[str]:
    refs = run(
        "git",
        "for-each-ref",
        "--format=%(refname:short)",
        "refs/heads",
        "refs/remotes/origin",
    ).splitlines()
    names = set()
    for ref in refs:
        if ref in {"origin", "origin/HEAD", "HEAD"}:
            continue
        if ref.startswith("origin/"):
            names.add(ref.removeprefix("origin/"))
        else:
            names.add(ref)
    return names


def check_evidence_manifest(manifest: dict) -> None:
    assert manifest["repository"]["name"] == EXPECTED_REPOSITORY
    assert manifest["repository"]["default_branch"] == "main"
    assert manifest["repository"]["attribution"] == EXPECTED_IDENTITY
    assert manifest["collection_status"] == (
        "VERIFIED_SCOPED_WITH_FALSIFIED_AND_BLOCKED_CLAIMS"
    )
    assert set(manifest["claims"]) == set(EXPECTED_STATUSES)
    for claim, expected in EXPECTED_STATUSES.items():
        record = manifest["claims"][claim]
        assert record["status"] == expected
        for relative in record["evidence"]:
            assert (ROOT / relative).is_file(), relative
    assert manifest["release_gate"]["met"] is False
    assert manifest["release_gate"]["publication_authorized"] is False


def check_artifacts() -> None:
    summary = load_json("outputs/summary.json")
    assert summary["claim_1"] == "verified"
    assert summary["claim_3"] == "verified"
    assert abs(summary["depth_correlation"] - 0.9998673437962312) < 1e-12
    assert summary["trees_total"] == 180000

    claim_2 = load_json(".openresearch/artifacts/claim_2/summary.json")
    claim_2_check = load_json(
        ".openresearch/artifacts/claim_2/independent_checker.json"
    )
    assert claim_2["verdict"] == "FALSIFIED"
    assert claim_2["knn_literal_necessity_counterexamples_at_90pct_boundary"] == 480
    assert claim_2_check["passed"] is True
    assert claim_2_check["mismatches"] == 0

    claim_2_randomized = load_json(
        ".openresearch/artifacts/claim_2_route_b/summary.json"
    )
    claim_2_randomized_check = load_json(
        ".openresearch/artifacts/claim_2_route_b/independent_checker.json"
    )
    assert claim_2_randomized["verdict"] == "FALSIFIED"
    assert claim_2_randomized["knn_literal_necessity_counterexamples_at_90pct_boundary"] == 144
    assert claim_2_randomized_check["passed"] is True

    claim_4 = load_json(".openresearch/artifacts/claim_4_route_b/summary.json")
    claim_4_check = load_json(
        ".openresearch/artifacts/claim_4_route_b/independent_checker.json"
    )
    assert claim_4["verdict"] == "FALSIFIED"
    assert claim_4["all_finite_large_separations_fail_detection"] is True
    assert claim_4["all_infinite_separation_limits_fail_detection"] is True
    assert claim_4_check["passed"] is True
    assert claim_4_check["mismatches"] == 0

    claim_4_route_a = load_json(
        ".openresearch/artifacts/claim_4_route_a/summary.json"
    )
    assert claim_4_route_a["verdict"] == "BLOCKED"

    claim_5 = load_json(".openresearch/artifacts/claim_5/summary.json")
    claim_5_check = load_json(
        ".openresearch/artifacts/claim_5/independent_checker.json"
    )
    assert claim_5["verdict"] == "VERIFIED"
    assert claim_5["total_trees_generated"] == 540000
    assert claim_5_check["passed"] is True

    claim_6 = load_json(".openresearch/artifacts/claim_6/summary.json")
    claim_6_check = load_json(
        ".openresearch/artifacts/claim_6/independent_checker.json"
    )
    assert claim_6["verdict"] == "BLOCKED"
    assert claim_6["exact_historical_manifest_present"] is False
    assert claim_6["full_feature_values_present"] is False
    assert claim_6["kappa_recomputed_for_historical_dimensions"] is False
    assert claim_6_check["passed"] is True


def check_release_verifier() -> None:
    result = subprocess.run(
        ["python3", "reproduction/verify_release_candidate.py"],
        cwd=ROOT,
        text=True,
        capture_output=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def main() -> None:
    assert not run("git", "status", "--porcelain")
    assert sha256(ROOT / "paper.pdf") == EXPECTED_PDF_SHA256

    remote = run("git", "remote", "get-url", "origin").removesuffix(".git")
    assert remote == "https://github.com/" + EXPECTED_REPOSITORY

    assert ref_branch_names() == EXPECTED_BRANCHES
    assert run("git", "symbolic-ref", "--short", "HEAD") == "main"

    identities = set(
        run("git", "log", "--all", "--format=%an <%ae>|%cn <%ce>").splitlines()
    )
    expected_identity_pair = {EXPECTED_IDENTITY + "|" + EXPECTED_IDENTITY}
    assert identities == expected_identity_pair, identities
    assert "Co-authored-by:" not in run("git", "log", "--all", "--format=%B")

    manifest = load_json("EVIDENCE_MANIFEST.json")
    check_evidence_manifest(manifest)
    check_artifacts()
    check_release_verifier()

    for relative in CURRENT_DOCS:
        text = (ROOT / relative).read_text()
        assert "icml26-repro-J0y3sNbo9G-isolation-forest" not in text
        assert "orx/" not in text
    assert "Thank you" in (ROOT / "README.md").read_text()
    assert "CITATION.cff" in (ROOT / "README.md").read_text()
    branch_audit = (ROOT / "BRANCH_AUDIT.md").read_text()
    assert "orx/" in branch_audit
    for branch in EXPECTED_BRANCHES:
        assert branch in branch_audit

    print(
        json.dumps(
            {
                "status": "PASS",
                "repository": EXPECTED_REPOSITORY,
                "branches": sorted(EXPECTED_BRANCHES),
                "canonical_identity": EXPECTED_IDENTITY,
                "paper_sha256": EXPECTED_PDF_SHA256,
                "claim_statuses": EXPECTED_STATUSES,
                "release_verifier": "PASS",
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
