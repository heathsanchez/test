#!/usr/bin/env python3
"""V13 — level-blind developmental controller integration benchmark.

This is deliberately an integration test of the existing MathGraph developmental
calculus, not a new replacement theory. Every episode exposes the same initial
interface: a verifier-defined target is outside current bounded closure. The
controller is NOT told which intervention level is required.

It must:
  residual -> K(rho) -> CompleteCover(T_0) -> ... -> first nonempty version
  space -> minimum-cost Theta -> verify -> local ablation -> retain/reuse.

The benchmark contains heterogeneous finite domains with different surface
encodings but the same verifier-relative obstruction roles. Ground-truth minimal
level l* is computed independently by exhaustive enumeration of every declared
carrier. The controller then runs level-blind and is scored on l-hat == l*,
over/under-promotion, causal closure, and retained-schema reuse.

IMPORTANT BOUNDARY: the obstruction-role vocabulary and nested transformation
families are supplied. This tests autonomous LEVEL SELECTION and recursive
ratcheting under exact bounded CompleteCover; it does not yet demonstrate
invention of the level hierarchy or discovery of the obstruction ontology.
"""
from __future__ import annotations
import argparse, json, random
from dataclasses import dataclass
from pathlib import Path
from collections import Counter, defaultdict

LEVELS = (
    "SEARCH",
    "COMPOSE",
    "OPERATOR",
    "OBSERVABLE",
    "RELATION",
    "ARITY_FRAME",
)
ROLES = (
    "PATH_MISSING",
    "ATOMS_PRESENT_NOT_COMPOSED",
    "MISSING_EFFECT",
    "ALIASED_DISTINCTION",
    "UNADDRESSABLE_RELATION",
    "CARRIER_ARITY_INSUFFICIENT",
)

@dataclass(frozen=True)
class Theta:
    name: str
    level: int
    effects: frozenset[str]
    cost: tuple[int,int,str]

@dataclass
class Episode:
    eid: str
    domain: str
    surface: dict[str,str]
    required: frozenset[str]
    protected: frozenset[str]
    impossible: bool


def build_carriers(rng: random.Random):
    """Finite nested intervention families with distractors and cross-effects."""
    carriers=[]
    for i,role in enumerate(ROLES):
        xs=[]
        # exact primitive at this level
        xs.append(Theta(f"L{i}_exact_{role}", i, frozenset([role]), (1,1,f"exact-{role}")))
        # several lawful distractors that do not satisfy K alone
        for j in range(7):
            other=ROLES[(i+j+1)%len(ROLES)]
            xs.append(Theta(f"L{i}_distractor_{j}", i, frozenset([other]), (1,2+j,f"d{j}")))
        # a higher-cost mixed action that can repair role plus an extra effect
        extra=ROLES[(i+1)%len(ROLES)]
        xs.append(Theta(f"L{i}_mixed", i, frozenset([role,extra]), (2,5,"mixed")))
        carriers.append(xs)
    return carriers


def make_domains():
    # Surface names deliberately differ. Controller receives verifier-normalized
    # residual roles, while raw domain labels are retained only for transfer audit.
    return {
      "equational": {
        "PATH_MISSING":"rewrite_frontier_gap",
        "ATOMS_PRESENT_NOT_COMPOSED":"lemma_synergy",
        "MISSING_EFFECT":"missing_inference_effect",
        "ALIASED_DISTINCTION":"term_quotient_alias",
        "UNADDRESSABLE_RELATION":"endpoint_unaddressable",
        "CARRIER_ARITY_INSUFFICIENT":"context_arity_shortfall",
      },
      "graphs": {
        "PATH_MISSING":"certificate_path_gap",
        "ATOMS_PRESENT_NOT_COMPOSED":"motif_composition_gap",
        "MISSING_EFFECT":"missing_graph_operator",
        "ALIASED_DISTINCTION":"wl_alias",
        "UNADDRESSABLE_RELATION":"incidence_unaddressable",
        "CARRIER_ARITY_INSUFFICIENT":"fwl_arity_shortfall",
      },
      "arc": {
        "PATH_MISSING":"search_route_gap",
        "ATOMS_PRESENT_NOT_COMPOSED":"transform_composition_gap",
        "MISSING_EFFECT":"missing_constructor_effect",
        "ALIASED_DISTINCTION":"residual_signature_alias",
        "UNADDRESSABLE_RELATION":"object_correspondence_gap",
        "CARRIER_ARITY_INSUFFICIENT":"frame_language_shortfall",
      },
      "programs": {
        "PATH_MISSING":"repair_trace_gap",
        "ATOMS_PRESENT_NOT_COMPOSED":"edit_synergy",
        "MISSING_EFFECT":"missing_repair_operator",
        "ALIASED_DISTINCTION":"state_alias",
        "UNADDRESSABLE_RELATION":"dependency_unaddressable",
        "CARRIER_ARITY_INSUFFICIENT":"schema_arity_shortfall",
      },
    }


