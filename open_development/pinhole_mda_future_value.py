"""Source-exact MDA future-value separator.

Tests whether the *same current observation interface* can hide distinct
future capability reachability. No claim of total lifecycle optimality.
"""
from __future__ import annotations
from copy import deepcopy
import json,tempfile
from pathlib import Path
from .runtime import EvidenceStore
from .composition import ProofCompositionAdapter
from .mda_v7 import MinimalContinuation
from .role_transport import QualifiedRoleLiftAdapter
from .role_transport_qualification import BASE,SOURCE_THIRD,NEXT,AFTER,FUTURES,obl

def main():
    with tempfile.TemporaryDirectory() as td:
        store=EvidenceStore(Path(td)/'source.sqlite')
        old=MinimalContinuation(store,ProofCompositionAdapter())
        entries=[]
        for target,budget in zip((BASE[0],BASE[1],SOURCE_THIRD),(2,1,1)):
            d=old.run_minimal(obl(target,budget));assert d.outcome=='COMMIT'
            entries.append(d)
        adapter=QualifiedRoleLiftAdapter()
        dev=MinimalContinuation(store,adapter)
        for target in (NEXT,AFTER):
            assert dev.run_minimal(obl(target,1)).outcome=='COMMIT'
        full=store.state()
        parent=entries[2].retained[0]
        broken=deepcopy(full)
        del broken['capabilities'][parent]['repair']['payload']['body']
        assert full['observations']==broken['observations']
        assert full['policies']==broken['policies']
        # Do not use the hash of the whole state as 'present observation':
        # the evidence body is precisely what this intentionally coarse
        # present-only observation does not expose.
        full_v=[adapter.assess(full,obl(t,0)).verdict for t in FUTURES]
        broken_v=[adapter.assess(broken,obl(t,0)).verdict for t in FUTURES]
        assert len(full_v)==len(broken_v)==16
        assert all(v=='verified' for v in full_v)
        assert all(v=='unknown' for v in broken_v)
        # The damaged state is an *ablation probe*, never an admitted ledger.
        # Full authoritative revocation must cascade instead of allowing a
        # stale descendant to remain apparently certified.
        removed=set(store.revoke(parent,'future reachability causal ablation'))
        assert len(removed)>=3
        after=store.state()
        after_v=[adapter.assess(after,obl(t,0)).verdict for t in FUTURES]
        assert all(v=='unknown' for v in after_v)
        store.close()
    print(json.dumps({
       'status':'PASS_SOURCE_EXACT_FUTURE_REACHABILITY_SEPARATOR',
       'same_present_observation_interface':True,
       'protected_goals':16,
       'before_verified':full_v.count('verified'),
       'body_ablated_unknown':broken_v.count('unknown'),
       'ledger_revoked_unknown':after_v.count('unknown'),
       'revoked_capability_count':len(removed),
       'cost_optimality':'UNKNOWN',
       'future_reacquisition_cost':'NOT_MEASURED',
       'independent_proof_semantics':'EXISTING_SOURCE_ADAPTER',
       'limitation':'Coarse present interface intentionally omits executable bodies; no equal-state or physical identity claim.'
    },sort_keys=True,indent=2))
if __name__=='__main__':main()
