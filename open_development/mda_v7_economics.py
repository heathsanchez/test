"""MDA v7: measured bounded compounding on the actual proof-program adapter.

Three acquisition generations are trained once; a separate frozen
coefficient-distinct set is used only after state/version freeze. Compare:
  PERSIST: retained executable lineage (genesis paid once)
  EPISODIC_RECONSTRUCT: same recorded training experiences, relearn every task
  EXACT_LEDGER_REPLAY: strong memory containing the actual qualified executable
                       state, equivalent to PERSIST in authority and function
and surgical body/ancestor ablations. These are separate memory baselines.
No natural-domain, hardware-normalized, or unbounded recursion claim.
"""
from __future__ import annotations
from collections import Counter
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
import shutil
import tempfile

from .mda_v7 import MinimalContinuation
from .composition import ProofCompositionAdapter
from .finite import FiniteAdapter
from .runtime import EvidenceStore, Obligation, canonical, digest

ROOT = Path(__file__).resolve().parent
STAGES = json.loads((ROOT / "examples/proof.json").read_text())["stages"]
FINITE = json.loads((ROOT / "examples/finite.json").read_text())
THIRD = {"polynomial":{"1":"1","3":"-1"}, "domain":["interval","0","1"]}
# A×B products are deliberately source-distinct from phase 1/2/3;
# the heldout set is declared in code, not chosen by the verifier.
HELDOUT = tuple(
    {"polynomial":{"1":str(a*b),"2":str(b-a),"3":"-1"},
     "domain":["interval","0","1"]}
    for a in range(2,6) for b in range(2,6)
)
SOURCE_CLAIM = "historical bounded proof composition + new MDA minimal continuation"


class Meter:
    """Counts invocations at the existing independent adapter authority."""
    def __init__(self, native):
        self.native = native
        self.name = native.name
        self.verifier_id = native.verifier_id
        self.contract = native.contract
        self.calls = Counter()

    def assess(self, state, obligation):
        self.calls["assess"] += 1
        return self.native.assess(state, obligation)

    def propose(self, state, obligation, residual):
        for repair in self.native.propose(state,obligation,residual):
            self.calls["propose"] += 1
            yield repair

    def verify(self, state, obligation, repair):
        self.calls["verify"] += 1
        return self.native.verify(state,obligation,repair)

    def attach(self, state, repair, evidence):
        self.calls["attach"] += 1
        return self.native.attach(state,repair,evidence)


def obligation(problem,budget):
    return Obligation("proof-composition",problem,budget,"method")


def acquire(store,meter):
    dev=MinimalContinuation(store,meter)
    witness=[]
    for stage,budget in zip((STAGES[0],STAGES[1],THIRD),(2,1,1)):
        result=dev.run_minimal(obligation(stage,budget))
        assert result.outcome=="COMMIT",(stage,result)
        witness.append({
            "problem_sha256":digest(stage), "retained":list(result.retained),
            "verdict":result.verdict, "proposal_checks":result.proposal_checks,
            "independent_verifier_invocations":result.verifier_checks,
            "replayed_proofs":result.replay_checks,
            "admitted_frontier":result.frontier})
    assert [len(w["retained"]) for w in witness]==[2,1,1]
    return witness


def evaluate_all(store,meter):
    dev=MinimalContinuation(store,meter)
    snap_before=digest(store.state())
    rows=[]
    for index,problem in enumerate(HELDOUT):
        status=dev.run_minimal(obligation(problem,0))
        rows.append({"index":index,"problem_sha256":digest(problem),
                     "verdict":status.verdict,"outcome":status.outcome,
                     "retained":list(status.retained)})
    assert all(r["outcome"]=="IDENTITY" and r["verdict"]=="verified"
               and not r["retained"] for r in rows), rows
    assert digest(store.state())==snap_before,"no hidden future re-development allowed"
    return rows