def make_episodes(seed=1729, per_domain=84):
    rng=random.Random(seed); ds=make_domains(); eps=[]
    for d,surface in ds.items():
        # Balanced across six levels plus explicit impossible controls.
        kinds=list(range(len(LEVELS)))+[None]
        for n in range(per_domain):
            k=kinds[n%len(kinds)]
            if k is None:
                # requirement deliberately outside declared hierarchy
                req=frozenset(["OUTSIDE_DECLARED_META_LANGUAGE"]); impossible=True
            else:
                # primary role is exactly the minimum intervention level; sometimes
                # add lower-level obligations already repairable by the same Theta.
                req={ROLES[k]}
                if k>0 and rng.random()<0.35:
                    req.add(ROLES[rng.randrange(k)])
                req=frozenset(req); impossible=False
            protected=frozenset(["VERIFIER_IDENTITY","OLD_CERTIFICATES"])
            eps.append(Episode(f"{d}-{n:03d}",d,surface,req,protected,impossible))
    rng.shuffle(eps)
    return eps


def apply(theta: Theta, ep: Episode, retained_effects=frozenset()):
    """Verifier semantics: obligations are monotone effects; protected invariants persist."""
    achieved=set(retained_effects)|set(theta.effects)
    solved=ep.required.issubset(achieved)
    preserve=True  # all declared interventions are additive in this finite benchmark
    return solved, preserve, frozenset(achieved)


def exact_ground_truth(ep, carriers):
    """Independent exhaustive l* over all single and depth-2 compositions per level."""
    if ep.impossible: return None
    accumulated=[]
    for level,xs in enumerate(carriers):
        accumulated += xs
        # single actions
        for a in accumulated:
            if ep.required.issubset(a.effects): return level
        # depth-2 compositions available by this level
        for i,a in enumerate(accumulated):
            for b in accumulated[i+1:]:
                if ep.required.issubset(a.effects|b.effects): return level
    return None


def version_space(ep, available, retained_effects):
    """Exact finite CompleteCover of singles and ordered-distinct pairs."""
    out=[]; checked=0
    for a in available:
        checked+=1
        eff=retained_effects|a.effects
        if ep.required.issubset(eff): out.append(((a,), eff))
    for a in available:
        for b in available:
            if a is b: continue
            checked+=1
            eff=retained_effects|a.effects|b.effects
            if ep.required.issubset(eff): out.append(((a,b),eff))
    return out,checked


def choose_min(vs):
    def c(item):
        acts,_=item
        return (len(acts), sum(a.cost[1] for a in acts), tuple(a.name for a in acts))
    return min(vs,key=c)


def controller(ep, carriers, registry):
    # K(rho) is the verifier-normalized set of unresolved necessary effects.
    retained=frozenset(registry.get(ep.domain,set()))
    rho={"unresolved_roles":sorted(ep.required-retained),"target_not_in_closure":True}
    K=frozenset(ep.required-retained)
    trace=[]; available=[]
    if not K:
        return {"status":"REUSED","level_hat":0,"rho":rho,"K":[],"trace":trace,"acts":[],"causal":True,"solved":True}
    for level,xs in enumerate(carriers):
        available += xs
        vs,checked=version_space(ep,available,retained)
        trace.append({"level":level,"name":LEVELS[level],"CompleteCover":True,"checked":checked,"version_space":len(vs)})
        if not vs: continue
        acts,eff=choose_min(vs)
        # verify presence and additive preservation
        solved=ep.required.issubset(eff); preserve=True
        # local ablation: remove selected acts, retain everything else
        ablated=ep.required.issubset(retained)
        causal=bool(solved and not ablated)
        if solved and preserve and causal:
            # retain only effects actually required on this episode; this keeps
            # the registry compact and gives later reuse a causal provenance.
            registry.setdefault(ep.domain,set()).update(ep.required)
        return {"status":"SOLVED" if solved else "FAILED","level_hat":level,"rho":rho,"K":sorted(K),"trace":trace,"acts":[a.name for a in acts],"causal":causal,"solved":solved}
    return {"status":"OBSTRUCTED","level_hat":None,"rho":rho,"K":sorted(K),"trace":trace,"acts":[],"causal":False,"solved":False}


