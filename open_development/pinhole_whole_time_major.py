"""Major whole-time falsifier: observation minimization, goal-conditioned histories,
real MDA proof-capability dependency closure, and revocation. Exact finite checks.
"""
from __future__ import annotations
import itertools,json,tempfile
from pathlib import Path
from .pinhole_temporal_whole_v1 import partition
from .runtime import EvidenceStore
from .composition import ProofCompositionAdapter
from .mda_v7 import MinimalContinuation
from .role_transport import QualifiedRoleLiftAdapter
from .role_transport_qualification import BASE,SOURCE_THIRD,NEXT,AFTER,FUTURES,obl

def main():
    histories=tuple(itertools.product((0,1),repeat=3))
    def present(h):
        s=0
        for x in h:s=(2*s+x)%3
        return s
    futures=tuple(itertools.chain.from_iterable(itertools.product((0,1),repeat=n) for n in range(4)))
    def outcome(h,f):
        s=present(h)
        for x in f:s=(2*s+x)%3
        return s%2
    whole=partition(histories,futures,outcome)
    # Enumerate every subset of future tests; find ALL inclusion-minimal
    # sufficient apertures and their smallest cardinality.
    best=[]; min_size=len(futures)+1
    for mask in range(1<<len(futures)):
        if mask.bit_count()>min_size:continue
        subset=tuple(f for i,f in enumerate(futures) if mask>>i&1)
        if partition(histories,subset,outcome)==whole:
            if len(subset)<min_size:min_size=len(subset);best=[]
            best.append(tuple(''.join(map(str,f)) or 'epsilon' for f in subset))
    assert best
    # Every possible pairwise history test is checked by direct evaluation.
    for a,b in itertools.combinations(histories,2):
        eq=all(outcome(a,f)==outcome(b,f) for f in futures)
        eq2=any(a in c and b in c for c in whole)
        assert eq==eq2
    # Future-goal-conditioned exact existence vs present-only ambiguity.
    goal_cases=0;consistent=0;present_ambiguous=0
    for obs in (0,1):
        matching=[h for h in histories if outcome(h,())==obs]
        for f in futures:
            for desired in (0,1):
                goal_cases+=1
                candidates=[h for h in matching if outcome(h,f)==desired]
                consistent+=bool(candidates)
                present_ambiguous+=bool(candidates) and len(candidates)!=len(matching)
    with tempfile.TemporaryDirectory() as td:
        path=Path(td)/'ledger.sqlite';store=EvidenceStore(path)
        old=MinimalContinuation(store,ProofCompositionAdapter())
        for t,b in zip((BASE[0],BASE[1],SOURCE_THIRD),(2,1,1)):
            assert old.run_minimal(obl(t,b)).outcome=='COMMIT'
        new=MinimalContinuation(store,QualifiedRoleLiftAdapter())
        for t in (NEXT,AFTER):
            assert new.run_minimal(obl(t,1)).outcome=='COMMIT'
        state=store.state();caps=state['capabilities'];assert len(caps)==6
        ids=tuple(sorted(caps))
        deps={k:set(v['repair']['dependencies']) for k,v in caps.items()}
        assert all(p in deps for parents in deps.values() for p in parents)
        # Whole-DAG dependency closures, not local one-step choice.
        def descendants(root):
            affected={root}
            while True:
                nxt=affected|{k for k,parents in deps.items() if parents&affected}
                if nxt==affected:return affected
                affected=nxt
        closures={k:descendants(k) for k in ids}
        edges=sum(len(x) for x in deps.values())
        # Compare exact graph-wide invalidation with the actual ledger's
        # authoritative cascading revocation on six independent shadow copies.
        for key in ids:
            shadow=EvidenceStore(Path(td)/(key+'.sqlite'))
            for event in store.events():shadow.append(event)
            removed=set(shadow.revoke(key,'whole-time causal ablation'))
            assert removed==closures[key]
            shadow.close()
        store.close();store=EvidenceStore(path)
        checks=[MinimalContinuation(store,QualifiedRoleLiftAdapter()).run_minimal(obl(t,0)) for t in FUTURES]
        assert len(checks)==16 and all(x.verdict=='verified' and x.outcome=='IDENTITY' for x in checks)
        store.close()
    print(json.dumps({
      'schema':'metalogic.pinhole.whole-time-major.v1',
      'status':'PASS_EXACT_BOUNDED_WHOLE_TIME',
      'history_count':len(histories),'future_tests':len(futures),
      'present_classes':len(partition(histories,((),),outcome)),
      'whole_future_classes':len(whole),
      'minimal_observation_count':min_size,
      'minimum_aperture_choices':len(best),
      'minimum_apertures':best[:12],
      'goal_conditioned_cases':goal_cases,
      'consistent_goal_cases':consistent,
      'present_ambiguous_goal_cases':present_ambiguous,
      'mda_capabilities':len(ids),'mda_dependency_edges':edges,
      'mda_exact_revocation_shadows':len(ids),
      'mda_protected_future_replays':len(checks),
      'whole_lifecycle_cost_optimality':'UNKNOWN',
      'cross_domain_future_semantics':'NOT_ESTABLISHED',
      'autonomous_language_growth':'UNKNOWN',
      'physical_simultaneity':'NOT_CLAIMED'
    },sort_keys=True,indent=2))
if __name__=='__main__':main()
