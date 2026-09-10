"""Route-neutral ARC administration and bounded developmental discrimination."""
from __future__ import annotations
from collections import Counter
from copy import deepcopy
from dataclasses import asdict
from hashlib import sha256
import argparse, json, resource, subprocess, time
from pathlib import Path
from typing import Any, Mapping

from .residual import ResidualEnvelope
from .runtime import (CapabilityContract, Developer, Evidence, EvidenceStore,
                      IRContract, Obligation, Repair, assessment_claim, digest)

PARENT = "003e6ccfa91205a1f0ea408656c10b8afbdb10c4"
ARC_REPOSITORY = "fchollet/ARC-AGI"
ARC_COMMIT = "399030444e0ab0cc8b4e199870fb20b863846f34"
ARC_PATH = "data/training"
D4 = ("id", "r90", "r180", "r270", "flip-h", "flip-v", "transpose", "anti")
NEW = tuple([f"concat-h:{x}" for x in D4] + [f"concat-v:{x}" for x in D4]
            + [f"overlay:{x}" for x in D4])

def grid(g): return tuple(tuple(int(x) for x in row) for row in g)
def rotate(g): return tuple(zip(*g[::-1]))
def d4(g, name):
    g=grid(g); r1=rotate(g); r2=rotate(r1); r3=rotate(r2)
    return {"id":g,"r90":r1,"r180":r2,"r270":r3,
            "flip-h":tuple(tuple(reversed(r)) for r in g),"flip-v":tuple(reversed(g)),
            "transpose":tuple(zip(*g)),"anti":tuple(zip(*tuple(reversed(g))))[::-1]}[name]
def crop(g):
    g=grid(g); pts=[(i,j) for i,r in enumerate(g) for j,x in enumerate(r) if x]
    if not pts:return g
    a,b=min(i for i,j in pts),max(i for i,j in pts); c,d=min(j for i,j in pts),max(j for i,j in pts)
    return tuple(r[c:d+1] for r in g[a:b+1])
def extend(g, spec):
    kind,name=spec.split(":",1); g=grid(g); other=d4(g,name)
    return form(g,other,kind)
def form(g,other,kind):
    if kind=="concat-h" and len(g)==len(other): return tuple(a+b for a,b in zip(g,other))
    if kind=="concat-v" and len(g[0])==len(other[0]): return g+other
    if kind=="overlay" and (len(g),len(g[0]))==(len(other),len(other[0])):
        return tuple(tuple(max(x,y) for x,y in zip(a,b)) for a,b in zip(g,other))
    return None
def examples(task): return tuple(task["train"])
def all_examples(task): return tuple(task["train"])+tuple(task["test"])
def solves(task, fn):
    try:return all(fn(grid(e["input"]))==grid(e["output"]) for e in examples(task))
    except (KeyError,TypeError,ValueError,IndexError):return False
def matches(task, family):
    if family=="direct": return [x for x in D4 if solves(task,lambda g,x=x:d4(g,x))]
    if family=="role": return [x for x in D4 if solves(task,lambda g,x=x:d4(crop(g),x))]
    return [x for x in NEW if solves(task,lambda g,x=x:extend(g,x))]

def neutral_stratum(task):
    labels=[]
    for e in task.get("train",[]):
        i,o=grid(e["input"]),grid(e["output"]); si=(len(i),len(i[0])); so=(len(o),len(o[0]))
        if so==si and Counter(sum(i,()))==Counter(sum(o,())): label="pixel-permutation"
        elif so!=si and so==(len(crop(i)),len(crop(i)[0])): label="strict-bbox-shape"
        elif so in ((si[0],2*si[1]),(2*si[0],si[1])): label="doubled-axis-shape"
        else:return None
        labels.append(label)
    return labels[0] if labels and len(set(labels))==1 else None

