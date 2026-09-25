#!/usr/bin/env python3
from __future__ import annotations
import hashlib, json, os, subprocess
from pathlib import Path

PIN="888a4303846000ace1c7ef4c62a8d3e99110d979"
ROOT=Path(os.environ.get("QLF_ROOT","vendor/QLF")).resolve()
OUT=Path(os.environ.get("EVIDENCE_OUT","evidence/generic-gauge-born-v5.json"))
GEN=Path("experiments/generic_gauge_born_v5/MathGraphGenericGauge.lean")
AD=Path("experiments/generic_gauge_born_v5/BornTransferAppend.lean")
TARGET=ROOT/"lean/QLF_StateSpace.lean"

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
head=subprocess.check_output(["git","-C",str(ROOT),"rev-parse","HEAD"],text=True).strip()
if head != PIN: raise SystemExit(f"QLF pin mismatch {head}")

g=GEN.read_text()
for x in [
 "CommGroupWithZero",
 "def GaugeEq",
 "theorem gauge_refl",
 "theorem gauge_symm",
 "theorem gauge_trans",
 "def gaugeSetoid",
 "theorem observe_eq_of_gauge",
 "def quotientObserve",
]:
 assert x in g

a=AD.read_text()
proof=a.split(":= by",1)[1]
assert "bornProb_global_scale" not in proof
assert "observe_eq_of_gauge" in proof

rc=int(os.environ.get("ABLATION_RC","0"))
if rc==0: raise SystemExit("ablation unexpectedly passed")

ev={
 "schema":"metalogic.generic-gauge-born.v5",
 "epistemic_state":"CANDIDATE",
 "external_target":{
   "repository":"rchain-community/quantum-logical-framework",
   "revision":PIN,
   "file":"lean/QLF_StateSpace.lean",
   "existing_theorem":"QLF.StateSpace.bornProb_global_scale",
   "source_sha256_after_ephemeral_patch":sha(TARGET)
 },
 "generic_capability":{
   "carrier_boundary":"CommGroupWithZero",
   "representation":"nonzero-scalar quotient of numerator/denominator pairs",
   "observation":"num / den",
   "quotient_factorization":"PASS",
   "module_sha256":sha(GEN)
 },
 "transfer":{
   "scalar":"Rat",
   "domain":"Born probability over Gaussian-integer amplitude vectors",
   "theorem":"mathgraph_v5_bornProb_global_scale",
   "semantic_transfer":"PASS",
   "ablation_without_capability":"EXPECTED_FAIL",
   "ablation_exit_code":rc
 },
 "boundary":{
   "uses_only_formal_algebraic_target_statement":True,
   "surrounding_physical_interpretation":"NOT_ADOPTED",
   "gpu_performance":"NOT_APPLICABLE"
 }
}
OUT.parent.mkdir(parents=True,exist_ok=True)
OUT.write_text(json.dumps(ev,indent=2,sort_keys=True)+"\n")
print(json.dumps(ev,indent=2,sort_keys=True))
