"""Source-backed whole-construction ledger census; no synthetic edges.

Executes the existing qualified MDA role-transport workload and instruments
its real source ledger. This is an evidence census, not a four-way optimizer.
"""
from __future__ import annotations
import json, tempfile
from pathlib import Path
from collections import Counter
from .runtime import EvidenceStore, Obligation, digest
from .composition import ProofCompositionAdapter
from .mda_v7 import MinimalContinuation
from .role_transport import QualifiedRoleLiftAdapter
from .role_transport_qualification import BASE, SOURCE_THIRD, NEXT, AFTER, FUTURES, obl

def run():
    with tempfile.TemporaryDirectory() as tmp:
        path=Path(tmp)/"evidence.sqlite"
        store=EvidenceStore(path)
        old=MinimalContinuation(store,ProofCompositionAdapter())
        acquisitions=[]
        for target,budget in zip((BASE[0],BASE[1],SOURCE_THIRD),(2,1,1)):
            result=old.run_minimal(obl(target,budget))
            assert result.outcome=="COMMIT",result
            acquisitions.append(result)
        successor=MinimalContinuation(store,QualifiedRoleLiftAdapter())
        for target in (NEXT,AFTER):
            result=successor.run_minimal(obl(target,1))
            assert result.outcome=="COMMIT",result
            acquisitions.append(result)
        live=store.state()
        caps=live["capabilities"]
        nodes={key:{"dependencies":value["repair"].get("dependencies",[]),
                    "verifier":value["evidence"].get("verifier")}
               for key,value in caps.items()}
        assert len(nodes)==6
        for k,v in nodes.items():
            assert all(parent in nodes for parent in v["dependencies"])
        # Detect cycles and compute exact transitive dependency closure.
        def closure(key,seen=None):
            seen=set() if seen is None else seen
            assert key not in seen,"dependency cycle"
            out=set()
            for p in nodes[key]["dependencies"]:
                out.add(p)
                out.update(closure(p,seen|{key}))
            return out
        ancestors={k:sorted(closure(k)) for k in nodes}
        pre=digest(live)
        store.close()
        store=EvidenceStore(path)
        assert digest(store.state())==pre
        reuse=MinimalContinuation(store,QualifiedRoleLiftAdapter())
        results=[reuse.run_minimal(obl(t,0)) for t in FUTURES]
        assert len(results)==16 and all(x.outcome=="IDENTITY" and x.verdict=="verified" for x in results)
        output={
          "schema":"metalogic.whole-construction.real-ledger-census.v1",
          "status":"CANDIDATE_UNTIL_EXACT_CI",
          "source":"actual MDA v7 EvidenceStore and adapters",
          "capabilities":nodes,"transitive_dependencies":ancestors,
          "live_capability_count":len(nodes),
          "protected_future_verified":len(results),
          "acquisition_proposals":sum(x.proposal_checks for x in acquisitions),
          "acquisition_verifier_calls":sum(x.verifier_checks for x in acquisitions),
          "state_digest":pre,
          "independent_cross_domain_edges":"NOT_ESTABLISHED",
          "whole_graph_optimality":"UNKNOWN",
          "flash_incremental_gain":"UNKNOWN",
          "exact_ledger_replay":"SUPPORTED_BY_ORIGINAL_MDA_QUALIFICATION"
        }
        print(json.dumps(output,sort_keys=True,indent=2))
        store.close()
if __name__=="__main__":run()