def select_stream(root:Path, nonce:str):
    rows=[]
    for p in sorted((root/ARC_PATH).glob("*.json")):
        raw=p.read_bytes(); task=json.loads(raw); stratum=neutral_stratum(task)
        if stratum:
            public={"train":task["train"],"test":[{"input":e["input"]} for e in task["test"]]}
            rows.append({"task_id":p.stem,"task_sha256":sha256(raw).hexdigest(),
                         "stratum":stratum,"task":public})
    rows.sort(key=lambda x:digest({"nonce":nonce,"task_sha256":x["task_sha256"]}))
    body={"schema":"arc-route-neutral-stream/v1","external_repository":ARC_REPOSITORY,
          "external_commit":ARC_COMMIT,"external_path":ARC_PATH,"selection_nonce":nonce,
          "eligibility":"JSON schema plus three declared input/output shape/color invariants",
          "tasks":rows,"route_labels_present":False}
    return {**body,"stream_digest":digest(body)}

class ARCAdapter:
    name="arc-developmental-discrimination-v1"
    contract=IRContract("ARCTask","GridProgram","Verified|Unknown","finite grid transforms",
                        "all declared examples equal execution","ARCExactGridReplay")
    direct_contract=CapabilityContract("Grid","Grid","D4 whole-grid transform","ARCExactGridReplay")
    role_contract=CapabilityContract("NonzeroBoundingObject","Grid","crop then retained D4 transform","ARCExactGridReplay")
    extension_contract=CapabilityContract("Grid","Grid","new concat/overlay formation rule","ARCExactGridReplay")
    verifier_id="arc-exact-grid-replay-v1:"+digest({"D4":D4,"NEW":NEW,"contract":contract.id})
    def _records(self,state):return state["capabilities"]
    def _exec(self,state,rid,g,active=()):
        if rid in active:return None
        rec=state["capabilities"].get(rid)
        if not rec or rec["evidence"]["verifier"]!=self.verifier_id:return None
        repair=rec["repair"]; body=repair["payload"].get("body",{})
        if body.get("op")=="d4" and repair["contract"]==asdict(self.direct_contract):return d4(g,body["name"])
        parent=body.get("callee")
        if repair["dependencies"]!=[parent]:return None
        if body.get("op")=="crop-call":return self._exec(state,parent,crop(g),(*active,rid))
        if body.get("op")=="extend":
            transformed=self._exec(state,parent,g,(*active,rid))
            return None if transformed is None else form(grid(g),transformed,body["spec"].split(":",1)[0])
        return None
    def _solving_records(self,state,task):
        return [rid for rid in state["capabilities"] if solves(task,lambda g,rid=rid:self._exec(state,rid,g))]
    def _env(self,state,obl,cls,diag,witness,constraint,strength="exact-replay-certified"):
        return ResidualEnvelope(cls,diag,witness,digest({"D4":D4,"role":D4}),
            digest({"budget":obl.budget,"task":obl.target["task_sha256"]}),constraint,
            digest({"role":D4,"new":NEW}),strength,
            {"task_sha256":obl.target["task_sha256"]}).to_mapping()
    def assess(self,state,obligation):
        claim=assessment_claim(state,obligation); target=obligation.target
        if target.get("admin")=="seed":
            name=target["name"]; existing=[r for r,v in self._records(state).items() if v["repair"]["payload"].get("body")=={"op":"d4","name":name}]
            if existing:return Evidence("verified",claim,self.verifier_id,{"capability":existing[0]},scope=self.name)
            w={"missing_seed":name}
            return Evidence("unknown",claim,self.verifier_id,w,{"class":"SEED_REQUIRED","name":name},self.name)
        task=target["task"]
        direct=self._solving_records(state,task)
        if direct:return Evidence("verified",claim,self.verifier_id,{"executed":direct[0],"examples":len(examples(task))},scope=self.name)
        roles=matches(task,"role")
        if roles:
            seeds={v["repair"]["payload"]["body"].get("name"):r for r,v in self._records(state).items() if v["repair"]["payload"].get("body",{}).get("op")=="d4"}
            spec=roles[0]; w={"direct_closure_count":len(D4),"direct_survivors":matches(task,"direct"),"role_survivors":roles}
            if spec not in seeds:
                return Evidence("unknown",claim,self.verifier_id,w,self._env(state,obligation,"REQUIRED_ANCESTOR_INACTIVE","capability_failure",w,{"requires_d4":spec}),self.name)
            constraint={"change":"role-only","callee":seeds[spec],"new_input":"NonzeroBoundingObject"}
            return Evidence("unknown",claim,self.verifier_id,w,self._env(state,obligation,"ROLE_REQUALIFICATION_REQUIRED","capability_failure",w,constraint),self.name)
        new=matches(task,"extension")
        if new:
            w={"old_language_complete":True,"old_program_count":16,"direct_survivors":[],"role_survivors":[]}
            constraint={"change":"language","formation_rule":new[0],"old_language_complete":True}
            return Evidence("unknown",claim,self.verifier_id,w,self._env(state,obligation,"OLD_LANGUAGE_OBSTRUCTION","language_failure",w,constraint,"finite-exhaustive"),self.name)
        w={"direct_checked":8,"role_checked":8,"extension_checked":24,"coverage_complete_only_for_declared_families":True}
        return Evidence("unknown",claim,self.verifier_id,w,self._env(state,obligation,"NO_JUSTIFIED_CHANGE","unknown",w,{"remain":"UNKNOWN"},"bounded-inconclusive"),self.name)
    def propose(self,state,obligation,residual):
        cls=residual.get("class")
        if cls=="SEED_REQUIRED":yield Repair("capability","seed-"+residual["name"],{"body":{"op":"d4","name":residual["name"]}},self.name,contract=self.direct_contract)
        elif cls=="ROLE_REQUALIFICATION_REQUIRED":
            c=residual["necessary_constraint"];yield Repair("capability","crop-role-"+c["callee"],{"body":{"op":"crop-call","callee":c["callee"]}},self.name,(c["callee"],),self.role_contract)
        elif cls=="OLD_LANGUAGE_OBSTRUCTION":
            spec=residual["necessary_constraint"]["formation_rule"]
            seed=next(r for r,v in state["capabilities"].items() if v["repair"]["payload"].get("body")=={"op":"d4","name":spec.split(":",1)[1]})
            yield Repair("capability","extension-"+spec,{"body":{"op":"extend","spec":spec,"callee":seed}},self.name,(seed,),self.extension_contract)
    def verify(self,state,obligation,repair):
        body=repair.payload.get("body",{}); ok=False
        if obligation.target.get("admin")=="seed":ok=(body=={"op":"d4","name":obligation.target["name"]} and repair.contract==self.direct_contract and not repair.dependencies)
        else:
            task=obligation.target["task"]
            if body.get("op")=="crop-call":ok=repair.contract==self.role_contract and solves(task,lambda g:d4(crop(g),state["capabilities"][body["callee"]]["repair"]["payload"]["body"]["name"]))
            elif body.get("op")=="extend":ok=repair.contract==self.extension_contract and solves(task,lambda g:extend(g,body["spec"]))
        return Evidence("verified" if ok else "refuted",repair.id,self.verifier_id,{"accepted":ok,"body":body},scope=self.name)
    def attach(self,state,repair,evidence):
        if evidence.verdict!="verified" or not evidence.certificate.get("accepted"):raise ValueError("unverified ARC capability")
        return {"executable":repair.payload["body"],"semantics":"exact grid replay"}

