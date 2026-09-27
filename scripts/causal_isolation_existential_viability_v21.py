#!/usr/bin/env python3
"""V21 — causal isolation of the existential viability object.

Residual frozen from V20:
    EXISTENTIAL_OBJECT_NOT_CAUSALLY_ISOLATED_FROM_COVER_SUMMARY

Question:
    Is typed inhabitation of the same-frame viability fibre genuinely necessary
    for unseen-mechanism transfer once every non-typed summary surrogate is
    adversarially matched?

Design
------
Each positive episode is paired with a negative episode having identical:
  * opaque witness-presence pattern,
  * coarse cover summary,
  * causal summary,
  * preservation summary,
  * retention summary,
  * nuisance bits.
The pair differs only in the hidden codomain of the present verified witness:
Theta_same versus Theta_other. Thus, after type erasure, the pair is
observationally identical to the policy learner.

The typed learner can quantify over verified witnesses by codomain and search a
finite compositional grammar. The decisive folds remove every positive training
example of one mechanism while retaining its matched negative twin. Therefore a
name-sensitive rule cannot lawfully generalize to the held-out positive.

An exact evaluator, independent of the policy features, computes the admissible
action from the hidden finite witness carrier (CompleteCover over all witnesses).

Boundary: finite manually constructed witness carrier and type system, supplied
policy grammar, exact finite verifier. This does not establish discovery of the
adequacy map or type system itself.
"""
from __future__ import annotations
import argparse, itertools, json
from dataclasses import dataclass
from pathlib import Path

SAME="Theta_same"; OTHER="Theta_other"
SAME_FRAME="SAME_FRAME_REPAIR"; EXPAND="EXPAND_CARRIER"; REJECT="REJECT"
MECHS=("m_local","m_cover","m_symbolic","m_alt")

@dataclass(frozen=True)
class Witness:
    wid:str; codomain:str; present:bool; verified:bool

@dataclass(frozen=True)
class Episode:
    name:str
    witnesses:tuple[Witness,...]
    cover_summary:int
    causal_summary:int
    preserve_summary:int
    retention_summary:int
    nuisance:tuple[int,...]
    verifier_causal_ok:bool=True
    verifier_preserve_ok:bool=True
    action:str=EXPAND


