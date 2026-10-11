"""Flash whole-future major stress: actual MDA lineage, all subsets and exact oracles.

No synthetic cross-domain edges, no claims of new optimal constructor.
"""
from __future__ import annotations
import itertools,json,tempfile
from pathlib import Path
from .runtime import EvidenceStore
from .composition import ProofCompositionAdapter
from .mda_v7 import MinimalContinuation
from .role_transport import QualifiedRoleLiftAdapter
from .role_transport_qualification import BASE,SOURCE_THIRD,NEXT,AFTER,FUTURES,obl

def main():
    with tempfile.TemporaryDirectory() as td:
        path=Path(td)/"actual.sqlite"
        store=EvidenceStore(path)
        old=MinimalContinuation(store,ProofCompositionAdapter())
        acquired=[]
        for t,b in zip((BASE[0],BASE[1],SOURCE_THIRD),(2,1,1)):
            r=old.run_minimal(obl(t,b));assert r.outcome=="COMMIT";acquired.extend(r.retained)
        new=MinimalContinuation(store,QualifiedRoleLiftAdapter())
        for t in (NEXT,AFTER):
            r=new.run_minimal(obl(t,1));assert r.outcome=="COMMIT";acquired.extend(r.retained)
        live=store.state();caps=live["capabilities"];assert len(caps)==6
        ids=tuple(sorted(caps))
        deps={k:set(v["repair"]["dependencies"]) for k,v in caps.items()}
        assert all(parents<=set(ids) for parents in deps.values())
        def closed(sub):
            return all(deps[k]<=sub for k in sub)
        def downward(sub):
            while True:
                nxt={k for k in sub if deps[k]<=sub}
                if nxt==sub:return nxt
                sub=nxt
        def forward(seed,allowed):
            present=set(seed)&set(allowed)
            while True:
                nxt=present|{k for k in allowed if deps[k]<=present}
                if nxt==present:return present
                present=nxt
        subsets=[{ids[i] for i in range(len(ids)) if mask>>i&1} for mask in range(1<<len(ids))]
        # Complete lattice of subsets, compare two independent constructions.
        closed_subsets=[s for s in subsets if closed(s)]
        assert set(ids) in closed_subsets
        assert all(closed(sub) == all(deps[k] <= sub for k in sub) for sub in subsets)
        assert any(not closed(sub) for sub in subsets), 'expected at least one dependency-invalid subset'
        checks=0
        for allowed in subsets:
            a=forward(set(),allowed)
            b=downward(set(allowed))
            assert a==b,(a,b)
            assert closed(a)
            checks+=1
        # Every single and double revocation compared against real ledger.
        # Sequential authoritative revocations are applied only to copies.
        scenarios=0;incremental_touches=0;full_touches=0
        for count in (1,2):
            for removed in itertools.combinations(ids,count):
                keep=set(ids)-set(removed)
                oracle=downward(keep)
                affected=set(ids)-oracle
                shadow=EvidenceStore(Path(td)/(str(scenarios)+".sqlite"))
                for event in store.events():shadow.append(event)
                for k in removed:
                    if k in shadow.state()["capabilities"]:
                        shadow.revoke(k,"major exact scenario")
                assert set(shadow.state()["capabilities"])==oracle
                shadow.close()
                scenarios+=1
                incremental_touches+=len(affected)
                full_touches+=len(ids)
        # Strong controls: no gain over exact replay of full executable state.
        store.close()
        store=EvidenceStore(path)
        before=[new.adapter.assess(store.state(),obl(t,0)).verdict for t in FUTURES]
        assert len(before)==16 and all(v=="verified" for v in before)
        store.close()
        print(json.dumps({
          "schema":"metalogic.flash.whole-future-major-stress.v1",
          "status":"PASS_EXACT_REAL_LEDGER_STRESS",
          "real_capabilities":len(ids),"real_dependency_edges":sum(map(len,deps.values())),
          "all_capability_subsets":checks,"dependency_closed_subsets":len(closed_subsets),
          "single_and_pair_revocation_scenarios":scenarios,
          "incremental_affected_node_visits":incremental_touches,
          "full_graph_node_visits":full_touches,
          "node_visit_saving_fraction":round(1-incremental_touches/full_touches,6),
          "protected_source_proofs":len(before),
          "exact_ledger_replay_baseline":"TIES_ON_REACHABILITY",
          "alternative_warranted_constructions":"NOT_ENUMERATED",
          "complete_lifecycle_cost_win":"UNKNOWN",
          "independent_cross_domain_transfer":"UNKNOWN",
          "unrestricted_autonomous_growth":"UNKNOWN",
          "caution":"Node visits are analytical counts, not measured runtime or independent new semantic proof."},sort_keys=True,indent=2))
if __name__=="__main__":main()
