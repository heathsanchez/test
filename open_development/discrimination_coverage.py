"""Pre-routing external coverage audit, NOT a discrimination qualification.

The canonical eligibility predicate already requires successful role replay.
Audit that boundary before claiming it supplies four developmental classes.
No external scoring bytes are needed to implement or test this audit.
"""
from __future__ import annotations

import argparse
from fractions import Fraction
from hashlib import sha1, sha256
import json
from pathlib import Path
import re
import subprocess

from .external_minif2f_entry import extract_candidates, freeze_source
from .external_minif2f import CORPUS_COMMIT, CORPUS_REPOSITORY, TEST_PATH, TEST_BLOB_SHA1
from .residual import ResidualEnvelope
from .runtime import EvidenceStore, digest

PARENT = "003e6ccfa91205a1f0ea408656c10b8afbdb10c4"
FILE_SHA256 = "8e135204947654a6f5234ee3da830ea7b72337f33dc29229fd8be6c69ac1c0b7"
OUTCOME = "UNKNOWN_EXTERNAL_ROUTE_COVERAGE"
CLASSES = ("REUSE", "EXAPTATION", "EXPANSION", "UNKNOWN")


def require(ok, message):
    if not ok:
        raise ValueError(message)


def source_identity(root):
    paths = sorted((root / "open_development").rglob("*.py"))
    paths += [root / ".github/workflows/developmental-discrimination-v1.yml"]
    return {str(p.relative_to(root)): sha256(p.read_bytes()).hexdigest() for p in paths}


def freeze(root, external, state, source_commit, nonce):
    require(not external.exists(), "external scoring path already exists")
    require(not state.exists(), "initial state must be fresh")
    require(re.fullmatch(r"[0-9a-f]{40}", source_commit), "invalid source commit")
    require(re.fullmatch(r"[1-9][0-9]*:[1-9][0-9]*", nonce), "invalid run:attempt nonce")
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()
    require(head == source_commit, "wrong source commit")
    subprocess.run(["git", "merge-base", "--is-ancestor", PARENT, head], cwd=root, check=True)
    source = freeze_source(state, source_commit)
    body = {"schema": "developmental-discrimination-coverage-freeze/v1",
            "canonical_parent_commit": PARENT, "source_commit": source_commit,
            "selection_nonce": nonce, "files": source_identity(root),
            "retained_source": source, "external_path_absent": True,
            "protocol": "canonical MiniF2F eligibility, fresh source state per obligation",
            "minimum_tasks": 12, "minimum_per_class": 3}
    return {**body, "digest": digest(body)}


def pool_audit(text, nonce):
    """Administrator only: independent arithmetic checks on normalized candidates.

    Eligibility is the canonical parser's exact boundary. This is NOT an
    independent Lean parser, and this routine never fabricates route predictions.
    A replayable global square is a role-only witness, ruling out EXPANSION.
    """
    candidates = extract_candidates(text)
    rows = []
    for task in candidates:
        p = {int(k): Fraction(v) for k, v in task["polynomial"].items()}
        a, b, c = p.get(2, 0), p.get(1, 0), p.get(0, 0)
        require(set(p) <= {0, 1, 2} and a > 0, "outside quadratic boundary")
        r, d = -b / (2 * a), c - b * b / (4 * a)
        require(d >= 0 and -2 * a * r == b and a * r * r + d == c,
                "independent role witness failed")
        rows.append({"task_id": task["name"], "task_hash": task["statement_sha256"],
                     "role_only_witness": {"A": str(a), "r": str(r), "D": str(d)},
                     "polynomial": task["polynomial"],
                     "expansion_ruled_out": True})
    rows.sort(key=lambda row: digest({"nonce": nonce, "task": row["task_hash"]}))
    # Frozen initial contracts cover rays/intervals, not all-real quadratics.
    # Every eligible polynomial has a lawful supplied global-role realization.
    counts = {k: len(rows) if k == "EXAPTATION" else 0 for k in CLASSES}
    return {"candidate_count": len(rows), "candidate_pool_digest": digest(candidates),
            "administrator_rows": rows, "initial_state_route_counts": counts,
            "missing_classes": [k for k in CLASSES if counts[k] < 3],
            "route_predictions": [], "scored_tasks": 0,
            "scoring_admissions": [], "v4_eligible": False,
            "outcome": OUTCOME}