def make_pair(mech:str, idx:int):
    # Identical non-typed observation vector and identical named-presence vector.
    summary=(idx%2, (idx//2)%2, (idx+1)%2, idx%3)
    nuisance=(idx%2,(idx+1)%2,(idx//2)%2)
    def mk(codomain, suffix, action):
        ws=[]
        for m in MECHS:
            present=(m==mech)
            ws.append(Witness(m, codomain if present else OTHER, present, present))
        # irrelevant witness is matched in both members of the pair
        ws.append(Witness("m_irrelevant",OTHER,True,True))
        return Episode(f"{mech}_{suffix}",tuple(ws),summary[0],summary[1],summary[2],summary[3],nuisance,True,True,action)
    return mk(SAME,"positive",SAME_FRAME), mk(OTHER,"matched_negative",EXPAND)


def corpus():
    eps=[]
    for i,m in enumerate(MECHS): eps.extend(make_pair(m,i))
    # Replicate each mechanism under different nuisance/summary marginals while preserving matched pairs.
    for j,m in enumerate(MECHS, start=4): eps.extend(make_pair(m,j))
    # Hostile verifier controls: typed witness exists but causal/preservation obligations fail.
    p,_=make_pair("m_local",8)
    eps.append(Episode("hostile_noncausal",p.witnesses,p.cover_summary,p.causal_summary,p.preserve_summary,p.retention_summary,p.nuisance,False,True,REJECT))
    p,_=make_pair("m_cover",9)
    eps.append(Episode("hostile_preservation",p.witnesses,p.cover_summary,p.causal_summary,p.preserve_summary,p.retention_summary,p.nuisance,True,False,REJECT))
    return eps

# DSL: typed existential, named witness atoms, non-typed summaries, Boolean composition.
def eval_pred(p,e:Episode,typed=True):
    op=p[0]
    if op=="exists_type":
        if not typed: return False
        return any(w.present and w.verified and w.codomain==p[1] for w in e.witnesses)
    if op=="named":
        return any(w.wid==p[1] and w.present and w.verified for w in e.witnesses)
    if op=="summary": return bool(getattr(e,p[1]))
    if op=="nuisance": return bool(e.nuisance[p[1]])
    if op=="not": return not eval_pred(p[1],e,typed)
    if op=="and": return eval_pred(p[1],e,typed) and eval_pred(p[2],e,typed)
    if op=="or": return eval_pred(p[1],e,typed) or eval_pred(p[2],e,typed)
    raise ValueError(p)

def pstr(p):
    op=p[0]
    if op=="exists_type": return f"exists_verified[{p[1]}]"
    if op=="named": return f"verified({p[1]})"
    if op=="summary": return p[1]
    if op=="nuisance": return f"nuisance_{p[1]}"
    if op=="not": return f"!({pstr(p[1])})"
    return f"{op}({pstr(p[1])},{pstr(p[2])})"

def psize(p):
    if p[0] in ("exists_type","named","summary","nuisance"): return 1
    if p[0]=="not": return 1+psize(p[1])
    return 1+psize(p[1])+psize(p[2])

def generate(max_size=5, typed=True):
    base=[]
    if typed: base += [("exists_type",SAME),("exists_type",OTHER)]
    base += [("named",m) for m in MECHS]
    base += [("summary",x) for x in ("cover_summary","causal_summary","preserve_summary","retention_summary")]
    base += [("nuisance",i) for i in range(3)]
    by={1:base}; seen={repr(x) for x in base}; out=list(base)
    for sz in range(2,max_size+1):
        cur=[]
        for q in by.get(sz-1,[]):
            r=("not",q)
            if repr(r) not in seen: seen.add(repr(r)); cur.append(r)
        for a_sz in range(1,sz-1):
            b_sz=sz-1-a_sz
            for a in by.get(a_sz,[]):
                for b in by.get(b_sz,[]):
                    if repr(a)>repr(b): continue
                    for op in ("and","or"):
                        r=(op,a,b)
                        if repr(r) not in seen: seen.add(repr(r)); cur.append(r)
        by[sz]=cur; out.extend(cur)
    return sorted(out,key=lambda p:(psize(p),pstr(p)))

def action(pred,e,typed=True): return SAME_FRAME if eval_pred(pred,e,typed) else EXPAND

def admissible_actions(e:Episode):
    if not e.verifier_causal_ok or not e.verifier_preserve_ok: return []
    same=any(w.present and w.verified and w.codomain==SAME for w in e.witnesses)
    return [SAME_FRAME] if same else [EXPAND]

def exact_verify(e,proposed):
    acts=admissible_actions(e); return proposed in acts, acts

def accepted(e): return e.action in (SAME_FRAME,EXPAND)

def fits(pred,train,typed=True):
    return all(action(pred,e,typed)==e.action for e in train if accepted(e))

def alpha_episode(e,perm):
    ws=tuple(reversed([Witness(perm.get(w.wid,w.wid),w.codomain,w.present,w.verified) for w in e.witnesses]))
    return Episode(e.name+"__alpha",ws,e.cover_summary,e.causal_summary,e.preserve_summary,e.retention_summary,e.nuisance,e.verifier_causal_ok,e.verifier_preserve_ok,e.action)

def invariant(pred,eps,typed=True):
    perms=[dict(zip(MECHS,MECHS[1:]+MECHS[:1])), dict(zip(MECHS,reversed(MECHS)))]
    for e in eps:
        v=eval_pred(pred,e,typed)
        for pm in perms:
            if eval_pred(pred,alpha_episode(e,pm),typed)!=v: return False
    return True

def synthesize(train,preds,typed=True):
    checked=0
    for p in preds:
        checked+=1
        if fits(p,train,typed) and invariant(p,train,typed): return p,checked
    return None,checked

def folds(eps):
    for mech in MECHS:
        held=[e for e in eps if e.name.startswith(mech+"_") and e.name.endswith("positive")]
        # all positive examples from this mechanism are absent; matched negatives remain.
        train=[e for e in eps if accepted(e) and e not in held]
        yield mech,train,held

def pair_balance(eps):
    rows=[]; ok=True
    for i in range(0,16,2):
        a,b=eps[i],eps[i+1]
        named_a=tuple((w.wid,w.present) for w in a.witnesses)
        named_b=tuple((w.wid,w.present) for w in b.witnesses)
        sa=(a.cover_summary,a.causal_summary,a.preserve_summary,a.retention_summary,a.nuisance,named_a)
        sb=(b.cover_summary,b.causal_summary,b.preserve_summary,b.retention_summary,b.nuisance,named_b)
        same=sa==sb; ok &= same
        rows.append({"positive":a.name,"negative":b.name,"all_non_typed_observables_identical":same})
    return ok,rows

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--out-dir',required=True); args=ap.parse_args()
    out=Path(args.out_dir); out.mkdir(parents=True,exist_ok=True)
    eps=corpus(); typed_preds=generate(5,True); untyped_preds=generate(5,False)
    balanced,balance_rows=pair_balance(eps)
    fold_rows=[]; typed_ok=True; verified_ok=True; intension_ok=True; untyped_collapse=True; alpha_ok=True
    for mech,train,held in folds(eps):
        tp,tc=synthesize(train,typed_preds,True)
        up,uc=synthesize(train,untyped_preds,False)
        trows=[]; urows=[]
        for e in held:
            pred=action(tp,e,True) if tp else None
            vok,acts=exact_verify(e,pred) if pred else (False,[])
            trows.append({"episode":e.name,"pred":pred,"truth":e.action,"correct":pred==e.action,"verified":vok,"completecover_actions":acts})
            upred=action(up,e,False) if up else None
            urows.append({"episode":e.name,"pred":upred,"truth":e.action,"correct":upred==e.action})
        this_t=bool(tp and trows and all(r['correct'] for r in trows))
        this_v=bool(tp and trows and all(r['verified'] for r in trows))
        this_i=bool(tp and tp[0]=='exists_type' and tp[1]==SAME)
        this_a=bool(tp and invariant(tp,train+held,True))
        this_u=not bool(up and urows and all(r['correct'] for r in urows))
        typed_ok &= this_t; verified_ok &= this_v; intension_ok &= this_i; alpha_ok &= this_a; untyped_collapse &= this_u
        fold_rows.append({
            "heldout_positive_mechanism":mech,
            "positive_mechanism_absent_from_training":True,
            "typed_program":None if tp is None else pstr(tp),"typed_size":None if tp is None else psize(tp),"typed_checked":tc,
            "typed_heldout":trows,
            "untyped_program":None if up is None else pstr(up),"untyped_checked":uc,"untyped_heldout":urows,
            "typed_alpha_invariant":this_a,
            "untyped_transfer_collapses":this_u,
        })
    natural=[e for e in eps if accepted(e)]
    full,fc=synthesize(natural,typed_preds,True)
    hostile=[]
    for e in eps:
        if e.action!=REJECT: continue
        proposed=action(full,e,True) if full else None
        accepted_v,acts=exact_verify(e,proposed) if proposed else (False,[])
        hostile.append({"episode":e.name,"proposed":proposed,"verifier_accepts":accepted_v,"completecover_actions":acts})
    gates={
        "all_non_typed_summary_marginals_pair_matched":balanced,
        "existential_viability_is_minimum_full_policy":bool(full and full[0]=='exists_type' and full[1]==SAME),
        "leave_one_positive_mechanism_out_typed_transfer_100pct":typed_ok,
        "all_typed_heldout_actions_completecover_verified":verified_ok,
        "typed_policy_is_intensional_existential":intension_ok,
        "alpha_rename_and_mechanism_reorder_invariant":alpha_ok,
        "type_erasure_breaks_unseen_mechanism_transfer":untyped_collapse,
        "hostile_causal_and_preservation_controls_rejected":bool(hostile and all(not x['verifier_accepts'] for x in hostile)),
    }
    gates['CAUSAL_ISOLATION_EXISTENTIAL_VIABILITY_GATE']=all(gates.values())
    result={
        "status":"CAUSAL_ISOLATION_EXISTENTIAL_VIABILITY_V21",
        "residual":"EXISTENTIAL_OBJECT_NOT_CAUSALLY_ISOLATED_FROM_COVER_SUMMARY",
        "claim_scope":"finite matched-pair witness corpus; supplied witness type system and finite policy grammar; all non-typed policy observables pair-matched; exact hidden-carrier CompleteCover evaluator",
        "semantic_object":"Inhabited(V_same(rho)) := exists verified w : Option[Theta_same]",
        "typed_candidate_programs":len(typed_preds),"untyped_candidate_programs":len(untyped_preds),
        "pair_balance_audit":balance_rows,
        "full_minimum_typed_policy":None if full is None else {"program":pstr(full),"size":psize(full),"checked":fc},
        "mechanism_holdout_folds":fold_rows,
        "hostile_controls":hostile,
        "gates":gates,
    }
    (out/'RESULT.json').write_text(json.dumps(result,indent=2)); print(json.dumps(result,indent=2))

if __name__=='__main__': main()
