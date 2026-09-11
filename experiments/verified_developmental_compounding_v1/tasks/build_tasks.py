#!/usr/bin/env python3
"""Generate the frozen, deterministic task manifest and expected observations."""
import json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parents[1]))
from controller.core import Adapter, canonical_hash

ROOT = Path(__file__).resolve().parent

domains = {
    "finite_theorem": {
        "operations": ["and_left", "xor_right", "negate_left", "swap"],
        "inputs": [(0,0),(0,1),(1,0),(1,1)],
        "chain": ["swap", "negate_left", "xor_right", "and_left"],
        "authority": "exhaustive evaluation over the complete two-bit carrier",
    },
    "program_synthesis": {
        "operations": ["duplicate", "rotate", "upper", "reverse"],
        "inputs": ["ab", "xY", "cab", "pqR"],
        "chain": ["reverse", "upper", "rotate", "duplicate"],
        "authority": "exact executable I/O replay over the frozen specification set",
    },
    "rule_induction": {
        "operations": ["rotate_rows", "transpose", "invert", "flip_h"],
        "inputs": [
            [[0,1],[0,0]], [[1,0],[1,1]], [[0,1,0],[1,0,0],[1,1,0]],
            [[1,0,1],[0,0,1],[1,0,0]],
        ],
        "chain": ["flip_h", "invert", "transpose", "rotate_rows"],
        "authority": "exact grid equality over all frozen transformation cases",
    },
}

out = {"schema_version": 1, "seed": 20260911, "domains": []}
for name, d in domains.items():
    adapter = Adapter({"domain": name, "operations": d["operations"]})
    tasks = []
    for stage in range(1,5):
        program = d["chain"][:stage]
        examples = [{"input": x, "output": adapter.execute(tuple(program), x)} for x in d["inputs"]]
        tasks.append({
            "stage": stage, "held_out": name == "rule_induction" and stage == 4,
            "target_program": program, "examples": examples,
            "verifier_authority": d["authority"],
        })
    out["domains"].append({"domain": name, "operations": d["operations"], "tasks": tasks})
out["manifest_sha256"] = canonical_hash(out)
(ROOT / "tasks.json").write_text(json.dumps(out, indent=2) + "\n")
print(out["manifest_sha256"])
