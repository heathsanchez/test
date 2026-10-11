"""Exact dependency closure and revocation replay on real MDA capabilities.

This is a structural Flash gate, NOT a global cost optimiser.
"""
from __future__ import annotations
import json,tempfile
from pathlib import Path
from .runtime import EvidenceStore,digest
from .composition import ProofCompositionAdapter
from .mda_v7 import MinimalContinuation
from .role_transport import QualifiedRoleLiftAdapter
from .role_transport_qualification import BASE,SOURCE_THIRD,NEXT,AFTER,FUTURES,obl

def main():
    with tempfile.TemporaryDirectory() as tmp:
        store=EvidenceStore(Path(tmp)/"graph.sqlite")
        old=MinimalContinuation(store,ProofCompositionAdapter())
        for target,budget in zip((BASE[0],BASE[1],SOURCE_THIRD),(2,1,1)):
            assert old.run_minimal(obl(target,budget)).outcome=="COMMIT"
        new=MinimalContinuation(store,QualifiedRoleLiftAdapter())
        for target in (NEXT,AFTER):
            assert new.run_minimal(obl(target,1)).outcome=="COMMIT"
        live=store.state()
        nodes={k:tuple(v["repair"]["dependencies"]) for k,v in live["capabilities"].items()}
        assert len(nodes)==6
        def descendants(root):
            found={root}
            while True:
                expanded=found|{k for k,parents in nodes.items() if set(parents)&found}
                if expanded==found:return found
                found=expanded
        closure={k:sorted(descendants(k)) for k in nodes}
        # A Flash-style incremental invalidation index is exact iff it
        # matches the existing ledger's authoritative cascade on every node.
        for key in nodes:
            shadow=EvidenceStore(Path(tmp)/(key+".sqlite"))
            for event in store.events():shadow.append(event)
            removed=set(shadow.revoke(key,"structural shadow ablation"))
            assert removed==set(closure[key]),(key,removed,closure[key])
            assert not removed & set(shadow.state()["capabilities"])
            shadow.close()
        # Existing original authority is the semantic arbiter: the
        # final-source ancestor must be required for protected future proofs.
        last=new.run_minimal(obl(FUTURES[0],0))
        assert last.outcome=="IDENTITY" and last.verdict=="verified"
        report={"schema":"metalogic.flash.real-ledger-reclosure.v1",
          "status":"CANDIDATE_UNTIL_CI",
          "nodes":len(nodes),
          "dependency_edges":sum(map(len,nodes.values())),
          "revocation_shadow_checks":len(nodes),
          "all_cascades_exact":True,
          "descendant_counts":{k:len(v) for k,v in closure.items()},
          "protected_future_sample_verified":True,
          "global_optimality":"UNKNOWN",
          "cross_frontier_speedup":"UNKNOWN",
          "alternate_plans":"NOT_ENUMERATED"}
        print(json.dumps(report,indent=2,sort_keys=True))
        store.close()
if __name__=="__main__":main()