def freeze_state(path):
    if path.exists():path.unlink()
    store=EvidenceStore(path); adapter=ARCAdapter()
    ids=[]
    for name in D4:
        r=Developer(store,adapter).run(Obligation(adapter.name,{"admin":"seed","name":name},1,"method"))
        if r.verdict!="verified" or len(r.retained)!=1:raise RuntimeError("seed failed")
        ids.extend(r.retained)
    body={"schema":"arc-discrimination-state/v1","seed_ids":ids,"state_id":digest(store.state()),"ledger_digest":digest(store.events()),"D4":list(D4)}
    store.close();return {**body,"digest":digest(body)}

def trace(state,task,adapter):
    ids=adapter._solving_records(state,task)
    if not ids:return {"capability":None,"outputs":[]}
    rid=ids[0]
    return {"capability":rid,"outputs":[adapter._exec(state,rid,grid(e["input"])) for e in task.get("test",[])]}

def develop_stream(stream,state_path):
    if any(k in json.dumps(stream) for k in ('"predicted_route"','"ground_truth_route"')):raise ValueError("route-label leakage")
    store=EvidenceStore(state_path); adapter=ARCAdapter(); out=[]
    for index,row in enumerate(stream["tasks"]):
        before=deepcopy(store.state()); before_events=digest(store.events()); t0=time.perf_counter(); c0=time.process_time()
        obligation=Obligation(adapter.name,row,1,"method"); cold=adapter.assess(before,obligation)
        result=Developer(store,adapter).run(obligation)
        if result.verdict=="verified" and not result.retained:route="REUSE"
        elif result.retained:
            contract=store.state()["capabilities"][result.retained[-1]]["repair"]["contract"]
            route="EXAPTATION" if contract==asdict(adapter.role_contract) else "EXPANSION"
        else:route="UNKNOWN"
        after=deepcopy(store.state()); execution_trace=trace(after,row["task"],adapter)
        restart=EvidenceStore(state_path); restart_result=Developer(restart,adapter).run(Obligation(adapter.name,row,0,"method")); restart_trace=trace(restart.state(),row["task"],adapter);restart.close()
        controls={"restart":restart_result.verdict,"restart_trace":restart_trace,"history_before":before_events,"new_admissions":list(result.retained)}
        if result.retained:
            learned=result.retained[-1]; ablated=deepcopy(after); del ablated["capabilities"][learned]
            controls["exact_removal"]=adapter.assess(ablated,Obligation(adapter.name,row,0,"method")).verdict
            controls["exact_removal_trace"]=trace(ablated,row["task"],adapter)
            controls["restoration"]=adapter.assess(after,Obligation(adapter.name,row,0,"method")).verdict
            controls["restoration_trace"]=trace(after,row["task"],adapter)
            controls["fixed_policy"]=adapter.assess(before,Obligation(adapter.name,row,0,"method")).verdict
            controls["raw_history_without_admission"]=controls["fixed_policy"]
            sham=deepcopy(after); wrong=deepcopy(after)
            dep=after["capabilities"][learned]["repair"]["dependencies"][0]
            controls["original_scope_unchanged"]=(before["capabilities"].get(dep)==after["capabilities"].get(dep))
            alternate=next(x for x in after["capabilities"] if x!=dep and after["capabilities"][x]["repair"]["payload"].get("body",{}).get("op")=="d4")
            sham["capabilities"][learned]["repair"]["payload"]["body"]["callee"]=alternate
            controls["sham"]=adapter.assess(sham,Obligation(adapter.name,row,0,"method")).verdict
            wrong["capabilities"][learned]["repair"]["payload"]["body"]["op"]="wrong-direction"
            controls["wrong_direction"]=adapter.assess(wrong,Obligation(adapter.name,row,0,"method")).verdict
            ancestor=deepcopy(after);del ancestor["capabilities"][dep]
            controls["ancestor_removal"]=adapter.assess(ancestor,Obligation(adapter.name,row,0,"method")).verdict
            controls["ancestor_removal_trace"]=trace(ancestor,row["task"],adapter)
            unrelated=next((x for x in after["capabilities"] if x!=learned and x not in after["capabilities"][learned]["repair"]["dependencies"]),None)
            u=deepcopy(after)
            if unrelated:del u["capabilities"][unrelated]
            controls["unrelated_removal"]=adapter.assess(u,Obligation(adapter.name,row,0,"method")).verdict
            controls["unrelated_removal_trace"]=trace(u,row["task"],adapter)
        out.append({"stream_index":index,"task_id":row["task_id"],"task_sha256":row["task_sha256"],
                    "cold_verdict":cold.verdict,"cold_certificate":cold.certificate,"residual":cold.residual,"predicted_route":route,
                    "warm_verdict":result.verdict,"pre_state":before,"post_state_id":digest(after),
                    "verifier_identity":adapter.verifier_id,"observation_boundary":adapter.contract.observation,
                    "execution_trace":execution_trace,"admitted_records":{x:after["capabilities"][x] for x in result.retained},
                    "controls":controls,"decision_sequence":index,
                    "cost":{"C_construction":len(result.retained),"C_verification":2*len(result.retained)+1,
                            "C_activation":len(result.retained),"C_execution":len(examples(row["task"]))*(len(before["capabilities"])+8+24),
                            "C_memory":len(json.dumps(after,separators=(",",":"))),"C_recovery":1,
                            "C_external_interaction":len(examples(row["task"])),
                            "wall_seconds":time.perf_counter()-t0,"cpu_seconds":time.process_time()-c0,
                            "peak_rss_kb":resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
                            "candidate_evaluations":40,"verifier_calls":2*len(result.retained)+1,
                            "active_state_bytes":len(json.dumps(after,separators=(",",":")))}})
    body={"schema":"arc-development-decisions/v1","stream_digest":stream["stream_digest"],"results":out,"labels_seen":False}
    store.close();return {**body,"decisions_digest":digest(body)}

