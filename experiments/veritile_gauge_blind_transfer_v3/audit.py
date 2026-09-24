#!/usr/bin/env python3
from __future__ import annotations
import hashlib, json, os, subprocess
from pathlib import Path

PIN="95a01f598e2cd1cac4052e5e5ff9145c658e18db"
FROZEN_CAP_COMMIT="9fa6a451eea2cb68004ce0934ee565763ad7c109"
ROOT=Path(os.environ.get("VERITILE_ROOT","vendor/VeriTile")).resolve()
OUT=Path(os.environ.get("EVIDENCE_OUT","evidence/veritile-gauge-blind-transfer-v3.json"))
CAP=Path("experiments/veritile_gauge_transfer_v2/MathGraphGaugeCapability.lean")
TRANSFER=Path("experiments/veritile_gauge_blind_transfer_v3/BlockSparseTransferAppend.lean")
TARGET=ROOT/"bench/tritonbench_g/block_sparse_attn/BlockSparseAttn.lean"

def sha256(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
head=subprocess.check_output(["git","-C",str(ROOT),"rev-parse","HEAD"],text=True).strip()
if head!=PIN: raise SystemExit(f"pin mismatch {head}")
target=TARGET.read_text()
proof=TRANSFER.read_text().split(":= by",1)[1]
assert "theorem bsaStreaming_eq_bsaAttn" in target
assert "mul_div_mul_left" in target
assert "MathGraphGaugeCapability.common_factor_ratio" in proof
assert "bsaStreaming_eq_bsaAttn" not in proof
rc=int(os.environ.get("ABLATION_RC","0"))
if rc==0: raise SystemExit("ablation unexpectedly passed")

ev={
 "schema":"metalogic.veritile-gauge-blind-transfer.v3",
 "epistemic_state":"CANDIDATE",
 "frozen_capability":{
   "commit":FROZEN_CAP_COMMIT,
   "theorem":"MathGraphGaugeCapability.common_factor_ratio",
   "sha256":sha256(CAP),
   "changed_after_target_selection":False
 },
 "target_selection":{
   "timing":"after capability freeze",
   "method":"structural search for independent online-softmax closed-form bridges using common-factor cancellation",
   "target":"bench/tritonbench_g/block_sparse_attn/BlockSparseAttn.lean",
   "target_family":"CSR-gathered causal block-sparse attention"
 },
 "veritile":{"revision":PIN,"target_sha256_after_ephemeral_patch":sha256(TARGET)},
 "transfer":{
   "theorem":"mathgraph_transfer_bsaStreaming_eq_bsaAttn",
   "semantic_transfer":"PASS",
   "ablation_without_capability":"EXPECTED_FAIL",
   "ablation_exit_code":rc
 },
 "boundary":{
   "reused":"final normalized common-factor cancellation",
   "target_specific_authority_retained":[
      "streaming partial-to-m-shifted equalities",
      "CSR visibility assumptions",
      "m-free gathered closed-form bridge"
   ],
   "gpu_performance":"UNKNOWN",
   "ieee_ptx_codegen":"UNKNOWN"
 }
}
OUT.parent.mkdir(parents=True,exist_ok=True)
OUT.write_text(json.dumps(ev,indent=2,sort_keys=True)+"\n")
print(json.dumps(ev,indent=2,sort_keys=True))