def audit(root, external, state, manifest, source_commit, nonce):
    require(manifest.get("source_commit") == source_commit, "wrong source commit")
    require(manifest.get("selection_nonce") == nonce, "wrong selection nonce")
    require(manifest.get("canonical_parent_commit") == PARENT, "wrong canonical parent")
    require(manifest.get("external_path_absent") is True, "invalid freeze chronology")
    require(manifest.get("digest") == digest({k: v for k, v in manifest.items() if k != "digest"}),
            "tampered freeze")
    require(manifest["files"] == source_identity(root), "stale frozen source")
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=external, text=True).strip()
    data = (external / TEST_PATH).read_bytes()
    blob = sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()
    require(commit == CORPUS_COMMIT and blob == TEST_BLOB_SHA1
            and sha256(data).hexdigest() == FILE_SHA256, "wrong external corpus identity")
    store = EvidenceStore(state)
    before = (digest(store.state()), digest(store.events()))
    require(before == (manifest["retained_source"]["state_id"],
                       manifest["retained_source"]["ledger_digest"]), "mutated source state")
    result = pool_audit(data.decode(), nonce)
    require(before == (digest(store.state()), digest(store.events())), "hidden admission")
    store.close()
    residual = ResidualEnvelope(
        residual_class=OUTCOME, diagnosis="unknown",
        verifier_certified_witness={"counts": result["initial_state_route_counts"],
                                    "pool_digest": result["candidate_pool_digest"]},
        closure_id=result["candidate_pool_digest"], budget_id=digest({"minimum_tasks": 12}),
        necessary_constraint={"minimum_per_class": 3, "classes": list(CLASSES)},
        version_space_id=digest({"eligibility": "canonical-global-quadratic"}),
        evidence_strength="exhaustive-relative-to-frozen-eligibility-predicate",
        source={"commit": CORPUS_COMMIT, "file_sha256": FILE_SHA256},
        domain_payload={"not_a_language_obstruction": True}).to_mapping()
    body = {**result, "schema": "developmental-discrimination-coverage/v1",
            "source_commit": source_commit, "canonical_parent_commit": PARENT,
            "freeze_digest": manifest["digest"], "selection_nonce": nonce,
            "external_repository": CORPUS_REPOSITORY, "external_commit": commit,
            "external_file": TEST_PATH, "external_blob": blob, "external_sha256": FILE_SHA256,
            "residual": residual, "history_unchanged": True,
            "limitations": ["coverage audit only; no four-way developer qualification",
                            "not an exhaustive audit of MiniF2F semantics or other corpora",
                            "canonical parser and supplied role grammar remain fixed",
                            "no human blinding; no task stream delivered to developer",
                            "no new Lean claim and no release v4"]}
    return {**body, "evidence_digest": digest(body)}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("stage", choices=["freeze", "audit", "validate"])
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--external", type=Path, default=Path("external"))
    parser.add_argument("--state", type=Path, default=Path("coverage-state.sqlite"))
    parser.add_argument("--manifest", type=Path, default=Path("coverage-freeze.json"))
    parser.add_argument("--result", type=Path, default=Path("coverage-result.json"))
    parser.add_argument("--source-commit", required=True)
    parser.add_argument("--nonce", required=True)
    args = parser.parse_args()
    if args.stage == "freeze":
        result = freeze(args.root, args.external, args.state, args.source_commit, args.nonce)
        args.manifest.write_text(json.dumps(result, indent=2) + "\n")
        print("COVERAGE_SOURCE_FREEZE", result["digest"])
    else:
        manifest = json.loads(args.manifest.read_text())
        result = audit(args.root, args.external, args.state, manifest, args.source_commit, args.nonce)
        if args.stage == "validate":
            require(json.loads(args.result.read_text()) == result, "recomputed evidence mismatch")
        else:
            args.result.write_text(json.dumps(result, indent=2) + "\n")
        print(result["outcome"], result["initial_state_route_counts"], result["evidence_digest"])


if __name__ == "__main__":
    main()