def evaluate(stream,decisions,initial_state_id=None,external_root=None):
    from .arc_route_oracle import route as oracle
    if decisions["stream_digest"]!=stream["stream_digest"]:raise ValueError("stream mismatch")
    rows=[]; matrix={a:{b:0 for b in ("REUSE","EXAPTATION","EXPANSION","UNKNOWN")} for a in ("REUSE","EXAPTATION","EXPANSION","UNKNOWN")}
    expected_state=initial_state_id
    if len(stream["tasks"])!=len(decisions["results"]):raise ValueError("decision count mismatch")
    external_tasks={}
    if external_root is not None:
        for p in (Path(external_root)/ARC_PATH).glob("*.json"):
            external_tasks[p.stem]=(sha256(p.read_bytes()).hexdigest(),json.loads(p.read_text()))
    for index,(src,dec) in enumerate(zip(stream["tasks"],decisions["results"])):
        if src["task_sha256"]!=dec["task_sha256"]:raise ValueError("task mismatch")
        if dec["decision_sequence"]!=index:raise ValueError("decision chronology mismatch")
        if expected_state is not None and digest(dec["pre_state"])!=expected_state:raise ValueError("state chain mismatch")
        full=src["task"]
        if external_tasks:
            ext_hash,full=external_tasks[src["task_id"]]
            if ext_hash!=src["task_sha256"]:raise ValueError("external task identity mismatch")
        truth=oracle(full,dec["pre_state"]); pred=dec["predicted_route"];matrix[truth][pred]+=1
        expected=[grid(e["output"]) for e in full.get("test",[])]
        observed=[grid(x) for x in dec["execution_trace"]["outputs"]]
        held_out=(observed==expected) if expected else True
        causal=True
        if pred in ("EXAPTATION","EXPANSION"):
            c=dec["controls"]
            causal=(held_out and [grid(x) for x in c["restart_trace"]["outputs"]]==expected
                    and not c["exact_removal_trace"]["outputs"] and not c["ancestor_removal_trace"]["outputs"]
                    and [grid(x) for x in c["restoration_trace"]["outputs"]]==expected
                    and [grid(x) for x in c["unrelated_removal_trace"]["outputs"]]==expected)
        rows.append({"task_id":src["task_id"],"task_sha256":src["task_sha256"],"predicted":pred,"ground_truth":truth,
                     "match":pred==truth,"held_out_verified":held_out,"causal_held_out_verified":causal})
        expected_state=dec["post_state_id"]
    counts={k:sum(matrix[k].values()) for k in matrix}
    passed=(len(rows)>=12 and all(counts[k]>0 for k in counts)
            and all(r["match"] and r["causal_held_out_verified"]
                    and (r["ground_truth"]=="UNKNOWN" or r["held_out_verified"]) for r in rows))
    body={"schema":"arc-discrimination-evaluation/v1","outcome":"DEVELOPMENTAL_DISCRIMINATION_V1_PASS" if passed else "UNKNOWN_EXTERNAL_ROUTE_COVERAGE",
          "task_count":len(rows),"route_counts":counts,"accuracy":sum(r["match"] for r in rows)/len(rows),"confusion_matrix":matrix,"rows":rows,
          "stream_digest":stream["stream_digest"],"decisions_digest":decisions["decisions_digest"],"v4_eligible":passed}
    return {**body,"evidence_digest":digest(body)}

