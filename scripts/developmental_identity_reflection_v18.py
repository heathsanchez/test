#!/usr/bin/env python3
"""V18 — verifier-visible developmental identity reflection.

Scientific target
-----------------
V17 showed that a coarse semantic key could be sound but fail to reflect the
StrCC dependency class. V18 freezes that residual and asks a narrower question:

    Can a *minimal subset of verifier-visible relation families* identify the
    frozen developmental quotient class, without exposing the dependency graph
    itself to the learner?

The learner sees only observations obtainable from verification experiments:
  COVER       : whether bounded CompleteCover was attempted, whether a witness
                existed, and whether a local same-frame candidate pre-existed;
  CAUSAL      : whether closure appears after intervention and whether local
                ablation restores failure;
  PRESERVE    : whether protected old behavior/certificates survive;
  RETENTION   : whether a verified construction is later required/reused.

The hidden target is a typed developmental dependency graph distilled from six
historical MathGraph episodes plus hostile counterfactual controls. The graph is
used only by the evaluator. The learner exhaustively searches all subsets of the
four observable relation families and chooses the minimum subset whose equality
partition is exactly the hidden StrCC-style graph-isomorphism partition.

This deliberately does NOT append the dependency signature to the semantics.
It tests whether observable semantics *reflects* the hidden dependency class.

IMPORTANT BOUNDARY
------------------
The adequacy encodings, observable relation families, historical distillations,
and hostile controls are manually authored and finite. Passing does not prove
that arbitrary natural-domain dependency geometry is automatically identifiable.
"""
from __future__ import annotations
import argparse, itertools, json
from pathlib import Path

GROUPS=("COVER","CAUSAL","PRESERVE","RETENTION")


def episode(name, provenance, nodes, edges, cover, causal, preserve, retention, action):
    return {
        "name":name,"provenance":provenance,
        "nodes":tuple(sorted(nodes)),"edges":tuple(sorted(tuple(e) for e in edges)),
        "obs":{
            "COVER":tuple(cover),
            "CAUSAL":tuple(causal),
            "PRESERVE":tuple(preserve),
            "RETENTION":tuple(retention),
        },
        "action":action,
    }


def chain_expand(retain=False, causal=True, preserve=True):
    nodes={"RESIDUAL","CC_EMPTY","EXPAND","VERIFY","TRANSFER","ABLATE",
           "PRESERVE_OK" if preserve else "PRESERVE_FAIL"}
    edges={
        ("RESIDUAL","CC_EMPTY"),("CC_EMPTY","EXPAND"),("EXPAND","VERIFY"),
        ("VERIFY","TRANSFER"),("VERIFY","PRESERVE_OK" if preserve else "PRESERVE_FAIL"),
    }
    if causal: edges.add(("EXPAND","ABLATE"))
    if retain:
        nodes|={"RETAIN","REUSE"}; edges|={("VERIFY","RETAIN"),("RETAIN","REUSE")}
    return nodes,edges


def chain_same_cover(causal=True,preserve=True):
    nodes={"RESIDUAL","CC_NONEMPTY","SAME_FRAME","VERIFY","TRANSFER","ABLATE",
           "PRESERVE_OK" if preserve else "PRESERVE_FAIL"}
    edges={("RESIDUAL","CC_NONEMPTY"),("CC_NONEMPTY","SAME_FRAME"),
           ("SAME_FRAME","VERIFY"),("VERIFY","TRANSFER"),
           ("VERIFY","PRESERVE_OK" if preserve else "PRESERVE_FAIL")}
    if causal: edges.add(("SAME_FRAME","ABLATE"))
    return nodes,edges


def chain_same_candidate(causal=True,preserve=True,retain=True):
    nodes={"RESIDUAL","CANDIDATE","SAME_FRAME","VERIFY","TRANSFER","ABLATE",
           "PRESERVE_OK" if preserve else "PRESERVE_FAIL"}
    edges={("RESIDUAL","CANDIDATE"),("CANDIDATE","SAME_FRAME"),
           ("SAME_FRAME","VERIFY"),("VERIFY","TRANSFER"),
           ("VERIFY","PRESERVE_OK" if preserve else "PRESERVE_FAIL")}
    if causal: edges.add(("SAME_FRAME","ABLATE"))
    if retain:
        nodes|={"RETAIN","REUSE"}; edges|={("VERIFY","RETAIN"),("RETAIN","REUSE")}
    return nodes,edges


