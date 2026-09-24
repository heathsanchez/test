#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import os
import subprocess
from pathlib import Path

PIN = "95a01f598e2cd1cac4052e5e5ff9145c658e18db"
ROOT = Path(os.environ.get("VERITILE_ROOT", "vendor/VeriTile")).resolve()
OUT = Path(os.environ.get("EVIDENCE_OUT", "evidence/veritile-capability-transfer-v1.json"))
SEED = ROOT / "VeriTile/Triton/Math/Softmax.lean"
HOLDOUT = ROOT / "bench/tritonbench_g/softmax_reducev/SoftmaxReducev.lean"
CAP = Path("experiments/veritile_capability_transfer/MathGraphShiftCapability.lean")
TRANSFER = Path("experiments/veritile_capability_transfer/TransferAppend.lean")

def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def nonblank_code_lines(text: str) -> int:
    return sum(
        1 for line in text.splitlines()
        if line.strip()
        and not line.lstrip().startswith("--")
        and not line.lstrip().startswith("/-")
        and not line.lstrip().startswith("*")
    )

def slice_between(text: str, start: str, end: str) -> str:
    i = text.index(start)
    j = text.index(end, i)
    return text[i:j]

git_head = subprocess.check_output(
    ["git", "-C", str(ROOT), "rev-parse", "HEAD"], text=True
).strip()
if git_head != PIN:
    raise SystemExit(f"VeriTile pin mismatch: {git_head} != {PIN}")

seed_text = SEED.read_text()
holdout_text = HOLDOUT.read_text()
cap_text = CAP.read_text()
transfer_text = TRANSFER.read_text()

assert "theorem naive_eq_stable" in seed_text
assert "theorem srWeightedSum_shift_invariant" in holdout_text
assert "theorem mathgraph_transfer_srWeightedSum_shift_invariant" in holdout_text
transfer_proof = transfer_text.split(":= by", 1)[1]
assert "srWeightedSum_shift_invariant" not in transfer_proof
assert "weighted_shift_invariant" in cap_text

baseline_segment = slice_between(
    holdout_text,
    "theorem srWeightedSum_denom_shift",
    "/-! ## The spec-equals-genuine bridge",
)

ablation_rc = int(os.environ.get("ABLATION_RC", "0"))
if ablation_rc == 0:
    raise SystemExit("Ablation unexpectedly elaborated without the capability")

evidence = {
    "schema": "metalogic.veritile-capability-transfer.v1",
    "epistemic_state": "CANDIDATE",
    "veritile": {
        "repository": "Lizn-zn/VeriTile",
        "revision": PIN,
        "seed_file": str(SEED.relative_to(ROOT)),
        "seed_sha256": sha256(SEED),
        "seed_theorem": "VeriTile.Triton.TiledSoftmax.naive_eq_stable",
        "holdout_file": str(HOLDOUT.relative_to(ROOT)),
        "holdout_sha256_after_ephemeral_patch": sha256(HOLDOUT),
        "holdout_theorem": "VeriTile.Bench.TritonBenchG.SoftmaxReducev.srWeightedSum_shift_invariant",
    },
    "compiled_capability": {
        "id": "normalized-exp-weighted-quotient.shift-invariance@1",
        "file": str(CAP),
        "sha256": sha256(CAP),
        "protected_consequence": "normalized exponentially weighted quotient value",
        "assumptions": ["finite index type Fin S", "real exponential arithmetic"],
        "excluded": [
            "IEEE-754 behavior",
            "PTX/codegen",
            "GPU concurrency",
            "runtime performance",
        ],
    },
    "transfer": {
        "theorem": "mathgraph_transfer_srWeightedSum_shift_invariant",
        "semantic_transfer": "PASS",
        "ablation_without_capability": "EXPECTED_FAIL",
        "ablation_exit_code": ablation_rc,
        "transfer_instantiation_code_lines": nonblank_code_lines(transfer_text),
        "existing_holdout_shift_stack_code_lines": nonblank_code_lines(baseline_segment),
    },
    "qualification": {
        "lean_semantics": "WARRANTED_IF_HOSTED_WORKFLOW_GREEN",
        "gpu_performance": "UNKNOWN",
        "external_float_codegen_boundary": "UNKNOWN",
        "promotion": "do not promote beyond bounded Lean semantic transfer",
    },
}

OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n")
print(json.dumps(evidence, indent=2, sort_keys=True))
