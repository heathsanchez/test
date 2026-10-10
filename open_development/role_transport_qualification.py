"""Exact bounded cross-authority role-transport and additional-generation test."""
from __future__ import annotations

from collections import Counter
from copy import deepcopy
from dataclasses import asdict
from hashlib import sha256
import json
from pathlib import Path
import tempfile

from .composition import ProofCompositionAdapter, check_program, program_shape
from .mda_v7 import MinimalContinuation
from .role_transport import QualifiedRoleLiftAdapter, ORIGINAL_VERIFIER
from .runtime import EvidenceStore, Obligation, digest

ROOT=Path(__file__).parent
BASE=json.loads((ROOT/"examples/proof.json").read_text())["stages"]
SOURCE_THIRD={"polynomial":{"1":"1","3":"-1"},"domain":["interval","0","1"]}
NEXT={"polynomial":{"2":"1","4":"-1"},"domain":["interval","0","1"]}
AFTER={"polynomial":{"3":"1","5":"-1"},"domain":["interval","0","1"]}
FUTURES=tuple({"polynomial":{"3":str(a*b),"4":str(b-a),"5":"-1"},
               "domain":["interval","0","1"]}
              for a in range(2,6) for b in range(2,6))


def obl(t,budget=0):
    return Obligation("proof-composition",t,budget,"method")


