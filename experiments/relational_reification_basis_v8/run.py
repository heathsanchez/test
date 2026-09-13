#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from basis import PRIMITIVES, BasisConfig, all_basis_subsets
from challenge_pack import run_ladder


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    full = BasisConfig.from_names(PRIMITIVES)
    full_result = run_ladder(full, detailed=True)

    subset_rows = []
    passing_sets = []

    for cfg in all_basis_subsets():
        r = run_ladder(cfg, detailed=False)
        row = {
            "basis": list(cfg.names()),
            "primitive_count": len(cfg.names()),
            "full_pass": r["full_pass"],
            "gates": r["gates"],
            "passed_gate_count": sum(bool(v) for v in r["gates"].values()),
            "total_gate_count": len(r["gates"]),
        }
        subset_rows.append(row)
        if r["full_pass"]:
            passing_sets.append(set(cfg.names()))

    minimal = []
    for s in passing_sets:
        if not any(t < s for t in passing_sets):
            minimal.append(s)
    minimal.sort(key=lambda s: (len(s), sorted(s)))

    ablations = {}
    for primitive in PRIMITIVES:
        names = [p for p in PRIMITIVES if p != primitive]
        r = run_ladder(BasisConfig.from_names(names), detailed=False)
        ablations[primitive] = {
            "basis": names,
            "full_pass": r["full_pass"],
            "failed_gates": [k for k, v in r["gates"].items() if not v],
        }

    unique_minimal = (
        len(minimal) == 1
        and minimal[0] == set(PRIMITIVES)
    )
    each_necessary = all(
        not ablations[p]["full_pass"]
        and bool(ablations[p]["failed_gates"])
        for p in PRIMITIVES
    )

    evidence = {
        "experiment": "relational_reification_basis_v8",
        "scientific_freeze_commit": "54c67f03f6f6861a15e03d66f1a4480659784f3b",
        "post_freeze_challenge_ladder": True,
        "hashes": {
            "PROTOCOL.md": sha256(HERE / "PROTOCOL.md"),
            "FREEZE.json": sha256(HERE / "FREEZE.json"),
            "basis.py": sha256(HERE / "basis.py"),
            "kernel.py": sha256(HERE / "kernel.py"),
            "challenge_pack.py": sha256(HERE / "challenge_pack.py"),
        },
        "full_basis": full_result,
        "subset_matrix": subset_rows,
        "passing_basis_count": len(passing_sets),
        "minimal_passing_bases": [sorted(s) for s in minimal],
        "single_primitive_ablations": ablations,
        "meta_gates": {
            "full_basis_passes_ladder": full_result["full_pass"],
            "all_4_subsets_exhausted": len(subset_rows) == 4,
            "unique_inclusion_minimal_full_pass_basis": unique_minimal,
            "every_primitive_has_causal_ablation_failure": each_necessary,
            "product_not_object_primitive": "PRODUCT" not in PRIMITIVES,
            "quotient_not_object_primitive": "QUOTIENT" not in PRIMITIVES,
        },
    }

    evidence["full_pass"] = all(evidence["meta_gates"].values())
    evidence["verdict"] = (
        "VERIFIED_RELATION_COMPOSE_REGENERATES_V7_VIA_VERIFIED_REIFICATION"
        if evidence["full_pass"]
        else "RELATIONAL_REIFICATION_V8_GAPS_EXPOSED"
    )

    (HERE / "evidence.json").write_text(
        json.dumps(evidence, indent=2, sort_keys=True, default=str) + "\n"
    )

    print(json.dumps(evidence, indent=2, sort_keys=True, default=str))
    return 0 if evidence["full_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