def build_episodes():
    out=[]
    # Four surface-distinct histories sharing the same developmental graph.
    for name,prov in [
        ("fwl","mathgraph_gold_fwl_constructor_synthesis.py"),
        ("rc2","RC2_LOCAL_TEST_RESULTS.json"),
        ("mi_v8_external","MI_V8_PRISTINE_EXTERNAL_STREAM_RESULT_20260812.json"),
        ("bugsinpy_new_primitive","MI_V10_DEFINITIVE_RESULT.json"),
    ]:
        n,e=chain_expand(retain=False,causal=True,preserve=True)
        out.append(episode(name,prov,n,e,
            cover=(1,0,0),causal=(1,1),preserve=(1,),retention=(0,),action="EXPAND_CARRIER"))

    # V12: same-frame witness after an explicit nonempty CompleteCover.
    n,e=chain_same_cover()
    out.append(episode("arc_v12","ARC V12 PR #40 / Actions",
        n,e,cover=(1,1,0),causal=(1,1),preserve=(1,),retention=(0,),action="SAME_FRAME_REPAIR"))

    # Lean-kernel development: local candidate path rather than CompleteCover witness,
    # with retained/reused optimization state.
    n,e=chain_same_candidate(retain=True)
    out.append(episode("lean_kernel","mathgraph-lean-kernel Arena development",
        n,e,cover=(0,0,1),causal=(1,1),preserve=(1,),retention=(1,),action="SAME_FRAME_REPAIR"))

    # Hostile controls prevent COVER alone from defining developmental identity.
    # Same cover state, different causal incidence.
    n,e=chain_expand(retain=False,causal=False,preserve=True)
    out.append(episode("control_expand_noncausal","hostile counterfactual",
        n,e,cover=(1,0,0),causal=(1,0),preserve=(1,),retention=(0,),action="EXPAND_CARRIER"))

    # Same cover + causal state, preservation differs.
    n,e=chain_expand(retain=False,causal=True,preserve=False)
    out.append(episode("control_expand_preservation_fail","hostile counterfactual",
        n,e,cover=(1,0,0),causal=(1,1),preserve=(0,),retention=(0,),action="EXPAND_CARRIER"))

    # Same cover + causal + preservation, but retained construction changes future dependency.
    n,e=chain_expand(retain=True,causal=True,preserve=True)
    out.append(episode("control_expand_retained","hostile counterfactual",
        n,e,cover=(1,0,0),causal=(1,1),preserve=(1,),retention=(1,),action="EXPAND_CARRIER"))

    return out


def qkey(ep):
    # Frozen StrCC-style target: typed graph up to the already abstracted role names.
    # Domain/surface identifiers are absent from this key.
    return (ep["nodes"],ep["edges"])


def sig(ep,subset): return tuple((g,ep["obs"][g]) for g in subset)


def pairwise_exact(eps,subset):
    for a,b in itertools.combinations(eps,2):
        if (sig(a,subset)==sig(b,subset)) != (qkey(a)==qkey(b)):
            return False
    return True


def synthesize_basis(eps):
    checked=0; winners=[]
    for k in range(1,len(GROUPS)+1):
        for ss in itertools.combinations(GROUPS,k):
            checked+=1
            if pairwise_exact(eps,ss): winners.append(ss)
        if winners: break
    if not winners:return None,checked,[]
    return min(winners),checked,winners


def loo_reflection(eps,basis):
    rows=[]
    for h in eps:
        train=[e for e in eps if e is not h]
        comparisons=[]
        ok=True
        for t in train:
            pred=(sig(h,basis)==sig(t,basis)); truth=(qkey(h)==qkey(t))
            comparisons.append({"train":t["name"],"pred_equiv":pred,"truth_equiv":truth})
            ok &= pred==truth
        rows.append({"heldout":h["name"],"correct":ok,"comparisons":comparisons})
    return rows


def basis_ablation(eps,basis):
    out=[]
    for g in basis:
        ss=tuple(x for x in basis if x!=g)
        out.append({"removed":g,"remaining":ss,"still_reflects":pairwise_exact(eps,ss)})
    return out


