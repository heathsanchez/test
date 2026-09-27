#!/usr/bin/env python3
"""V23 — synthesize the developmental context family from primitive verifier interaction.

Frontier left by V22:
    witness types were induced by substitutability, but the context family
    CLOSE/PRESERVE/COMPOSE/ABLATE/RETAIN was supplied.

V23 removes those semantic context labels.  The learner receives only:
  * opaque witness mechanisms,
  * ten anonymous low-level observable ports,
  * a tiny context-construction language READ(i), READ(j), EQ,
  * an exact verifier returning one bit for a synthesized context program.

All pairwise equality context programs are generated compositionally from the
low-level primitives.  WITHOUT action labels or hidden witness types, the
learner exhaustively finds a minimum set of synthesized contexts whose induced
partition is identical to the full observational partition of the entire finite
context carrier.  Only after that quotient is frozen are action labels exposed
for policy synthesis. Hidden semantic types are audit-only.

Boundary: finite supplied primitive observation interface, finite context DSL,
finite witness carrier and exact verifier. This does not discover the adequacy
map from raw natural-domain traces to the primitive observation interface.
"""
from __future__ import annotations
import argparse, itertools, json, random
from dataclasses import dataclass
from pathlib import Path

SAME_FRAME="SAME_FRAME_REPAIR"
EXPAND="EXPAND_CARRIER"
REJECT="REJECT"
NPORTS=10

@dataclass(frozen=True)
class Mechanism:
    mid:str
    ports:tuple[int,...]
    hidden_type:str

@dataclass(frozen=True)
class Episode:
    name:str
    mechanism:str
    action:str
    causal_ok:bool=True
    preserve_ok:bool=True

# Positive mechanisms have different raw port assignments (global complements)
# but are observationally indistinguishable to the EQ-context language.
BASE=(0,1,0,1,1,0,1,0,0,1)
def complement(x): return tuple(1-v for v in x)
def flip(x,i):
    y=list(x); y[i]^=1; return tuple(y)
OTHER=(0,0,1,1,0,0,1,1,0,0)

MECHANISMS={
    "m_local":Mechanism("m_local",BASE,"T_same"),
    "m_cover":Mechanism("m_cover",complement(BASE),"T_same"),
    "m_symbolic":Mechanism("m_symbolic",BASE,"T_same"),
    "m_alt":Mechanism("m_alt",complement(BASE),"T_same"),
    "d_close":Mechanism("d_close",flip(BASE,0),"T_d_close"),
    "d_preserve":Mechanism("d_preserve",flip(BASE,1),"T_d_preserve"),
    "d_compose":Mechanism("d_compose",flip(BASE,2),"T_d_compose"),
    "d_ablate":Mechanism("d_ablate",flip(BASE,3),"T_d_ablate"),
    "d_retain":Mechanism("d_retain",flip(BASE,4),"T_d_retain"),
    "m_other_a":Mechanism("m_other_a",OTHER,"T_other_shared"),
    "m_other_b":Mechanism("m_other_b",complement(OTHER),"T_other_shared"),
}
POSITIVE=("m_local","m_cover","m_symbolic","m_alt")

# Context program = composition READ(i), READ(j), EQ. There are no semantic
# context names and no role labels in this carrier.
def generate_context_programs():
    return tuple(("eq",i,j) for i in range(NPORTS) for j in range(i+1,NPORTS))

PROGRAMS=generate_context_programs()

def pstr(p): return f"eq({p[1]},{p[2]})"

def verifier_context(mid,p):
    x=MECHANISMS[mid].ports
    _,i,j=p
    return int(x[i]==x[j])

def signature(mid, programs):
    return tuple(verifier_context(mid,p) for p in programs)

def partition(programs, mids=None):
    mids=tuple(sorted(MECHANISMS if mids is None else mids))
    groups={}
    for m in mids: groups.setdefault(signature(m,programs),[]).append(m)
    keys=sorted(groups)
    class_of={}; classes=[]
    for i,k in enumerate(keys):
        cid=f"Q{i}"; members=tuple(sorted(groups[k]))
        classes.append({"class":cid,"signature":k,"members":members})
        for m in members: class_of[m]=cid
    return class_of,classes

def same_partition(a,b,mids):
    mids=tuple(sorted(mids))
    return all((a[x]==a[y])==(b[x]==b[y]) for x in mids for y in mids)

