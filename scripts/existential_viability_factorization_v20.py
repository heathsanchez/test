#!/usr/bin/env python3
"""V20 — existential viability factorization.

Residual from V19:
    POLICY_STRUCTURE_UNDERDETERMINED_BY_LEAVE_ONE_MECHANISM_OUT

Question:
    Can heterogeneous verifier witness mechanisms be recognized as evidence for
    one common semantic proposition — inhabitation of the same-frame viability
    fibre — rather than memorized as unrelated Boolean atoms?

The learner receives typed witness producers
    w : residual -> Option[Theta_same]
with opaque, permutable mechanism identifiers.  It is NOT given the names
`candidate_preexists` or `cover_witness` as policy atoms.  The policy grammar
contains both name-sensitive atoms and type/role-level quantifiers.  Candidate
programs must fit training data AND satisfy preregistered alpha-renaming and
mechanism-reordering metamorphic constraints.  The minimum surviving program is
then frozen and tested on a positive witness mechanism never positive in that
fold's training data.

Boundary: finite supplied witness type system, finite mechanism carrier,
finite policy grammar, exact verifier and CompleteCover.  This does not establish
automatic discovery of the witness type system or adequacy map.
"""
from __future__ import annotations
import argparse, itertools, json
from dataclasses import dataclass
from pathlib import Path

SAME = "Theta_same"
OTHER = "Theta_other"
SAME_FRAME = "SAME_FRAME_REPAIR"
EXPAND = "EXPAND_CARRIER"
REJECT = "REJECT"

@dataclass(frozen=True)
class Witness:
    wid: str
    codomain: str
    present: bool
    verified: bool

@dataclass(frozen=True)
class Episode:
    name: str
    witnesses: tuple[Witness, ...]
    completecover_empty_same: bool
    causal_ok: bool = True
    preserve_ok: bool = True
    action: str = EXPAND

# Three operationally distinct same-frame witness mechanisms.  Only their opaque
# ids differ; their shared codomain is visible as type information.
MECHS = ("m_local", "m_cover", "m_symbolic")


def ep(name, positives=(), *, empty=False, causal=True, preserve=True, action=None,
       other_positive=False):
    ws=[]
    for m in MECHS:
        ws.append(Witness(m, SAME, m in positives, m in positives))
    ws.append(Witness("m_irrelevant", OTHER, other_positive, other_positive))
    if action is None:
        if not causal or not preserve:
            action=REJECT
        elif positives:
            action=SAME_FRAME
        elif empty:
            action=EXPAND
        else:
            action=REJECT
    return Episode(name, tuple(ws), empty, causal, preserve, action)


def corpus():
    # Natural-style historical roles: different proof modes for the same
    # semantic proposition, plus empty-fibre expansion cases and hostile controls.
    return [
        ep("arc_v12_like", ("m_cover",), action=SAME_FRAME),
        ep("lean_candidate_like", ("m_local",), action=SAME_FRAME),
        ep("symbolic_same_frame", ("m_symbolic",), action=SAME_FRAME),
        ep("fwl_like_empty", (), empty=True, action=EXPAND),
        ep("rc2_like_empty", (), empty=True, action=EXPAND),
        ep("bugsinpy_like_empty", (), empty=True, action=EXPAND),
        ep("irrelevant_other_type", (), empty=True, other_positive=True, action=EXPAND),
        ep("noncausal_control", ("m_local",), causal=False, action=REJECT),
        ep("preservation_control", ("m_cover",), preserve=False, action=REJECT),
        ep("unverified_no_cover", (), empty=False, action=REJECT),
    ]

# Policy DSL.  A policy predicate is represented as a tuple.
# atoms:
#   ('named', wid)          -- syntactic mechanism-specific witness
#   ('exists_type', type)   -- existential over all verified witnesses of codomain
#   ('empty_cover',)        -- exact CompleteCover emptiness fact
#   ('causal',), ('preserve',)
# combinators: ('not', p), ('and', p,q), ('or',p,q)


def eval_pred(p, e:Episode):
    op=p[0]
    if op=="named":
        w=next((w for w in e.witnesses if w.wid==p[1]),None)
        return bool(w and w.present and w.verified)
    if op=="exists_type":
        return any(w.codomain==p[1] and w.present and w.verified for w in e.witnesses)
    if op=="empty_cover": return e.completecover_empty_same
    if op=="causal": return e.causal_ok
    if op=="preserve": return e.preserve_ok
    if op=="not": return not eval_pred(p[1],e)
    if op=="and": return eval_pred(p[1],e) and eval_pred(p[2],e)
    if op=="or": return eval_pred(p[1],e) or eval_pred(p[2],e)
    raise ValueError(p)