def main():
    assert len(HELDOUT)==len({digest(x) for x in HELDOUT})==16
    with tempfile.TemporaryDirectory() as temp:
        base=Path(temp)
        path=base/"persistent.sqlite"
        meter=Meter(ProofCompositionAdapter())
        store=EvidenceStore(path)
        cold=MinimalContinuation(store,meter).run_minimal(obligation(THIRD,0))
        assert cold.outcome=="UNKNOWN_SEARCH"
        before=dict(meter.calls)
        lineage=acquire(store,meter)
        genesis=dict(meter.calls)
        live=store.state()
        source_2=lineage[1]["retained"][0]
        source_3=lineage[2]["retained"][0]
        assert live["capabilities"][source_3]["repair"]["dependencies"]==[source_2]
        assert source_2 in live["capabilities"]
        snap=digest(live)
        store.close()
        snapshot=base/"frozen_accepted_ledger.sqlite"
        shutil.copyfile(path,snapshot)
        freeze_hash=sha256(snapshot.read_bytes()).hexdigest()

        # A: one persistent developmental life; no training data replay.
        store=EvidenceStore(path)
        persistent_rows=evaluate_all(store,meter)
        persistent_cost=dict(meter.calls)
        store.close()

        # B: the same recorded experiences are available. Without compiled
        # executable state, a bounded episodic agent must reconstruct and
        # requalify the necessary lineage under the identical verifier.
        episodic=Meter(ProofCompositionAdapter())
        episodic_rows=[]
        for index,problem in enumerate(HELDOUT):
            epath=base/f"episodic_{index}.sqlite"
            estate=EvidenceStore(epath)
            recover=acquire(estate,episodic)
            status=MinimalContinuation(estate,episodic).run_minimal(
                obligation(problem,0))
            assert status.outcome=="IDENTITY" and status.verdict=="verified"
            episodic_rows.append({"index":index,
                                  "source_admissions":sum(len(x["retained"]) for x in recover),
                                  "target_verified":True})
            estate.close()

        # C: strongest memory control: exact original accepted executable
        # ledger bytes may be replayed. It is functionally a retained present,
        # regardless of whether called 'memory' or 'development'.
        replay=Meter(ProofCompositionAdapter())
        replay_rows=[]
        for index,problem in enumerate(HELDOUT):
            rpath=base/f"ledger_{index}.sqlite"
            shutil.copyfile(snapshot,rpath)
            checked=EvidenceStore(rpath)
            assert digest(checked.state())==snap
            assert checked.events()
            decision=MinimalContinuation(checked,replay).run_minimal(
                obligation(problem,0))
            assert decision.outcome=="IDENTITY" and decision.verdict=="verified"
            replay_rows.append({"index":index,"verified":True})
            checked.close()

        # The body, not the admission labels or metadata, carries the later
        # behaviour. Surgery on a copy does not forge a ledger admission.
        damaged=deepcopy(live)
        assert damaged["capabilities"][source_2]["repair"]["payload"]["body"]
        del damaged["capabilities"][source_2]["repair"]["payload"]["body"]
        ablated=[meter.native.assess(damaged,obligation(x,0)).verdict for x in HELDOUT]
        assert all(x=="unknown" for x in ablated)
        unrelated=deepcopy(live)
        # The ray program is independent of the O2->O3 interval chain.
        other=lineage[0]["retained"][1]
        assert other not in (source_2,source_3)
        del unrelated["capabilities"][other]
        unrelated_outcomes=[meter.native.assess(unrelated,obligation(x,0)).verdict
                            for x in HELDOUT]
        assert all(x=="verified" for x in unrelated_outcomes)

        # Derive a genuine dual observation-side development on its own source
        # finite-model authority, without hardcoding a route in the MDA kernel.
        fs=EvidenceStore(base/"finite.sqlite")
        ft=Meter(FiniteAdapter(FINITE))
        first=Obligation("finite",{"task":"first","actual_world":"1"},3)
        f_cold=MinimalContinuation(fs,ft).run_minimal(
            Obligation("finite",first.target,0))
        f_new=MinimalContinuation(fs,ft).run_minimal(first)
        f_reuse=MinimalContinuation(fs,ft).run_minimal(
            Obligation("finite",{"task":"first","actual_world":"2"},0))
        assert (f_cold.outcome,f_new.outcome,f_reuse.outcome)==(
            "UNKNOWN_SEARCH","COMMIT","IDENTITY")
        fid=f_new.retained[0]
        fs.revoke(fid,"finite question ancestor ablation")
        f_removed=MinimalContinuation(fs,ft).run_minimal(
            Obligation("finite",{"task":"first","actual_world":"2"},0))
        assert f_removed.outcome=="UNKNOWN_SEARCH"
        fs.close()

        # Result costs are *separate counted event units*, not fabricated
        # equivalent dollars. Charged genesis is retained in persistent.
        aggregate={
            "persistent":persistent_cost,
            "episodic_reconstruction":dict(episodic.calls),
            "exact_executable_ledger_replay":dict(replay.calls),
            "persistent_genesis_only":{k:v-before.get(k,0) for k,v in genesis.items()},
            "finite_question_genesis_and_ablation":dict(ft.calls),
        }
        # Episodic reconstruction cannot be beaten by silently ignoring its
        # cost. But exact executable replay can match zero reacquisition.
        gates={
            "unique_protected_tasks":len(HELDOUT)==16,
            "three_generations_qualified":len(lineage)==3,
            "all_heldout_same_outcomes":len(persistent_rows)==len(episodic_rows)==len(replay_rows)==16,
            "persistent_zero_new_reacquisition":sum(len(r["retained"]) for r in persistent_rows)==0,
            "reconstruction_more_verifier_calls":episodic.calls["verify"]>persistent_cost.get("verify",0),
            "reconstruction_more_proposals":episodic.calls["propose"]>persistent_cost.get("propose",0),
            "exact_ledger_replay_can_match":replay.calls["verify"]==0 and replay.calls["propose"]==0,
            "body_ablation_restores_unknown":all(x=="unknown" for x in ablated),
            "unrelated_ablation_preserves":all(x=="verified" for x in unrelated_outcomes),
            "question_side_development":f_new.outcome=="COMMIT" and f_reuse.outcome=="IDENTITY",
            "question_ablation_restores_unknown":f_removed.outcome=="UNKNOWN_SEARCH",
        }
        result={
            "schema":"metalogic.mda-v7.compounding.v1",
            "source":"heathsanchez/test:open-development-core-v1",
            "source_old_core_commit":"003e6ccfa91205a1f0ea408656c10b8afbdb10c4",
            "source_claim":SOURCE_CLAIM,
            "finite_authority":"exact supplied finite table, NOT external natural-world accuracy",
            "proof_authority":meter.verifier_id,
            "frozen_accepted_ledger_sha256":freeze_hash,
            "frozen_accepted_state_sha256":snap,
            "training_experience_sha256":digest((STAGES[0],STAGES[1],THIRD)),
            "protected_family_manifest_sha256":digest(HELDOUT),
            "protected_family_count":len(HELDOUT),
            "lineage":lineage,"counts":aggregate,
            "strong_memory_equivalence":
                "exactly replayed executable certified ledger achieves same protected outcomes, NOT inferior",
            "ablation":{"dependent_body_removed_outcomes":dict(Counter(ablated)),
                        "unrelated_removed_outcomes":dict(Counter(unrelated_outcomes))},
            "finite_question":{"cold":f_cold.outcome,"acquired":f_new.outcome,
                               "reuse":f_reuse.outcome,"removed":f_removed.outcome},
            "gates":gates,
            "claims":{
                "bounded_persistent_executable_compounding":
                    "WARRANTED_BOUNDED" if all(gates.values()) else "UNKNOWN",
                "outperforms_episodic_reconstruction_in_verifier_calls":
                    "WARRANTED_BOUNDED" if gates["reconstruction_more_verifier_calls"] else "UNKNOWN",
                "strict_improvement_over_full_certificate_replay":
                    "REJECTED_ON_THIS_CASE",
                "development_changes_later_discovery_not_only_reuse":
                    "UNKNOWN",
                "natural_or_unbounded_compounding":
                    "UNKNOWN"
            },
            "limits":[
                "authored finite polynomial family, not prospectively independent real-world tasks",
                "16 coefficient-distinct heldouts share a fixed supplied certificate-program grammar",
                "memory with certified executable state is equivalent to full developmental state on this replay",
                "counted invocation vectors are not dollars or resource-normalized execution time",
                "does not prove generation of genuinely new ontologies or general recursive acceleration",
                "the adapter's Python proof program interpretation is not newly Lean-verified here",
            ]}
        assert all(gates.values()),gates
        print(json.dumps(result,sort_keys=True,indent=2))


if __name__=="__main__":
    main()
