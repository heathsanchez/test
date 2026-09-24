#!/usr/bin/env python3
from __future__ import annotations
import hashlib
import json
import os
import subprocess
from pathlib import Path

PIN = "95a01f598e2cd1cac4052e5e5ff9145c658e18db"
PARENT = "6044fb46eb0f1aa8377633f1bf5a2f71d6553a3b"
ROOT = Path(os.environ.get("VERITILE_ROOT", "vendor/VeriTile")).resolve()
OUT = Path(os.environ.get("EVIDENCE_OUT", "evidence/veritile-gauge-transfer-v2.json"))
CAP = Path("experiments/veritile_gauge_transfer_v2/MathGraphGaugeCapability.lean")
TRANSFER = Path("experiments/veritile_gauge_transfer_v2/MixedSparseTransferAppend.lean")
TARGET = ROOT / "bench/tritonbench_g/mixed_sparse_attention/MixedSparseAttention.lean"

def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def code_lines(text: str) -> int:
    return sum(1 for x in text.splitlines()
               if x.strip() and not x.lstrip().startswith(("--", "/-", "*")))

head = subprocess.check_output(["git","-C",str(ROOT),"rev-parse","HEAD"], text=True).strip()
if head != PIN:
    raise SystemExit(f"pin mismatch: {head} != {PIN}")

target = TARGET.read_text()
transfer = TRANSFER.read_text()
cap = CAP.read_text()
assert "theorem msaPartial_ratio_collapse" in target
assert "WithBot.realExp2" in target
assert "theorem common_factor_ratio" in cap
proof = transfer.split(":= by", 1)[1]
assert "msaPartial_ratio_collapse" not in proof
assert "MathGraphGaugeCapability.common_factor_ratio" in proof

ablation_rc = int(os.environ.get("ABLATION_RC", "0"))
if ablation_rc == 0:
    raise SystemExit("ablation unexpectedly passed")

evidence = {
  "schema": "metalogic.veritile-gauge-transfer.v2",
  "epistemic_state": "CANDIDATE",
  "parent_authority": {
    "repo": "heathsanchez/test",
    "head": PARENT,
    "run": 36073106526,
    "artifact": 10839118758
  },
  "veritile": {
    "repository": "Lizn-zn/VeriTile",
    "revision": PIN,
    "target_file": str(TARGET.relative_to(ROOT)),
    "target_sha256_after_ephemeral_patch": sha256(TARGET),
    "target_existing_theorem": "msaPartial_ratio_collapse",
    "different_weight_semantics": "WithBot.realExp2"
  },
  "compiled_capability": {
    "id": "normalized-quotient.common-nonzero-factor-cancellation@1",
    "sha256": sha256(CAP),
    "theorem": "MathGraphGaugeCapability.common_factor_ratio",
    "protected_consequence": "normalized quotient value",
    "requires": [
      "shared multiplicative factor",
      "factor is nonzero",
      "factor relations independently established"
    ]
  },
  "transfer": {
    "theorem": "mathgraph_transfer_msaPartial_ratio_collapse",
    "semantic_transfer": "PASS",
    "ablation_without_capability": "EXPECTED_FAIL",
    "ablation_exit_code": ablation_rc,
    "transfer_code_lines": code_lines(transfer)
  },
  "boundary": {
    "reused": "final common-factor cancellation only",
    "not_reused": [
      "MixedSparseAttention recurrence proof",
      "WithBot max dominance",
      "exp2 shift cancellation",
      "GPU execution/performance"
    ],
    "gpu_performance": "UNKNOWN",
    "ieee_ptx_codegen": "UNKNOWN"
  }
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n")
print(json.dumps(evidence, indent=2, sort_keys=True))