def main():
    assert len(FUTURES)==len({digest(x) for x in FUTURES})==16
    with tempfile.TemporaryDirectory() as tmp:
        store=EvidenceStore(Path(tmp)/"lineage.sqlite")
        original=ProofCompositionAdapter()
        old=MinimalContinuation(store,original)
        entries=[]
        for target,budget in zip((BASE[0],BASE[1],SOURCE_THIRD),(2,1,1)):
            result=old.run_minimal(obl(target,budget))
            assert result.outcome=="COMMIT",result
            entries.append(result)
        ancestor=entries[2].retained[0]
        assert store.state()["capabilities"][ancestor]["evidence"]["verifier"]==ORIGINAL_VERIFIER

        # No hidden promotion: the original creator *can interpret* a nested
        # certificate but its bounded proposer cannot produce one here.
        baseline=old.run_minimal(obl(NEXT,2))
        assert baseline.outcome=="UNKNOWN_SEARCH" and not baseline.retained,baseline
        baseline_residual=original.assess(store.state(),obl(NEXT,0)).residual
        assert baseline_residual["class"]=="BOUNDED_PROGRAM_NOT_FOUND"

        # The typed role must be present and valid. Without source O3 a new
        # verifier may not pretend it discovered the prior developmental law.
        incomplete=deepcopy(store.state())
        incomplete["capabilities"].pop(ancestor)
        replacement=QualifiedRoleLiftAdapter()
        assert not replacement._source_role(incomplete)
        unsupported=replacement.assess(incomplete,obl(NEXT,0))
        assert unsupported.verdict=="unknown"
        no_authority=deepcopy(store.state())
        no_authority["capabilities"][ancestor]["evidence"]["verifier"]="forged-source"
        assert not replacement._source_role(no_authority)

        # Requalification does not mutate predecessor bytes/verifier identity.
        frozen=digest(store.state())
        eligible=replacement.assess(store.state(),obl(NEXT,0))
        assert eligible.verdict=="unknown"
        assert eligible.residual["class"]=="PROGRAM_CONSTRUCTED"
        effective=MinimalContinuation(store,replacement)
        acquired=effective.run_minimal(obl(NEXT,1),
            protected=(obl(SOURCE_THIRD,0),))
        assert acquired.outcome=="COMMIT" and len(acquired.retained)==1,acquired
        parent=acquired.retained[0]
        assert store.state()["capabilities"][parent]["repair"]["dependencies"]==[ancestor]
        assert store.state()["capabilities"][ancestor]["evidence"]["verifier"]==ORIGINAL_VERIFIER
        assert frozen!=digest(store.state())

        after=effective.run_minimal(obl(AFTER,1),
            protected=(obl(SOURCE_THIRD,0),obl(NEXT,0)))
        assert after.outcome=="COMMIT" and len(after.retained)==1,after
        descendant=after.retained[0]
        assert store.state()["capabilities"][descendant]["repair"]["dependencies"]==[parent]

        old_scope=original.assess(store.state(),obl(AFTER,0))
        assert old_scope.verdict=="unknown","source authority cannot silently see successor proofs"

        # Restart is the operative persistence boundary.
        store.close()
        store=EvidenceStore(Path(tmp)/"lineage.sqlite")
        effective=MinimalContinuation(store,QualifiedRoleLiftAdapter())
        successful=[]
        for target in FUTURES:
            decision=effective.run_minimal(obl(target,0))
            assert decision.outcome=="IDENTITY" and decision.verdict=="verified",decision
            successful.append(decision.verdict)
        assert len(store.state()["capabilities"])==6

        # Surgical executable-source ablation is not ledger forgery. Body
        # invalidation breaks all dependent executions and is not bypassed by
        # apparently valid dependency metadata.
        live=store.state()
        surgery=deepcopy(live)
        del surgery["capabilities"][ancestor]["repair"]["payload"]["body"]
        body_loss=[QualifiedRoleLiftAdapter().assess(surgery,obl(q)).verdict for q in FUTURES]
        assert all(v=="unknown" for v in body_loss)
        unrelated=deepcopy(live)
        independent=entries[0].retained[1]
        assert independent not in {ancestor,parent,descendant}
        del unrelated["capabilities"][independent]
        still=[QualifiedRoleLiftAdapter().assess(unrelated,obl(q)).verdict for q in FUTURES]
        assert all(v=="verified" for v in still)

        removed=store.revoke(ancestor,"source role causal ablation")
        assert {ancestor,parent,descendant}.issubset(removed)
        unavailable=[effective.run_minimal(obl(q,0)).verdict for q in FUTURES]
        assert all(v=="unknown" for v in unavailable)
        state=store.state()
        assert entries[1].retained[0] in state["capabilities"]
        assert entries[0].retained[0] in state["capabilities"]
        store.close()

        gates={
            "old_search_residual_not_expressivity_claim":
                baseline.outcome=="UNKNOWN_SEARCH" and baseline_residual["class"]=="BOUNDED_PROGRAM_NOT_FOUND",
            "old_source_required":not replacement._source_role(incomplete),
            "forged_authority_rejected":not replacement._source_role(no_authority),
            "new_authority_distinct":replacement.verifier_id!=ORIGINAL_VERIFIER,
            "two_new_generations":acquired.outcome==after.outcome=="COMMIT",
            "dependency_chain":True,
            "six_total_live_capabilities_before_ablation":len(live["capabilities"])==6,
            "future_16_16":len(successful)==16,
            "body_ablation_16_unknown":all(v=="unknown" for v in body_loss),
            "unrelated_removal_16_verified":all(v=="verified" for v in still),
            "ancestor_revocation_cascades":{ancestor,parent,descendant}.issubset(removed),
            "revocation_16_unknown":all(v=="unknown" for v in unavailable),
            "original_old_verifier_preserved":True
        }
        assert all(gates.values())
        report={
            "schema":"metalogic.mda-v7.role-transport.v1",
            "source_core_commit":"003e6ccfa91205a1f0ea408656c10b8afbdb10c4",
            "role_origin_verifier":ORIGINAL_VERIFIER,
            "role_successor_verifier":replacement.verifier_id,
            "qualified_source_role":ancestor,
            "new_capabilities":[parent,descendant],
            "old_residual":baseline_residual,
            "outcomes":{"old_program_builder":baseline.outcome,
                        "requalified_generation_4":acquired.outcome,
                        "requalified_generation_5":after.outcome,
                        "protected_future_verdict_counts":dict(Counter(successful)),
                        "source_body_ablation":dict(Counter(body_loss)),
                        "unrelated_ablation":dict(Counter(still)),
                        "ancestor_revocation":dict(Counter(unavailable))},
            "cost_event_counts":{"new_candidate_attempts":acquired.proposal_checks+after.proposal_checks,
                                 "new_independent_verifications":acquired.verifier_checks+after.verifier_checks,
                                 "new_replayed_proof_checks":acquired.replay_checks+after.replay_checks},
            "gates":gates,
            "claims":{
                "typed_requalification_of_retained_lift_role":"WARRANTED_BOUNDED_RUNTIME",
                "two_additional_dependent_capability_generations":"WARRANTED_BOUNDED_RUNTIME",
                "new_grammar_invented":"NOT_CLAIMED",
                "general_CLC_transport_theorem":"UNKNOWN",
                "autonomous_general_generator_invention":"UNKNOWN",
                "long_horizon_recursive_economic_acceleration":"UNKNOWN"},
            "limits":[
                "same mathematical problem and shared interpreter, not independent natural domain",
                "cross-verifier transport is runtime checked on declared source lineage, not a formal general CLC proof",
                "extension was proposed by developer after inspecting exact residual, not autonomously generated by MDA",
                "complete grammar inadequacy was NOT proved; selected repair is of candidate search/requalification",
                "16 authored polynomial coefficient variants are not independent challenge submissions",
                "candidate count excludes interpreter work, source discovery, integration and CI cost"
            ]}
        print(json.dumps(report,sort_keys=True,indent=2))


if __name__=="__main__":
    main()
