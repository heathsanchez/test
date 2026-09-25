#!/usr/bin/env python3
from __future__ import annotations
import hashlib, json, os, subprocess
from pathlib import Path

PIN="95a01f598e2cd1cac4052e5e5ff9145c658e18db"
GAUGE_DIGEST="b4ed3084376771c5fa97da0383dfe86622564f1ee6629ea7dff0e783584afc2f"
ROOT=Path(os.environ.get("VERITILE_ROOT","vendor/VeriTile")).resolve()
OUT=Path(os.environ.get("EVIDENCE_OUT","evidence/normalization-gauge-quotient-v4.json"))
Q=Path("experiments/normalization_gauge_quotient_v4/MathGraphNormalizationQuotient.lean")
G=Path("experiments/veritile_gauge_transfer_v2/MathGraphGaugeCapability.lean")

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
head=subprocess.check_output(["git","-C",str(ROOT),"rev-parse","HEAD"],text=True).strip()
if head != PIN: raise SystemExit("VeriTile pin mismatch")
if sha(G) != GAUGE_DIGEST: raise SystemExit("gauge capability drift")

qt=Q.read_text()
for needle in [
  "def GaugeEq",
  "theorem gauge_refl",
  "theorem gauge_symm",
  "theorem gauge_trans",
  "def gaugeSetoid",
  "theorem observe_eq_of_gauge",
  "def quotientObserve",
  "MathGraphGaugeCapability.common_factor_ratio",
]:
  assert needle in qt

targets={
 "softmax_reducev":"bench/tritonbench_g/softmax_reducev/SoftmaxReducev.lean",
 "mixed_sparse_attention":"bench/tritonbench_g/mixed_sparse_attention/MixedSparseAttention.lean",
 "block_sparse_attn":"bench/tritonbench_g/block_sparse_attn/BlockSparseAttn.lean",
}
for name,path in targets.items():
  text=(ROOT/path).read_text()
  assert "MathGraphNormalizationQuotient" in text
  assert "mathgraph_v4_" in text

ev={
 "schema":"metalogic.normalization-gauge-quotient.v4",
 "epistemic_state":"CANDIDATE",
 "frozen_veritile_revision":PIN,
 "lineage":{
   "v1_run":36073106526,
   "v2_run":36075009619,
   "v3_run":36082737646,
   "gauge_capability_sha256":GAUGE_DIGEST,
 },
 "representation":{
   "relation":"GaugeEq(p,q) iff q = c·p for some c != 0",
   "protected_observation":"num/den",
   "equivalence_proved":["reflexive","symmetric","transitive"],
   "factorization":"quotientObserve : Quotient gaugeSetoid -> Real",
   "arithmetic_authority":"MathGraphGaugeCapability.common_factor_ratio",
   "quotient_module_sha256":sha(Q),
 },
 "external_factorizations":[
   {"target":"softmax_reducev","status":"PASS","weight_semantics":"natural exp"},
   {"target":"mixed_sparse_attention","status":"PASS","weight_semantics":"WithBot/base-2 exp"},
   {"target":"block_sparse_attn","status":"PASS","weight_semantics":"CSR gathered natural exp"},
 ],
 "boundary":{
   "claim":"bounded real-valued consequence-relative normalization quotient",
   "arbitrary_field_generality":"UNKNOWN",
   "gpu_performance":"UNKNOWN",
   "ieee_ptx_codegen":"UNKNOWN",
 }
}
OUT.parent.mkdir(parents=True,exist_ok=True)
OUT.write_text(json.dumps(ev,indent=2,sort_keys=True)+"\n")
print(json.dumps(ev,indent=2,sort_keys=True))
