"""Fail-closed qualification manifest for the bounded developmental core."""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any, Mapping

from .runtime import canonical, digest

SCHEMA = "open-development-release/v1"
CLAIM = "bounded verifier-governed developmental machine"
LIMITATIONS = [
    "finite supplied constructor grammars",
    "exact rational polynomial proof domain",
    "no unrestricted grammar invention or completeness claim",
    "generated proof certificates use the exact-rational checker; generic rules and qualified programs have separate Lean evidence",
]


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def build_release(*, repository: str, source_commit: str, run_id: int,
                  finite: Mapping[str, Any], proof: Mapping[str, Any],
                  growth: Mapping[str, Any]) -> dict[str, Any]:
    _require(re.fullmatch(r"[0-9a-f]{40}", source_commit) is not None,
             "source commit must be a full lowercase Git SHA")
    _require(run_id > 0 and re.fullmatch(r"[^/]+/[^/]+", repository) is not None,
             "invalid GitHub run identity")
    _require(finite.get("first") == "verified" and finite.get("second") == "verified"
             and finite.get("ablated") == "unknown", "finite causal gate failed")
    _require(proof.get("cold") == ["unknown", "unknown"]
             and proof.get("warm") == ["verified", "verified"]
             and proof.get("restart") is True
             and proof.get("exact_ablation") == "unknown", "proof self-application gate failed")
    _require(growth.get("cold_O2") == "unknown" and growth.get("O1") == "verified"
             and growth.get("O2") == "verified"
             and growth.get("unlisted_O3_zero_acquisition_budget") == "verified"
             and growth.get("second_restart") is True
             and growth.get("removal_ablation") == "unknown",
             "capability-growth causal gate failed")
    body = {
        "schema": SCHEMA,
        "claim": CLAIM,
        "scope": "finite observational and exact-rational proof-program development",
        "source_commit": source_commit,
        "run_id": run_id,
        "run_url": f"https://github.com/{repository}/actions/runs/{run_id}",
        "controls": {
            "finite": dict(finite), "proof_procedure": dict(proof),
            "capability_growth": dict(growth),
        },
        "formal_authorities": [
            "Lean 4.24.0 MSI/developmental bridge and finite realization",
            "pinned Mathlib generic proof-program rules and concrete O2/O3 semantics",
        ],
        "limitations": LIMITATIONS,
    }
    return {**body, "evidence_digest": digest(body)}


def validate_release(manifest: Mapping[str, Any]) -> None:
    _require(manifest.get("schema") == SCHEMA and manifest.get("claim") == CLAIM,
             "unknown release claim or schema")
    supplied = manifest.get("evidence_digest")
    body = {key: value for key, value in manifest.items() if key != "evidence_digest"}
    _require(isinstance(supplied, str) and supplied == digest(body),
             "release evidence is missing, malformed, or stale")
    rebuilt = build_release(
        repository=manifest["run_url"].split("github.com/", 1)[1].split("/actions/", 1)[0],
        source_commit=manifest["source_commit"], run_id=manifest["run_id"],
        finite=manifest["controls"]["finite"],
        proof=manifest["controls"]["proof_procedure"],
        growth=manifest["controls"]["capability_growth"])
    _require(rebuilt == dict(manifest), "release evidence does not match its declared run")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repository", required=True)
    parser.add_argument("--source-commit", required=True)
    parser.add_argument("--run-id", required=True, type=int)
    parser.add_argument("--finite", type=Path, required=True)
    parser.add_argument("--proof", type=Path, required=True)
    parser.add_argument("--growth", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    load = lambda path: json.loads(path.read_text())
    manifest = build_release(repository=args.repository, source_commit=args.source_commit,
                             run_id=args.run_id, finite=load(args.finite),
                             proof=load(args.proof), growth=load(args.growth))
    validate_release(manifest)
    args.output.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    print("RELEASE_EVIDENCE_PASS", manifest["evidence_digest"])


if __name__ == "__main__":
    main()