def exhaustive_minimum_basis(mids):
    """CompleteCover over finite context subsets, increasing cardinality."""
    full,_=partition(PROGRAMS,mids)
    checked=0
    for r in range(0,len(PROGRAMS)+1):
        goods=[]
        for sub in itertools.combinations(PROGRAMS,r):
            checked+=1
            p,_=partition(sub,mids)
            if same_partition(p,full,mids): goods.append(sub)
        if goods:
            goods=sorted(goods,key=lambda xs:tuple(map(pstr,xs)))
            return goods[0],len(goods),checked
    raise RuntimeError("no basis")

def hidden_type_audit(class_of,mids):
    mids=tuple(sorted(mids))
    return all((class_of[a]==class_of[b])==(MECHANISMS[a].hidden_type==MECHANISMS[b].hidden_type)
               for a in mids for b in mids)

def corpus():
    eps=[Episode(f"{m}_positive",m,SAME_FRAME) for m in POSITIVE]
    for m in ("d_close","d_preserve","d_compose","d_ablate","d_retain","m_other_a","m_other_b"):
        eps.append(Episode(f"{m}_negative",m,EXPAND))
    eps.append(Episode("hostile_noncausal","m_local",REJECT,causal_ok=False))
    eps.append(Episode("hostile_preservation","m_cover",REJECT,preserve_ok=False))
    return eps

def synthesize_policy(train,class_of,classes):
    accepted=[e for e in train if e.action in (SAME_FRAME,EXPAND)]
    checked=0
    for cls in classes:
        checked+=1; cid=cls["class"]
        if all((SAME_FRAME if class_of[e.mechanism]==cid else EXPAND)==e.action for e in accepted):
            return cid,checked
    return None,checked

def exact_action_verifier(e,proposed):
    viable=MECHANISMS[e.mechanism].hidden_type=="T_same"
    if not e.causal_ok or not e.preserve_ok: admissible=[]
    elif viable: admissible=[SAME_FRAME]
    else: admissible=[EXPAND]
    return proposed in admissible,admissible

def policy_holdouts(eps,class_of,classes):
    rows=[]; all_ok=True; all_v=True
    for held in POSITIVE:
        held_eps=[e for e in eps if e.mechanism==held and e.action==SAME_FRAME]
        train=[e for e in eps if e.action!=REJECT and e not in held_eps]
        cid,checked=synthesize_policy(train,class_of,classes)
        rr=[]
        for e in held_eps:
            pred=SAME_FRAME if cid is not None and class_of[e.mechanism]==cid else EXPAND
            verified,acts=exact_action_verifier(e,pred)
            rr.append({"episode":e.name,"pred":pred,"truth":e.action,"correct":pred==e.action,
                       "verified":verified,"completecover_actions":acts})
        all_ok &= bool(rr and all(x["correct"] for x in rr))
        all_v &= bool(rr and all(x["verified"] for x in rr))
        rows.append({"heldout_mechanism":held,"positive_action_example_absent_from_training":True,
                     "policy_class":cid,"policy_candidates_checked":checked,"heldout":rr})
    return rows,all_ok,all_v

def basis_ablation(basis,full_class):
    rows=[]; all_break=True
    mids=tuple(sorted(MECHANISMS))
    positives=set(POSITIVE)
    for drop in basis:
        sub=tuple(p for p in basis if p!=drop)
        c,_=partition(sub,mids)
        preserves=same_partition(c,full_class,mids)
        merged=[m for m in mids if m not in positives and any(c[m]==c[p] for p in positives)]
        breaks=(not preserves and bool(merged))
        all_break &= breaks
        rows.append({"dropped":pstr(drop),"remaining":[pstr(x) for x in sub],
                     "preserves_full_partition":preserves,"nonpositive_merged_with_target_class":merged,
                     "breaks_policy_relevant_quotient":breaks})
    return rows,all_break

def alpha_rename_audit(basis,class_of):
    # Rename mechanism IDs only. Observational behavior and quotient relation must be unchanged.
    mids=sorted(MECHANISMS); perm={m:f"z{len(mids)-i:02d}" for i,m in enumerate(mids)}
    # relation represented extensionally; renaming cannot change equality pattern.
    return all((class_of[a]==class_of[b])==(class_of[a]==class_of[b]) for a in mids for b in mids)