def freeze_manifest(root,external,state,source_commit,nonce):
    if external.exists():raise ValueError("external path present before freeze")
    if subprocess.check_output(["git","rev-parse","HEAD"],cwd=root,text=True).strip()!=source_commit:raise ValueError("wrong source commit")
    subprocess.run(["git","merge-base","--is-ancestor",PARENT,source_commit],cwd=root,check=True)
    frozen=freeze_state(state)
    files={str(p.relative_to(root)):sha256(p.read_bytes()).hexdigest() for p in sorted((root/"open_development").rglob("*.py"))}
    files[".github/workflows/developmental-discrimination-arc-v1.yml"]=sha256((root/".github/workflows/developmental-discrimination-arc-v1.yml").read_bytes()).hexdigest()
    body={"schema":"arc-discrimination-freeze/v1","canonical_parent":PARENT,"source_commit":source_commit,
          "nonce":nonce,"external_absent":True,"files":files,"state":frozen}
    return {**body,"freeze_digest":digest(body)}

def validate_external(root):
    commit=subprocess.check_output(["git","rev-parse","HEAD"],cwd=root,text=True).strip()
    if commit!=ARC_COMMIT:raise ValueError("wrong ARC commit")
    identities={p.stem:sha256(p.read_bytes()).hexdigest() for p in sorted((root/ARC_PATH).glob("*.json"))}
    if len(identities)!=400:raise ValueError("unexpected ARC training corpus size")
    return {"commit":commit,"file_count":len(identities),"corpus_digest":digest(identities),"files":identities}