def pstr(p):
    op=p[0]
    if op=="named": return f"verified({p[1]})"
    if op=="exists_type": return f"exists_verified[{p[1]}]"
    if op in ("empty_cover","causal","preserve"): return op
    if op=="not": return f"!({pstr(p[1])})"
    return f"{op}({pstr(p[1])},{pstr(p[2])})"


def psize(p):
    if p[0] in ("named","exists_type","empty_cover","causal","preserve"): return 1
    if p[0]=="not": return 1+psize(p[1])
    return 1+psize(p[1])+psize(p[2])


def generate_preds(max_size=5):
    base=[("named",m) for m in MECHS]+[("named","m_irrelevant"),
          ("exists_type",SAME),("exists_type",OTHER),
          ("empty_cover",),("causal",),("preserve",)]
    by={1:base}; seen={repr(x) for x in base}; allp=list(base)
    for sz in range(2,max_size+1):
        cur=[]
        for q in by.get(sz-1,[]):
            r=("not",q)
            if repr(r) not in seen: seen.add(repr(r));cur.append(r)
        for a_sz in range(1,sz-1):
            b_sz=sz-1-a_sz
            for a in by.get(a_sz,[]):
                for b in by.get(b_sz,[]):
                    # canonicalize commutative args
                    if repr(a)>repr(b): continue
                    for op in ("and","or"):
                        r=(op,a,b)
                        if repr(r) not in seen: seen.add(repr(r));cur.append(r)
        by[sz]=cur;allp.extend(cur)
    return sorted(allp,key=lambda p:(psize(p),pstr(p)))


def rename_episode(e:Episode, perm):
    ws=[]
    for w in e.witnesses:
        wid=perm.get(w.wid,w.wid)
        ws.append(Witness(wid,w.codomain,w.present,w.verified))
    # reordering is deliberately reversed after renaming.
    return Episode(e.name+"__alpha",tuple(reversed(ws)),e.completecover_empty_same,
                   e.causal_ok,e.preserve_ok,e.action)


def alpha_variants(e:Episode):
    # Two nontrivial permutations; typed existential semantics must be invariant.
    perms=[
        {"m_local":"m_cover","m_cover":"m_symbolic","m_symbolic":"m_local"},
        {"m_local":"m_symbolic","m_symbolic":"m_cover","m_cover":"m_local"},
    ]
    return [rename_episode(e,p) for p in perms]


def policy_action(pred,e):
    # Policy chooses between SAME_FRAME and EXPAND; verifier can still reject.
    return SAME_FRAME if eval_pred(pred,e) else EXPAND


def exact_action_verifier(e:Episode, proposed):
    inhabited=any(w.codomain==SAME and w.present and w.verified for w in e.witnesses)
    if not e.causal_ok or not e.preserve_ok:
        admissible=[]
    elif inhabited:
        admissible=[SAME_FRAME]
    elif e.completecover_empty_same:
        admissible=[EXPAND]
    else:
        admissible=[]
    return proposed in admissible, admissible


def fits_training(pred, train):
    # Learn only on accepted natural decisions. Controls are verifier tests, not labels.
    for e in train:
        if e.action in (SAME_FRAME,EXPAND) and policy_action(pred,e)!=e.action:
            return False
    return True


def metamorphic_invariant(pred, train):
    # Policy result must survive alpha-renaming and witness ordering changes.
    for e in train:
        v=eval_pred(pred,e)
        for r in alpha_variants(e):
            if eval_pred(pred,r)!=v: return False
    return True


def synthesize(train,preds):
    checked=0
    for p in preds:
        checked+=1
        if fits_training(p,train) and metamorphic_invariant(p,train):
            return p,checked
    return None,checked


def mechanism_holdout_folds(eps):
    folds=[]
    for held_mech in MECHS:
        held=[e for e in eps if any(w.wid==held_mech and w.present for w in e.witnesses)
              and e.action==SAME_FRAME and e.causal_ok and e.preserve_ok]
        # Remove every positive occurrence of the mechanism from training; other
        # positive mechanisms remain, along with all empty-fibre negatives.
        train=[]
        for e in eps:
            if e in held: continue
            if e.action==REJECT: continue
            train.append(e)
        folds.append((held_mech,train,held))
    return folds


