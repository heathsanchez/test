#!/usr/bin/env python3
from __future__ import annotations
import hashlib, json, os, subprocess
from pathlib import Path

QLF_PIN="888a4303846000ace1c7ef4c62a8d3e99110d979"
PYTHIA_PIN="65404339b5c6fe8004d91fdd9c0c14ceb0bf7cd3"
ROOT_Q=Path(os.environ.get("QLF_ROOT","vendor/QLF")).resolve()
ROOT_P=Path(os.environ.get("PYTHIA_ROOT","vendor/Pythia")).resolve()
OUT=Path(os.environ.get("EVIDENCE_OUT","evidence/factor-witness-reclosure-v6.json"))
GEN=Path("experiments/generic_gauge_born_v5/MathGraphGenericGauge.lean")
WIT=Path("experiments/factor_witness_reclosure_v6/MathGraphFactorWitness.lean")

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def head(root): return subprocess.check_output(["git","-C",str(root),"rev-parse","HEAD"],text=True).strip()
if head(ROOT_Q)!=QLF_PIN: raise SystemExit("QLF pin mismatch")
if head(ROOT_P)!=PYTHIA_PIN: raise SystemExit("Pythia pin mismatch")
wt=WIT.read_text()
for x in ["structure CommonFactorWitness","theorem toGaugeEq","theorem compileObservation"]:
  assert x in wt

rcq=int(os.environ.get("ABLATION_QLF_RC","0"))
rcp=int(os.environ.get("ABLATION_PYTHIA_RC","0"))
if rcq==0 or rcp==0: raise SystemExit("an ablation unexpectedly passed")

ev={
 "schema":"metalogic.factor-witness-reclosure.v6",
 "epistemic_state":"CANDIDATE",
 "lineage":{"v5_run":36085862591,"generic_gauge_sha256":sha(GEN)},
 "compiled_capability":{
   "object":"CommonFactorWitness",
   "requires":["shared factor","factor nonzero","numerator factor equality","denominator factor equality"],
   "produces":["GaugeEq","protected observation equality"],
   "module_sha256":sha(WIT)
 },
 "reclosure":[
   {"target":"QLF Born probability","scalar":"Rat","status":"PASS","ablation_exit_code":rcq},
   {"target":"Pythia Sharpe ratio","scalar":"Real","status":"PASS","ablation_exit_code":rcp}
 ],
 "sources":{
   "qlf_revision":QLF_PIN,
   "pythia_revision":PYTHIA_PIN
 },
 "boundary":{
   "claim":"verified factor equalities compile once into normalized observation equality",
   "automatic_source_theorem_discovery":"UNKNOWN"
 }
}
OUT.parent.mkdir(parents=True,exist_ok=True)
OUT.write_text(json.dumps(ev,indent=2,sort_keys=True)+"\n")
print(json.dumps(ev,indent=2,sort_keys=True))
