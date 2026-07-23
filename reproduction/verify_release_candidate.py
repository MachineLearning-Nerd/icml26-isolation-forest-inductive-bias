#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path


ROOT = Path(__file__).parents[1]
RELEASE = ROOT / ".openresearch" / "release_candidate"
SPACE = RELEASE / "space"
OLD_MANIFEST = ROOT / ".openresearch" / "artifacts" / "startup" / "judged_space_manifest.tsv"

EXPECTED_UPLOADS = {
    "logbook.json",
    "pages/01-current-six-claim-release-audit/page.md",
    "pages/claim-2-marginal-single-exact/page.md",
    "pages/claim-4-marginal-clustered/page.md",
    "pages/claim-5-concentration/page.md",
    "pages/claim-6-openml-audit/page.md",
}

SECRET_PATTERNS = {
    "hugging_face_token": re.compile(rb"hf_[A-Za-z0-9]{20,}"),
    "github_token": re.compile(rb"gh[pousr]_[A-Za-z0-9_]{20,}"),
    "private_key": re.compile(rb"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_manifest(path: Path) -> dict[str, str]:
    lines = path.read_text().splitlines()
    assert lines and lines[0] == "sha256\tpath"
    result = {}
    for line in lines[1:]:
        digest, relpath = line.split("\t", 1)
        assert relpath not in result
        result[relpath] = digest
    return result


def logbook_files(node: dict) -> list[str]:
    files = [node["file"]]
    for child in node.get("children", []):
        files.extend(logbook_files(child))
    return files


def verify_release_candidate(claim_statuses: dict[str, str]) -> dict:
    old = read_manifest(OLD_MANIFEST)
    candidate_paths = {
        str(path.relative_to(SPACE))
        for path in SPACE.rglob("*")
        if path.is_file()
    }
    missing_old_paths = sorted(set(old) - candidate_paths)
    assert not missing_old_paths

    # logbook.json must change to expose additive pages. All other judged files,
    # including every old evidence page, must remain byte-identical.
    changed_old_files = sorted(
        relpath
        for relpath, digest in old.items()
        if relpath != "logbook.json" and sha256(SPACE / relpath) != digest
    )
    assert not changed_old_files

    logbook = json.loads((SPACE / "logbook.json").read_text())
    assert logbook["space_id"] == "DineshAI/J0y3sNbo9G"
    referenced = logbook_files(logbook["root"])
    assert len(referenced) == len(set(referenced))
    missing_references = sorted(relpath for relpath in referenced if not (SPACE / relpath).is_file())
    assert not missing_references

    allowlist = {
        line.strip()
        for line in (RELEASE / "upload_allowlist.txt").read_text().splitlines()
        if line.strip()
    }
    assert allowlist == EXPECTED_UPLOADS

    upload_manifest = read_manifest(RELEASE / "upload_sha256.tsv")
    assert set(upload_manifest) == EXPECTED_UPLOADS
    upload_hash_mismatches = sorted(
        relpath
        for relpath, digest in upload_manifest.items()
        if sha256(SPACE / relpath) != digest
    )
    assert not upload_hash_mismatches

    for relpath in allowlist:
        assert Path(relpath).suffix in {".json", ".md"}
        raw = (SPACE / relpath).read_bytes()
        assert b"\0" not in raw
        raw.decode("utf-8")

    secret_hits = []
    scan_roots = [ROOT / ".openresearch" / "artifacts", RELEASE]
    for scan_root in scan_roots:
        for path in scan_root.rglob("*"):
            if not path.is_file():
                continue
            raw = path.read_bytes()
            for pattern_name, pattern in SECRET_PATTERNS.items():
                if pattern.search(raw):
                    secret_hits.append(
                        {"path": str(path.relative_to(ROOT)), "pattern": pattern_name}
                    )
    assert not secret_hits

    expected_statuses = {
        "claim_1": "verified",
        "claim_2": "falsified",
        "claim_3": "verified",
        "claim_4": "falsified",
        "claim_5": "verified",
        "claim_6": "blocked",
    }
    assert claim_statuses == expected_statuses
    terminal = {"verified", "falsified"}
    release_gate_met = all(status in terminal for status in claim_statuses.values())
    assert not release_gate_met

    return {
        "judged_revision": "260bbe2fb64833c38a8acc22ab01b8d67a19d928",
        "old_file_count": len(old),
        "candidate_file_count": len(candidate_paths),
        "old_file_set_is_subset": True,
        "unchanged_old_files_except_logbook": len(old) - 1,
        "changed_old_files_except_logbook": changed_old_files,
        "logbook_json_valid": True,
        "logbook_references_resolve": True,
        "upload_allowlist": sorted(allowlist),
        "upload_allowlist_is_text_only": True,
        "upload_hashes_match": True,
        "secret_scan_hits": secret_hits,
        "claim_statuses": claim_statuses,
        "release_gate_met": release_gate_met,
        "publication_authorized": False,
    }


if __name__ == "__main__":
    statuses = {
        "claim_1": "verified",
        "claim_2": "falsified",
        "claim_3": "verified",
        "claim_4": "falsified",
        "claim_5": "verified",
        "claim_6": "blocked",
    }
    print(json.dumps(verify_release_candidate(statuses), indent=2))