def anonymous_boolean_ablation(train,held,preds):
    # Remove codomain/type-level existential operators; leave only opaque named
    # Booleans and ordinary connectives. This recreates V19's extensional setting.
    q=[p for p in preds if "exists_type" not in repr(p)]
    prog,checked=synthesize(train,q)
    return {
        "program":None if prog is None else pstr(prog),"checked":checked,
        "heldout_correct":bool(prog and all(policy_action(prog,e)==e.action for e in held))
    }


def main():
    ap=argparse.ArgumentParser();ap.add_argument("--out-dir",required=True);args=ap.parse_args()
    out=Path(args.out_dir);out.mkdir(parents=True,exist_ok=True)
    eps=corpus();preds=generate_preds(5)
    folds=[]
    all_holdout=True;all_verified=True;all_intensional=True;all_alpha=True;abl_drops=True
    for mech,train,held in mechanism_holdout_folds(eps):
        prog,checked=synthesize(train,preds)
        rows=[]
        for e in held:
            pred=policy_action(prog,e) if prog else None
            ok,admissible=exact_action_verifier(e,pred) if pred else (False,[])
            rows.append({"episode":e.name,"pred":pred,"truth":e.action,
                         "correct":pred==e.action,"verified":ok,
                         "completecover_actions":admissible})
        alpha_ok=bool(prog and metamorphic_invariant(prog,train+held))
        intensional=bool(prog and prog[0]=="exists_type" and prog[1]==SAME)
        ab=anonymous_boolean_ablation(train,held,preds)
        all_holdout &= bool(rows and all(r["correct"] for r in rows))
        all_verified &= bool(rows and all(r["verified"] for r in rows))
        all_alpha &= alpha_ok
        all_intensional &= intensional
        abl_drops &= not ab["heldout_correct"]
        folds.append({
            "heldout_positive_mechanism":mech,
            "positive_mechanism_absent_from_training":True,
            "program":None if prog is None else pstr(prog),
            "program_size":None if prog is None else psize(prog),
            "programs_checked":checked,
            "is_existential_viability_program":intensional,
            "alpha_rename_and_reorder_invariant":alpha_ok,
            "heldout":rows,
            "anonymous_boolean_ablation":ab,
        })

    # Full-corpus minimum law.
    natural=[e for e in eps if e.action in (SAME_FRAME,EXPAND)]
    full,full_checked=synthesize(natural,preds)
    hostile=[]
    for e in eps:
        if e.action!=REJECT: continue
        proposed=policy_action(full,e) if full else None
        accepted,acts=exact_action_verifier(e,proposed) if proposed else (False,[])
        hostile.append({"episode":e.name,"proposed":proposed,
                        "verifier_accepts":accepted,"completecover_actions":acts})

    gates={
        "existential_viability_object_synthesized":bool(full and full[0]=="exists_type" and full[1]==SAME),
        "minimum_under_declared_policy_grammar":full is not None,
        "leave_one_positive_mechanism_out_100pct":all_holdout,
        "all_heldout_actions_completecover_verified":all_verified,
        "positive_mechanism_names_never_required":all_intensional,
        "alpha_rename_and_mechanism_reorder_invariant":all_alpha,
        "typed_interface_ablation_breaks_mechanism_transfer":abl_drops,
        "hostile_noncausal_and_preservation_controls_rejected":bool(hostile and all(not x["verifier_accepts"] for x in hostile)),
    }
    gates["EXISTENTIAL_VIABILITY_FACTORIZATION_GATE"]=all(gates.values())
    result={
        "status":"EXISTENTIAL_VIABILITY_FACTORIZATION_V20",
        "residual":"POLICY_STRUCTURE_UNDERDETERMINED_BY_LEAVE_ONE_MECHANISM_OUT",
        "claim_scope":"finite supplied typed witness interface and policy grammar; witness mechanism names opaque/permutable; exact finite verifier and CompleteCover; no automatic adequacy-map or type-system discovery",
        "semantic_object":"Inhabited(V_same(rho)) := exists verified witness w : Option[Theta_same]",
        "candidate_programs_generated":len(preds),
        "full_minimum_policy":None if full is None else {"program":pstr(full),"size":psize(full),"checked":full_checked},
        "mechanism_holdout_folds":folds,
        "hostile_controls":hostile,
        "gates":gates,
    }
    (out/"RESULT.json").write_text(json.dumps(result,indent=2))
    print(json.dumps(result,indent=2))

if __name__=="__main__":main()
