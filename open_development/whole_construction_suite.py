"""Integrated source-exact developmental workload qualification.

Runs original MDA proof/finite economics, role requalification, real graph
census, and exhaustive real-ledger revocation, in independent processes.
Does not claim to implement a new global optimizer.
"""
from __future__ import annotations
import json,os,subprocess,sys,time,resource
from pathlib import Path

CASES=(
 ("proof_and_finite_economics","open_development.mda_v7_economics"),
 ("role_requalification_and_ablations","open_development.role_transport_qualification"),
 ("real_capability_dag","open_development.whole_construction_census"),
 ("exact_dependency_reclosure","open_development.whole_construction_reclosure"),
)
def main():
    out={"schema":"metalogic.whole-construction.integrated-real-workload.v1",
         "status":"CANDIDATE_UNTIL_EXACT_CI",
         "tests":[],"global_optimiser":"NOT_IMPLEMENTED",
         "alternative_complete_plans":"NOT_ENUMERATED",
         "cross_domain_dependency":"NOT_ESTABLISHED"}
    for name,module in CASES:
        start=time.perf_counter()
        p=subprocess.run([sys.executable,"-m",module],capture_output=True,text=True,timeout=240)
        elapsed=time.perf_counter()-start
        item={"name":name,"module":module,"returncode":p.returncode,
              "wall_seconds":round(elapsed,4),
              "stdout_sha256":__import__("hashlib").sha256(p.stdout.encode()).hexdigest()}
        if p.returncode:
            item["stderr_tail"]=p.stderr[-3000:]
            out["tests"].append(item)
            print(json.dumps(out,indent=2,sort_keys=True))
            raise RuntimeError(name+" failed: "+p.stderr[-2000:])
        # Extract actual JSON receipts where possible, not invented costs.
        try:
            obj=json.loads(p.stdout)
            item["receipt"]=obj
        except json.JSONDecodeError:
            item["stdout_tail"]=p.stdout[-2000:]
        out["tests"].append(item)
    assert len(out["tests"])==4 and all(x["returncode"]==0 for x in out["tests"])
    out["status"]="PASS_SOURCE_EXACT_INTEGRATED_RUNTIME"
    print(json.dumps(out,indent=2,sort_keys=True))
if __name__=="__main__":main()
