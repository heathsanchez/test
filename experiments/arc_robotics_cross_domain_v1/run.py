from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

from .core import (
    discover_source_operator,
    run_arm,
    serialize_capability,
    source_examples,
)

ROOT = Path(__file__).parent
ARMS = ("COLD", "WARM", "SHAM", "ABLATION", "RESTART")
N_WORLDS = 64


def derive_seed(github_sha: str, github_run_id: str) -> int:
    material = f"{github_sha}:{github_run_id}".encode("utf-8")
    return int.from_bytes(hashlib.sha256(material).digest()[:8], "big")


def build_packet(github_sha: str, github_run_id: str, n_worlds: int = N_WORLDS) -> tuple[list[dict], dict, str]:
    seed = derive_seed(github_sha, github_run_id)
    rows = [run_arm(arm, seed, n_worlds=n_worlds) for arm in ARMS]
    source_code, source_evaluations = discover_source_operator(source_examples())
    metadata = {
        "schema": "arc.robotics.cross_domain.v1",
        "seed": seed,
        "seed_provenance": {
            "github_sha": github_sha,
            "github_run_id": github_run_id,
        },
        "n_worlds": n_worlds,
        "arms": list(ARMS),
        "source_code": source_code,
        "source_discovery_evaluations": source_evaluations,
        "llm_used": False,
    }
    return rows, metadata, serialize_capability(source_code)


def main() -> None:
    github_sha = os.environ.get("GITHUB_SHA", "local")
    github_run_id = os.environ.get("GITHUB_RUN_ID", "0")
    rows, metadata, capability = build_packet(github_sha, github_run_id)

    (ROOT / "answers.json").write_text(json.dumps(rows, indent=2, sort_keys=True) + "\n")
    (ROOT / "run_metadata.json").write_text(json.dumps(metadata, indent=2, sort_keys=True) + "\n")
    (ROOT / "capability.json").write_text(capability + "\n")

    print(
        "ARC_ROBOTICS_CROSS_DOMAIN_V1_RUN_PASS",
        json.dumps(
            {
                "seed": metadata["seed"],
                "n_worlds": metadata["n_worlds"],
                "costs": {row["arm"]: row["developmental_cost"] for row in rows},
            },
            sort_keys=True,
        ),
        flush=True,
    )


if __name__ == "__main__":
    main()