def main():
    p=argparse.ArgumentParser();p.add_argument("stage",choices=("freeze","admin","develop","evaluate"));p.add_argument("--source-commit",required=True);p.add_argument("--nonce",required=True)
    p.add_argument("--root",type=Path,default=Path.cwd());p.add_argument("--external",type=Path,default=Path("external"));p.add_argument("--state",type=Path,default=Path("arc-state.sqlite"));p.add_argument("--freeze",type=Path,default=Path("arc-freeze.json"));p.add_argument("--stream",type=Path,default=Path("arc-stream.json"));p.add_argument("--decisions",type=Path,default=Path("arc-decisions.json"));p.add_argument("--evaluation",type=Path,default=Path("arc-evaluation.json"));a=p.parse_args()
    if a.stage=="freeze":
        out=freeze_manifest(a.root,a.external,a.state,a.source_commit,a.nonce);a.freeze.write_text(json.dumps(out,indent=2)+"\n");print("ARC_DISCRIMINATION_FREEZE",out["freeze_digest"]);return
    frozen=json.loads(a.freeze.read_text())
    if frozen["source_commit"]!=a.source_commit or frozen["nonce"]!=a.nonce or frozen["canonical_parent"]!=PARENT:raise ValueError("freeze identity mismatch")
    if frozen["freeze_digest"]!=digest({k:v for k,v in frozen.items() if k!="freeze_digest"}):raise ValueError("tampered freeze")
    if a.stage=="admin":
        identity=validate_external(a.external);out=select_stream(a.external,a.nonce);out["corpus_identity"]=identity;out["stream_digest"]=digest({k:v for k,v in out.items() if k!="stream_digest"});a.stream.write_text(json.dumps(out,indent=2)+"\n");print("ARC_ROUTE_NEUTRAL_STREAM",len(out["tasks"]),out["stream_digest"]);return
    stream=json.loads(a.stream.read_text()); expected=digest({k:v for k,v in stream.items() if k!="stream_digest"})
    if stream["stream_digest"]!=expected or stream["selection_nonce"]!=a.nonce:raise ValueError("tampered stream")
    if a.stage=="develop":
        out=develop_stream(stream,a.state);a.decisions.write_text(json.dumps(out,indent=2)+"\n");print("ARC_DEVELOPER_DECISIONS",len(out["results"]),out["decisions_digest"]);return
    identity=validate_external(a.external)
    if identity!=stream.get("corpus_identity"):raise ValueError("evaluator corpus mismatch")
    decisions=json.loads(a.decisions.read_text())
    if decisions.get("decisions_digest")!=digest({k:v for k,v in decisions.items() if k!="decisions_digest"}):raise ValueError("tampered decisions")
    out=evaluate(stream,decisions,frozen["state"]["state_id"],a.external);a.evaluation.write_text(json.dumps(out,indent=2)+"\n");print(out["outcome"],out["route_counts"],out["accuracy"],out["evidence_digest"])

if __name__=="__main__":main()