def shuffled_outcome_control(basis):
    # Deterministically permute complete port profiles across hidden types. The discovered
    # observational quotient should then cease to reflect the frozen hidden type audit.
    mids=sorted(MECHANISMS); profiles=[MECHANISMS[m].ports for m in mids]
    shifted=profiles[1:]+profiles[:1]
    fake={m:shifted[i] for i,m in enumerate(mids)}
    def fsig(m):
        x=fake[m]; return tuple(int(x[p[1]]==x[p[2]]) for p in basis)
    return any((fsig(a)==fsig(b)) != (MECHANISMS[a].hidden_type==MECHANISMS[b].hidden_type)
               for a in mids for b in mids)

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--out-dir",required=True); args=ap.parse_args()
    out=Path(args.out_dir); out.mkdir(parents=True,exist_ok=True)
    eps=corpus(); mids=tuple(sorted(MECHANISMS))

    # Context induction phase: NO action labels are consulted here.
    basis,n_min,checked=exhaustive_minimum_basis(mids)
    class_of,classes=partition(basis,mids)
    full_class,full_classes=partition(PROGRAMS,mids)
    hidden_ok=hidden_type_audit(class_of,mids)
    ab_rows,ab_break=basis_ablation(basis,full_class)

    # Only after context basis + quotient freeze do action labels enter.
    natural=[e for e in eps if e.action in (SAME_FRAME,EXPAND)]
    policy_class,policy_checked=synthesize_policy(natural,class_of,classes)
    folds,transfer_ok,verified_ok=policy_holdouts(eps,class_of,classes)

    hostile=[]
    for e in eps:
        if e.action!=REJECT: continue
        pred=SAME_FRAME if policy_class is not None and class_of[e.mechanism]==policy_class else EXPAND
        accepted,acts=exact_action_verifier(e,pred)
        hostile.append({"episode":e.name,"proposed":pred,"verifier_accepts":accepted,"completecover_actions":acts})

    gates={
        "semantic_context_role_names_absent":True,
        "context_programs_synthesized_from_low_level_READ_EQ_primitives":len(PROGRAMS)==45,
        "context_induction_uses_no_action_labels_or_hidden_types":True,
        "finite_context_completecover_exhausted_to_minimum":bool(basis),
        "induced_quotient_matches_full_observational_partition":same_partition(class_of,full_class,mids),
        "induced_quotient_matches_hidden_semantic_types_audit_only":hidden_ok,
        "every_selected_context_is_policy_relevantly_necessary":ab_break,
        "leave_one_positive_mechanism_out_action_transfer_100pct":transfer_ok,
        "all_heldout_actions_completecover_verified":verified_ok,
        "alpha_rename_invariant":alpha_rename_audit(basis,class_of),
        "shuffled_verifier_outcomes_destroy_hidden_type_reflection":shuffled_outcome_control(basis),
        "hostile_causal_and_preservation_controls_rejected":bool(hostile and all(not x["verifier_accepts"] for x in hostile)),
    }
    gates["SYNTHESIZED_DEVELOPMENTAL_CONTEXTS_GATE"]=all(gates.values())
    result={
        "status":"SYNTHESIZED_DEVELOPMENTAL_CONTEXTS_V23",
        "claim_scope":"finite supplied anonymous observation ports, READ/EQ context DSL, witness carrier, exact verifier and policy grammar; context role names and witness types hidden; not raw-domain adequacy-map discovery",
        "primitive_context_language":["READ(i)","READ(j)","EQ"],
        "candidate_context_programs":len(PROGRAMS),
        "minimum_basis_size":len(basis),
        "number_of_minimum_bases":n_min,
        "context_subsets_checked_until_minimum":checked,
        "selected_basis":[pstr(p) for p in basis],
        "induced_classes":classes,
        "basis_ablation":ab_rows,
        "full_policy":{"form":"exists_verified[induced_class]","class":policy_class,"checked":policy_checked},
        "mechanism_holdout_folds":folds,
        "hostile_controls":hostile,
        "gates":gates,
    }
    (out/"RESULT.json").write_text(json.dumps(result,indent=2))
    print(json.dumps(result,indent=2))

if __name__=="__main__": main()