def synthesize_action_rule(train,basis):
    # Search small equality rules over individual observable coordinates. Rule form:
    # if feature == value -> A else B. This is intentionally weaker than graph lookup.
    feats=[]
    for g in basis:
        width=len(train[0]["obs"][g])
        feats.extend((g,i) for i in range(width))
    actions=sorted(set(e["action"] for e in train))
    if len(actions)!=2:return None
    for g,i in feats:
        vals=sorted(set(e["obs"][g][i] for e in train))
        for v in vals:
            for a,b in [actions,actions[::-1]]:
                good=True
                for e in train:
                    pred=a if e["obs"][g][i]==v else b
                    if pred!=e["action"]:good=False;break
                if good:return (g,i,v,a,b)
    return None


def eval_action_rule(rule,e):
    if rule is None:return None
    g,i,v,a,b=rule
    return a if e["obs"][g][i]==v else b


def loo_action(eps,basis):
    rows=[]
    for h in eps:
        train=[e for e in eps if e is not h]
        rule=synthesize_action_rule(train,basis)
        pred=eval_action_rule(rule,h)
        rows.append({"heldout":h["name"],"rule":rule,"pred":pred,"truth":h["action"],"correct":pred==h["action"]})
    return rows


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--out-dir',required=True); a=ap.parse_args()
    out=Path(a.out_dir); out.mkdir(parents=True,exist_ok=True)
    eps=build_episodes(); basis,checked,winners=synthesize_basis(eps)
    loo=loo_reflection(eps,basis) if basis else []
    abl=basis_ablation(eps,basis) if basis else []
    action=loo_action(eps,basis) if basis else []
    natural=[e for e in eps if not e['name'].startswith('control_')]
    natural_cross=[]
    for a1,b1 in itertools.combinations(natural,2):
        natural_cross.append({"a":a1['name'],"b":b1['name'],
                              "same_hidden_class":qkey(a1)==qkey(b1),
                              "same_learned_class":sig(a1,basis)==sig(b1,basis)})
    gates={
        "basis_found":basis is not None,
        "finite_semantic_soundness_and_reflection":bool(basis and pairwise_exact(eps,basis)),
        "leave_one_episode_out_reflection_100pct":bool(loo and all(r['correct'] for r in loo)),
        "every_selected_relation_family_necessary":bool(abl and all(not r['still_reflects'] for r in abl)),
        "fwl_rc2_identified_same":bool(basis and sig(eps[0],basis)==sig(eps[1],basis) and qkey(eps[0])==qkey(eps[1])),
        "arc_lean_not_falsely_collapsed":bool(basis and sig(eps[4],basis)!=sig(eps[5],basis) and qkey(eps[4])!=qkey(eps[5])),
        "leave_one_episode_out_action_transfer_100pct":bool(action and all(r['correct'] for r in action)),
    }
    gates["DEVELOPMENTAL_IDENTITY_REFLECTION_GATE"]=all(gates.values())
    result={
        "status":"DEVELOPMENTAL_IDENTITY_REFLECTION_V18",
        "residual":"DEVELOPMENTAL_SEMANTICS_DOES_NOT_REFLECT_DEPENDENCY_GEOMETRY",
        "claim_scope":"finite manually-authored adequacy encodings over six historical developmental episodes plus hostile counterfactual controls; hidden target is typed dependency graph; learner sees only verifier-visible relation families; exhaustive subset synthesis",
        "historical_episodes":[{"name":e['name'],"provenance":e['provenance']} for e in natural],
        "hostile_controls":[e['name'] for e in eps if e['name'].startswith('control_')],
        "candidate_relation_families":list(GROUPS),
        "basis_subsets_checked":checked,
        "minimum_reflecting_basis":None if basis is None else list(basis),
        "minimum_basis_ties":[list(x) for x in winners],
        "basis_ablation":abl,
        "leave_one_out_reflection":loo,
        "leave_one_out_action_transfer":action,
        "natural_cross_domain_equivalence_checks":natural_cross,
        "gates":gates,
    }
    (out/'RESULT.json').write_text(json.dumps(result,indent=2))
    print(json.dumps(result,indent=2))

if __name__=='__main__':main()
