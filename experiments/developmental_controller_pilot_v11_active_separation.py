#!/usr/bin/env python3
"""V11: isolate ACTIVE DEVELOPMENTAL SEPARATION.

The version space is already supplied and correct. The only question is whether the
controller chooses interventions for expected discrimination rather than following a
fixed/passive sequence. Hypotheses have overlapping signatures, so no one probe names
the hidden regime.

Arms:
  ACTIVE  - choose the unused probe minimizing expected remaining version-space size.
  PASSIVE - fixed precommitted probe order p5,p6,p4,... independent of live rivals.

Primary protected comparison is after two probes. Secondary metric is probes required
to reach a singleton. This is a bounded controller-policy test; it does not test open-
ended hypothesis generation or whether the proposed experiment can be executed in a
natural scientific domain.
"""
from __future__ import annotations
import json
from pathlib import Path

H = {
  'constructor_gap':         {'prior':.24,'sig':{'p1':0,'p2':0,'p3':0,'p4':0,'p5':1,'p6':1}},
  'continuation_ir':         {'prior':.21,'sig':{'p1':0,'p2':0,'p3':1,'p4':1,'p5':0,'p6':1}},
  'multi_episode_compound':  {'prior':.19,'sig':{'p1':0,'p2':1,'p3':0,'p4':1,'p5':1,'p6':0}},
  'routing_refinement':      {'prior':.15,'sig':{'p1':1,'p2':0,'p3':1,'p4':0,'p5':1,'p6':0}},
  'representation_quotient': {'prior':.12,'sig':{'p1':1,'p2':1,'p3':0,'p4':0,'p5':0,'p6':1}},
  'verification_hardening':  {'prior':.09,'sig':{'p1':1,'p2':1,'p3':1,'p4':1,'p5':1,'p6':1}},
}
PROBES=list(next(iter(H.values()))['sig'])
PASSIVE_ORDER=['p5','p6','p4','p3','p2','p1']

def update(live,p,o): return [h for h in live if H[h]['sig'][p]==o]

def expected_remaining(live,p):
    z=sum(H[h]['prior'] for h in live)
    ans=0.0
    for o in (0,1):
        s=[h for h in live if H[h]['sig'][p]==o]
        mass=sum(H[h]['prior'] for h in s)/z if z else 0.0
        ans += mass*len(s)
    return ans

def active_probe(live,used):
    return min((p for p in PROBES if p not in used),key=lambda p:(expected_remaining(live,p),p))

def predict(live): return max(live,key=lambda h:H[h]['prior'])

def run(hidden,mode,budget=2):
    live=list(H); used=[]; trace=[]
    for step in range(budget):
        if len(live)==1: break
        if mode=='ACTIVE': p=active_probe(live,used)
        else: p=next(p for p in PASSIVE_ORDER if p not in used)
        used.append(p); o=H[hidden]['sig'][p]; before=len(live); live=update(live,p,o)
        trace.append({'probe':p,'outcome':o,'before':before,'after':len(live),'expected_remaining':expected_remaining([h for h in H if all(H[h]['sig'][q]==H[hidden]['sig'][q] for q in used[:-1])],p) if mode=='ACTIVE' else None})
    return {'live':live,'prediction':predict(live),'correct':predict(live)==hidden,'used':used,'trace':trace}

def probes_to_singleton(hidden,mode):
    live=list(H); used=[]
    while len(live)>1:
        p=active_probe(live,used) if mode=='ACTIVE' else next(p for p in PASSIVE_ORDER if p not in used)
        used.append(p); live=update(live,p,H[hidden]['sig'][p])
    return len(used),used

def main():
    rows=[]
    for hidden in H:
        a=run(hidden,'ACTIVE'); p=run(hidden,'PASSIVE')
        an,ap=probes_to_singleton(hidden,'ACTIVE'); pn,pp=probes_to_singleton(hidden,'PASSIVE')
        rows.append({'hidden':hidden,'active':a,'passive':p,'active_to_singleton':an,'passive_to_singleton':pn,'active_path':ap,'passive_path':pp})
    n=len(rows)
    ac=sum(r['active']['correct'] for r in rows); pc=sum(r['passive']['correct'] for r in rows)
    am=sum(r['active_to_singleton'] for r in rows)/n; pm=sum(r['passive_to_singleton'] for r in rows)/n
    gates={
      'active_two_probe_accuracy_strictly_better': ac>pc,
      'active_mean_probes_to_singleton_lower': am<pm,
      'active_recovers_every_hidden_regime': all(r['active_to_singleton']<=3 for r in rows),
      'passive_not_artificially_broken': all(r['passive_to_singleton']<=3 for r in rows),
    }
    out={'protocol':'DEVELOPMENTAL_CONTROLLER_PILOT_V11_ACTIVE_SEPARATION','episodes':n,'active_correct_after_2':ac,'passive_correct_after_2':pc,'active_mean_probes_to_singleton':am,'passive_mean_probes_to_singleton':pm,'gates':gates,'verdict':'PASS_ACTIVE_SEPARATION' if all(gates.values()) else 'FAIL_OR_INCONCLUSIVE','rows':rows,'claim_boundary':'Bounded supplied hypothesis/signature world. Establishes only the controller value of selecting probes for version-space discrimination; it does not establish natural experiment synthesis or open-ended latent-hypothesis generation.'}
    Path('v11_active_separation_result.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
    print(json.dumps(out,indent=2,sort_keys=True))
    if out['verdict'].startswith('FAIL'): raise SystemExit(1)
if __name__=='__main__': main()
