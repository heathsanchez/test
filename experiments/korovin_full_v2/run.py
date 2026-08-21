from __future__ import annotations
from pathlib import Path
import hashlib, json, re, sys

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
from worlds import source_world, transfer_world, noninvertible_control, cyclic_world, relabel_world, rows
from constructor import search_representation, execute_state_machine
from verifier import law_audit, element_orders

OUT=HERE/"results"
OUT.mkdir(exist_ok=True)
SEED=20260822

BANNED = [
    "group","quotient","equivalence","inverse","identity","monoid",
    "dihedral","symmetric","d4","s3","cayley"
]

def blind_source_audit():
    txt=(HERE/"constructor.py").read_text().lower()
    hits={w:len(re.findall(r"\b"+re.escape(w)+r"\b",txt)) for w in BANNED}
    hits={k:v for k,v in hits.items() if v}
    return {"pass":not hits,"hits":hits}

def syntax_baseline(train,test):
    mem={w:o for w,o in train}
    correct=sum(mem.get(w)==o for w,o in test)
    return {"correct":correct,"total":len(test),"accuracy":correct/len(test)}

def train_test(world):
    train=rows(world,0,9)
    test=rows(world,10,13)
    return train,test

def evaluate(world, model, test):
    good=0; unknown=0
    for w,truth in test:
        s=execute_state_machine(model,w)
        if s is None:
            unknown+=1; continue
        good += tuple(model["behaviors"][s])==tuple(truth)
    return {"correct":good,"total":len(test),"accuracy":good/len(test),"unknown":unknown}

def selected_probe_ablation(world,train,test,model):
    selected=model["selected_features"]
    out=[]
    for i,f in enumerate(selected):
        if f["kind"]!="probe": continue
        kept=selected[:i]+selected[i+1:]
        from constructor import Feature, _evaluate_candidate
        feats=tuple(Feature(x["kind"],x["arg"]) for x in kept)
        cand=_evaluate_candidate(train,tuple(world.generators),feats)
        out.append({
            "removed":f,
            "predictive_conflicts":cand.predictive_conflicts,
            "transition_conflicts":cand.transition_conflicts,
            "state_count":cand.state_count,
            "causal_damage":cand.predictive_conflicts+cand.transition_conflicts>0,
        })
    return out

def family_ablation(world,train):
    from constructor import _feature_library, _evaluate_candidate
    from itertools import combinations
    lib=[f for f in _feature_library(train,tuple(world.generators),world.n) if f.kind!="probe"]
    history=[]
    best_exact=None
    for width in range(1,5):
        level=[_evaluate_candidate(train,tuple(world.generators),c) for c in combinations(lib,width)]
        level.sort(key=lambda c:c.score)
        best=level[0]
        history.append({"width":width,"best_score":best.score,
                        "best_features":[(x.kind,x.arg) for x in best.features]})
        exact=[c for c in level if c.predictive_conflicts==0 and c.transition_conflicts==0]
        if exact:
            exact.sort(key=lambda c:c.score); best_exact=exact[0]; break
    return {
        "exact_found_without_probe_features":best_exact is not None,
        "best_exact_state_count":best_exact.state_count if best_exact else None,
        "history":history,
    }

def run_one(world):
    train,test=train_test(world)
    base=syntax_baseline(train,test)
    model=search_representation(train,tuple(world.generators),world.n,max_width=4)
    pred=evaluate(world,model,test)
    audit=law_audit(model)
    orders=element_orders(audit)
    abl=selected_probe_ablation(world,train,test,model)
    fam=family_ablation(world,train)
    return {
        "tag":world.tag,
        "n":world.n,
        "tokens":sorted(world.generators),
        "train_n":len(train),"test_n":len(test),
        "baseline":base,
        "selected_features":model["selected_features"],
        "search_history":model["search_history"],
        "state_count":model["state_count"],
        "heldout":pred,
        "law_audit":{k:v for k,v in audit.items() if k!="table"},
        "element_orders":orders,
        "selected_probe_ablation":abl,
        "feature_family_ablation":fam,
        "compression":(len(train)+len(test))/model["state_count"],
    }

def main():
    source=run_one(source_world())
    transfer=run_one(transfer_world())
    control=run_one(noninvertible_control())
    cycles=[run_one(cyclic_world(k)) for k in (3,5,7)]
    relabeled=[run_one(relabel_world(source_world(),s)) for s in (17,29,43,71)]

    leak=blind_source_audit()
    gates={
        "G0_constructor_target_vocabulary_absent":leak["pass"],
        "G1_source_syntax_baseline_zero":source["baseline"]["accuracy"]==0,
        "G2_source_heldout_perfect":source["heldout"]["accuracy"]==1,
        "G3_source_representation_causal":bool(source["selected_probe_ablation"]) and all(x["causal_damage"] for x in source["selected_probe_ablation"]),
        "G4_source_behavior_family_needed":not source["feature_family_ablation"]["exact_found_without_probe_features"],
        "G5_source_posthoc_group_laws":source["law_audit"]["group_axiom_bundle"],
        "G6_transfer_heldout_perfect":transfer["heldout"]["accuracy"]==1,
        "G7_transfer_posthoc_group_laws":transfer["law_audit"]["group_axiom_bundle"],
        "G8_negative_control_rejects_group_bundle":control["heldout"]["accuracy"]==1 and not control["law_audit"]["group_axiom_bundle"],
        "G9_multiple_orders_transfer":all(x["heldout"]["accuracy"]==1 and x["law_audit"]["group_axiom_bundle"] for x in cycles),
        "G10_relabeling_robustness":all(x["heldout"]["accuracy"]==1 and x["state_count"]==source["state_count"] for x in relabeled),
        "G11_nontrivial_compression":min([source["compression"],transfer["compression"],control["compression"]]+[x["compression"] for x in cycles])>10,
    }
    result={
        "experiment":"KOROVIN_OBJECT_REINVENTION_FULL_V2",
        "seed":SEED,
        "claim_boundary":"The blind constructor is not given algebraic object names/axioms or a preselected behavioral-key representation. It searches a generic feature DSL under predictive/compositional residuals. Post-hoc law recognition is isolated in verifier.py. This is evidence for constrained re-invention of familiar finite algebraic structure, not historically novel mathematics.",
        "blind_source_audit":leak,
        "gates":gates,
        "all_gates_pass":all(gates.values()),
        "source":source,
        "transfer":transfer,
        "negative_control":control,
        "cycle_transfer":cycles,
        "relabeling_controls":relabeled,
    }
    canonical=json.dumps(result,sort_keys=True,separators=(",",":")).encode()
    result["result_sha256"]=hashlib.sha256(canonical).hexdigest()
    (OUT/"RESULT.json").write_text(json.dumps(result,indent=2,sort_keys=True))
    print(json.dumps({
        "all_gates_pass":result["all_gates_pass"],
        "gates":gates,
        "source":{"selected":source["selected_features"],"states":source["state_count"],"heldout":source["heldout"],"laws":source["law_audit"],"compression":source["compression"]},
        "transfer":{"selected":transfer["selected_features"],"states":transfer["state_count"],"heldout":transfer["heldout"],"laws":transfer["law_audit"],"compression":transfer["compression"]},
        "negative":{"selected":control["selected_features"],"states":control["state_count"],"heldout":control["heldout"],"laws":control["law_audit"]},
        "sha256":result["result_sha256"],
    },indent=2))
    if not result["all_gates_pass"]:
        raise SystemExit(1)

if __name__=="__main__":
    main()