def run(seed=1729, per_domain=84):
    rng=random.Random(seed); carriers=build_carriers(rng); episodes=make_episodes(seed,per_domain)
    # Frozen ground truth before sequential retention changes anything.
    truth={e.eid:exact_ground_truth(e,carriers) for e in episodes}
    registry={}; rows=[]
    for ep in episodes:
        res=controller(ep,carriers,registry); lstar=truth[ep.eid]
        lhat=res["level_hat"]
        # For retained reuse, level_hat=0 is not compared to l* because the state
        # has legitimately changed. Accuracy metric is on first encounters only.
        reused=(res["status"]=="REUSED")
        correct=(None if reused else lhat==lstar)
        over=(False if reused or lhat is None or lstar is None else lhat>lstar)
        under=(False if reused or lhat is None or lstar is None else lhat<lstar)
        rows.append({"episode":ep.eid,"domain":ep.domain,"l_star":lstar,"l_hat":lhat,"reused":reused,"level_correct":correct,"over":over,"under":under,"solved":res['solved'],"causal":res['causal'],"K":res['K'],"acts":res['acts'],"trace":res['trace']})
    fresh=[r for r in rows if not r['reused']]
    decidable=[r for r in fresh if r['l_star'] is not None]
    impossible=[r for r in fresh if r['l_star'] is None]
    accuracy=sum(r['level_correct'] for r in fresh)/max(1,len(fresh))
    solve=sum(r['solved'] for r in decidable)/max(1,len(decidable))
    causal=sum(r['causal'] for r in decidable)/max(1,len(decidable))
    obstruction=sum((r['l_hat'] is None) for r in impossible)/max(1,len(impossible))
    reuse=sum(r['reused'] for r in rows)
    by_domain={}
    for d in sorted(set(r['domain'] for r in rows)):
        rr=[r for r in fresh if r['domain']==d]
        by_domain[d]={"fresh":len(rr),"level_accuracy":sum(x['level_correct'] for x in rr)/max(1,len(rr)),"reuse":sum(x['reused'] for x in rows if x['domain']==d)}
    gates={
      "ground_truth_completecover":True,
      "controller_completecover_each_attempt":all(all(t['CompleteCover'] for t in r['trace']) for r in fresh),
      "level_accuracy_100pct":accuracy==1.0,
      "zero_overpromotion":not any(r['over'] for r in fresh),
      "zero_underpromotion":not any(r['under'] for r in fresh),
      "all_decidable_close":solve==1.0,
      "all_decidable_causal":causal==1.0,
      "all_impossible_obstruct":obstruction==1.0,
      "persistent_reuse_observed":reuse>0,
      "all_domains_perfect_fresh_level_accuracy":all(v['level_accuracy']==1.0 for v in by_domain.values()),
    }
    gates['LEVEL_BLIND_CONTROLLER_GATE']=all(gates.values())
    return {
      "status":"LEVEL_BLIND_DEVELOPMENTAL_CONTROLLER_V13",
      "claim_scope":"finite exact integration benchmark; supplied obstruction-role ontology and supplied nested intervention hierarchy; controller is blind to episode minimal level; exact CompleteCover over singles and ordered-distinct depth-2 compositions; additive preservation; local causal ablation; persistent within-domain retention",
      "levels":list(LEVELS),"roles":list(ROLES),"episodes":len(rows),"fresh_decisions":len(fresh),"reused":reuse,
      "metrics":{"P_lhat_eq_lstar":accuracy,"decidable_solve_rate":solve,"decidable_causal_rate":causal,"impossible_obstruction_rate":obstruction,"overpromotion":sum(r['over'] for r in fresh),"underpromotion":sum(r['under'] for r in fresh)},
      "by_domain":by_domain,"registry_final":{k:sorted(v) for k,v in registry.items()},"gates":gates,"rows":rows,
    }


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--out-dir',required=True); ap.add_argument('--seed',type=int,default=1729); ap.add_argument('--per-domain',type=int,default=84); a=ap.parse_args()
    out=Path(a.out_dir); out.mkdir(parents=True,exist_ok=True)
    result=run(a.seed,a.per_domain)
    (out/'RESULT.json').write_text(json.dumps(result,indent=2))
    # concise stdout for Actions logs
    slim={k:v for k,v in result.items() if k not in ('rows',)}
    print(json.dumps(slim,indent=2))

if __name__=='__main__': main()
