from __future__ import annotations
from pathlib import Path
import hashlib,json,re,sys
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
from worlds import source_world,transfer_world,noninvertible_control,cyclic_world,relabel_world,rows
from constructor import synthesize,execute,library,apply_program,residuals
from verifier import law_audit,element_orders

OUT=HERE/"results"; OUT.mkdir(exist_ok=True)

BANNED=["group","quotient","equivalence","inverse","identity","monoid","dihedral","symmetric","d4","s3","cayley",
        "tuple-key","tuple key","behavioral-equivalence","behavioral equivalence"]

def leak_audit():
    txt=(HERE/"constructor.py").read_text().lower()
    hits={w:len(re.findall(r"\b"+re.escape(w)+r"\b",txt)) for w in BANNED}
    return {k:v for k,v in hits.items() if v}

def split(world):
    train=rows(world,0,9); test=rows(world,10,13)
    return train,test

def baseline(train,test):
    mem={w:o for w,o in train}
    c=sum(mem.get(w)==o for w,o in test)
    return c/len(test)

def eval_model(model,test):
    c=0; u=0
    for w,o in test:
        s=execute(model,w)
        if s is None:u+=1
        elif tuple(model["behaviors"][s])==tuple(o):c+=1
    return {"correct":c,"total":len(test),"accuracy":c/len(test),"unknown":u}

def ablate_program(world,train,model):
    tokens=tuple(world.generators)
    lookup={w:o for w,o in train}
    results=[]
    prog=model["program"]
    from constructor import Op
    for i in range(len(prog)):
        p=[Op(x["kind"],x["arg"]) for j,x in enumerate(prog) if j!=i]
        part,_=apply_program(train,tokens,p)
        pc,tc=residuals(part,tokens,lookup)
        results.append({"removed_index":i,"removed":prog[i],"predictive_conflicts":pc,
                        "transition_conflicts":tc,"causal_damage":pc+tc>0})
    return results

def forbid_observation_splits(world,train,max_len=4):
    # Re-run the same synthesis space with all split_probe primitives removed.
    from constructor import library,Op,apply_program,residuals
    from itertools import product
    tokens=tuple(world.generators); lookup={w:o for w,o in train}
    lib=[x for x in library(tokens,world.n) if x.kind!="split_probe"]
    best=None; exact=False; searched=0
    for L in range(max_len+1):
        for prog in product(lib,repeat=L):
            searched+=1
            part,_=apply_program(train,tokens,prog)
            pc,tc=residuals(part,tokens,lookup)
            score=(pc+tc,len(part),L)
            if best is None or score<best[0]:
                best=(score,[(x.kind,x.arg) for x in prog],pc,tc)
            if pc==0 and tc==0:
                exact=True
                return {"exact_found":True,"searched":searched,"best":best}
    return {"exact_found":False,"searched":searched,"best":best}

def run(world, causal=False):
    train,test=split(world)
    model=synthesize(train,tuple(world.generators),world.n,max_len=4)
    held=eval_model(model,test)
    audit=law_audit(model)
    return {
        "tag":world.tag,"train_n":len(train),"test_n":len(test),
        "syntax_baseline":baseline(train,test),
        "program":model["program"],"trajectory":model["trajectory"],
        "search_history":model["search_history"],"programs_searched":model["programs_searched"],
        "states":model["state_count"],"heldout":held,
        "law_audit":{k:v for k,v in audit.items() if k!="table"},
        "element_orders":element_orders(audit),
        "program_ablation":ablate_program(world,train,model) if causal else [],
        "observation_family_ablation":forbid_observation_splits(world,train) if causal else {"exact_found":None},
        "compression":(len(train)+len(test))/model["state_count"],
    }

def main():
    source=run(source_world(), causal=True)
    transfer=run(transfer_world())
    control=run(noninvertible_control())
    cycles=[run(cyclic_world(k)) for k in (3,5,7)]
    relabel=[run(relabel_world(source_world(),s)) for s in (17,29,43,71)]
    leaks=leak_audit()
    gates={
      "G0_no_target_or_direct_key_vocabulary":not leaks,
      "G1_source_memory_zero":source["syntax_baseline"]==0,
      "G2_source_program_synthesized":len(source["program"])>0,
      "G3_source_heldout_perfect":source["heldout"]["accuracy"]==1,
      "G4_source_program_causal":all(x["causal_damage"] for x in source["program_ablation"]),
      "G5_source_observation_family_needed":not source["observation_family_ablation"]["exact_found"],
      "G6_source_posthoc_group_bundle":source["law_audit"]["group_axiom_bundle"],
      "G7_transfer_perfect_and_group":transfer["heldout"]["accuracy"]==1 and transfer["law_audit"]["group_axiom_bundle"],
      "G8_negative_control_perfect_but_not_group":control["heldout"]["accuracy"]==1 and not control["law_audit"]["group_axiom_bundle"],
      "G9_order_transfer":all(x["heldout"]["accuracy"]==1 and x["law_audit"]["group_axiom_bundle"] for x in cycles),
      "G10_relabeling":all(x["heldout"]["accuracy"]==1 and x["states"]==source["states"] for x in relabel),
      "G11_compression":min([source["compression"],transfer["compression"],control["compression"]]+[x["compression"] for x in cycles])>10,
    }
    R={"experiment":"KOROVIN_REPRESENTATION_PROGRAM_INVENTION_V3",
       "claim_boundary":"The controller synthesizes a representation-building program from generic partition operations; it is not given a direct feature-key state constructor or algebraic laws. The DSL still contains generic split/refine/merge primitives, so this is constrained abstraction-program synthesis, not ex nihilo invention of mathematical ontology.",
       "leaks":leaks,"gates":gates,"all_gates_pass":all(gates.values()),
       "source":source,"transfer":transfer,"negative_control":control,
       "cycle_transfer":cycles,"relabel_controls":relabel}
    raw=json.dumps(R,sort_keys=True,separators=(",",":")).encode()
    R["sha256"]=hashlib.sha256(raw).hexdigest()
    (OUT/"RESULT.json").write_text(json.dumps(R,indent=2,sort_keys=True))
    print(json.dumps({
      "all_gates_pass":R["all_gates_pass"],"gates":gates,
      "source":{"program":source["program"],"trajectory":source["trajectory"],"states":source["states"],
                "heldout":source["heldout"],"laws":source["law_audit"],
                "searched":source["programs_searched"]},
      "transfer":{"program":transfer["program"],"states":transfer["states"],"heldout":transfer["heldout"]},
      "negative":{"program":control["program"],"states":control["states"],"heldout":control["heldout"],"laws":control["law_audit"]},
      "sha256":R["sha256"]
    },indent=2))
    if not R["all_gates_pass"]: raise SystemExit(1)
if __name__=="__main__": main()
