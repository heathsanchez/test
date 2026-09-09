"""Strict control qualification for the already-preregistered exaptation workload.

This does not introduce a new task or controller.  It reuses the workload frozen
at parent 17057ab3 and the same Developer/EvidenceStore transition, while
hardening the residual envelope, same-size sham, matched fixed-policy baseline,
and developmental-cost accounting required by the completion protocol.
"""
from __future__ import annotations

from copy import deepcopy
from dataclasses import asdict
from hashlib import sha256
import json
from pathlib import Path
import tempfile
from typing import Any, Mapping

from .composition import ProofCompositionAdapter
from .exaptation import (
    ExaptationAdapter,
    _assert_workload_has_no_answer,
    _direct_equivalence,
    _problem,
    _source_fingerprint,
)
from .residual import ResidualEnvelope
from .runtime import (
    Developer,
    Evidence,
    EvidenceStore,
    Obligation,
    Repair,
    canonical,
    digest,
)

PARENT_CHECKPOINT = "17057ab3667bbc2296a8307cd9e125f863e8deb4"
WORKLOAD = Path(__file__).parent / "examples" / "exaptation_workload.json"


class StrictExaptationAdapter(ExaptationAdapter):
    """Same exaptation semantics with a shared typed residual and optional fixed policy."""

    def __init__(self, *, allow_requalification: bool = True):
        super().__init__()
        base = self.verifier_id
        self.allow_requalification = allow_requalification
        self.verifier_id = "prospective-exaptation-strict-v1:" + digest({
            "base_verifier": base,
            "strict_source": sha256(Path(__file__).read_bytes()).hexdigest(),
            "allow_requalification": allow_requalification,
        })

    def assess(self, state: Mapping[str, Any], obligation: Obligation) -> Evidence:
        evidence = super().assess(state, obligation)
        residual = evidence.residual
        if (evidence.verdict == "unknown" and isinstance(residual, Mapping)
                and residual.get("class") == "ROLE_REQUALIFICATION_REQUIRED"):
            constraint = residual["constraint"]
            source = residual["source"]
            envelope = ResidualEnvelope(
                residual_class="ROLE_REQUALIFICATION_REQUIRED",
                diagnosis="capability_failure",
                verifier_certified_witness=deepcopy(evidence.certificate),
                closure_id=digest({
                    "scope": self.name,
                    "active": sorted(state["capabilities"]),
                }),
                budget_id=digest({
                    "budget": obligation.budget,
                    "kind": obligation.kind,
                    "domain": obligation.domain,
                }),
                necessary_constraint=deepcopy(constraint),
                version_space_id=digest({
                    "source": source,
                    "candidate_role": "requalify-affine-factors",
                }),
                evidence_strength="replay-certified",
                domain_payload={"class": "ROLE_REQUALIFICATION_REQUIRED"},
                source=source,
                source_fingerprint=residual["source_fingerprint"],
                constraint=deepcopy(constraint),
            ).to_mapping()
            return Evidence(evidence.verdict, evidence.claim, self.verifier_id,
                            deepcopy(evidence.certificate), envelope, self.name,
                            deepcopy(evidence.cost))
        return evidence

    def propose(self, state: Mapping[str, Any], obligation: Obligation, residual: Any):
        if (isinstance(residual, Mapping)
                and residual.get("class") == "ROLE_REQUALIFICATION_REQUIRED"
                and not self.allow_requalification):
            return
        yield from super().propose(state, obligation, residual)


def _acquire_source(store: EvidenceStore, proof_stages):
    source_adapter = ProofCompositionAdapter()
    dev = Developer(store, source_adapter)
    first = dev.run(Obligation("proof-composition", proof_stages[0], 2, "method"))
    second = dev.run(Obligation("proof-composition", proof_stages[1], 1, "method"))
    assert first.verdict == second.verdict == "verified"
    assert len(second.retained) == 1
    return source_adapter, first, second, second.retained[0]


def _matched_fixed_policy(proof_stages, train):
    with tempfile.TemporaryDirectory() as tmp:
        store = EvidenceStore(Path(tmp) / "fixed.sqlite")
        _, _, _, source = _acquire_source(store, proof_stages)
        adapter = StrictExaptationAdapter(allow_requalification=False)
        obligation = Obligation(adapter.name, train, 2, "method")
        result = Developer(store, adapter).run(obligation)
        assert result.verdict == "unknown"
        assert result.evidence.residual["type"] == "ResidualEnvelope/v1"
        out = {
            "K_A": source,
            "B_acquisition_budget": 2,
            "verdict": result.verdict,
            "residual_type": result.evidence.residual["type"],
            "policy": "requalification-disabled",
        }
        store.close()
        return out


def _typed_cost(adapter: StrictExaptationAdapter, state, recovery_admissions: int):
    construction = int(adapter.metrics["construction"])
    verification = int(adapter.metrics["verification"])
    activation = int(adapter.metrics["activation"])
    execution = int(adapter.metrics["execution"])
    memory_records = sum(
        rec["repair"]["scope"] == adapter.name for rec in state["capabilities"].values())
    scalar = construction + verification + activation + execution + memory_records + recovery_admissions
    return {
        "C_construction": construction,
        "C_verification": verification,
        "C_activation": activation,
        "C_execution": execution,
        "C_memory": memory_records,
        "C_recovery": recovery_admissions,
        "C_total": scalar,
        "identity": "C_total=C_construction+C_verification+C_activation+C_execution+C_memory+C_recovery",
        "unit": "counted verifier/development/execution events or active exaptation records",
        "active_state_bytes": len(canonical(state).encode()),
        "wall_clock_excluded": True,
    }


def qualify_strict():
    proof_stages = json.loads((Path(__file__).parent / "examples/proof.json").read_text())["stages"]
    workload_bytes = WORKLOAD.read_bytes()
    workload_sha = sha256(workload_bytes).hexdigest()
    workload = json.loads(workload_bytes)
    _assert_workload_has_no_answer(workload)
    train, heldout = workload["train"], workload["heldout"]

    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "strict-exaptation.sqlite"
        store = EvidenceStore(path)
        source_adapter, source_first, source_second, source = _acquire_source(store, proof_stages)
        frozen_source = deepcopy(store.state()["capabilities"][source])
        frozen_fingerprint = _source_fingerprint(frozen_source)
        frozen_digest = digest({
            "id": source,
            "repair": frozen_source["repair"],
            "verifier": frozen_source["evidence"]["verifier"],
            "attachment": frozen_source["attachment"],
            "status": frozen_source["status"],
        })

        adapter = StrictExaptationAdapter()
        obligation = lambda target, budget: Obligation(adapter.name, target, budget, "method")

        cold = Developer(store, adapter).run(obligation(train, 0))
        assert cold.verdict == "unknown"
        residual = cold.evidence.residual
        parsed = ResidualEnvelope.from_mapping(residual)
        assert parsed.diagnosis == "capability_failure"
        assert parsed.evidence_strength == "replay-certified"
        assert parsed.necessary_constraint == parsed.constraint

        real = next(adapter.propose(store.state(), obligation(train, 2), residual))
        sham_payload = deepcopy(real.payload)
        sham_payload["body"]["op"] = "requalify-affine-factorS"
        sham = Repair(real.kind, real.name, sham_payload, real.scope,
                      real.dependencies, real.contract)
        assert len(canonical(asdict(sham))) == len(canonical(asdict(real)))
        sham_evidence = adapter.verify(store.state(), obligation(train, 2), sham)
        assert sham_evidence.verdict == "refuted"

        developed = Developer(store, adapter).run(obligation(train, 2))
        assert developed.verdict == "verified" and len(developed.retained) == 2
        role, child = developed.retained
        state = store.state()
        assert _source_fingerprint(state["capabilities"][source]) == frozen_fingerprint
        assert state["capabilities"][role]["repair"]["dependencies"] == [source]
        assert state["capabilities"][child]["repair"]["dependencies"] == [role]

        store.close()
        store = EvidenceStore(path)
        adapter = StrictExaptationAdapter()
        heldout_result = Developer(store, adapter).run(obligation(heldout, 0))
        assert heldout_result.verdict == "verified" and not heldout_result.retained
        trace = heldout_result.evidence.certificate["execution_trace"]
        assert trace == [child, role, source]

        same_class, observations, direct_hash = _direct_equivalence(
            adapter, store.state(), source, [train, heldout])
        assert same_class

        wrong = Repair(
            "capability", "wrong-direction-role",
            {"role": "affine-factor-pair", "source_fingerprint": frozen_fingerprint,
             "body": {"op": "reverse-call", "callee": source}},
            adapter.name, (source,), adapter.role_contract)
        wrong_evidence = adapter.verify(store.state(), obligation(train, 2), wrong)
        assert wrong_evidence.verdict == "refuted"

        live = store.state()
        missing_body = deepcopy(live)
        del missing_body["capabilities"][source]["repair"]["payload"]["body"]
        missing = adapter.assess(missing_body, obligation(heldout, 0))
        assert missing.verdict == "unknown"

        unrelated = deepcopy(live)
        unrelated_id = source_first.retained[1]
        assert unrelated_id not in {source, role, child}
        del unrelated["capabilities"][unrelated_id]
        poly, domain = _problem(heldout)
        assert adapter.execute_program(unrelated, child, poly, domain, []) is not None
        unrelated_verdict = "verified"

        removed = set(store.revoke(source, "strict exaptation ancestor ablation"))
        assert {source, role, child} <= removed
        raw_history = Developer(store, adapter).run(obligation(train, 2))
        assert raw_history.verdict == "unknown"
        assert any(e["type"] == "admit" and e["record"]["id"] == source for e in store.events())

        before_restore = dict(adapter.metrics)
        restored_source = Developer(store, source_adapter).run(
            Obligation("proof-composition", proof_stages[1], 1, "method"))
        assert restored_source.verdict == "verified" and restored_source.retained == (source,)
        restored = Developer(store, adapter).run(obligation(train, 2))
        assert restored.verdict == "verified" and restored.retained == (role, child)
        restored_heldout = Developer(store, adapter).run(obligation(heldout, 0))
        assert restored_heldout.verdict == "verified"
        recovery_admissions = 3
        recovery_metric_delta = {
            k: adapter.metrics[k] - before_restore[k] for k in before_restore
        }

        fixed = _matched_fixed_policy(proof_stages, train)
        assert fixed["verdict"] == "unknown" and fixed["B_acquisition_budget"] == 2

        final_state = store.state()
        assert _source_fingerprint(final_state["capabilities"][source]) == frozen_fingerprint
        costs = _typed_cost(adapter, final_state, recovery_admissions)

        result = {
            "outcome": "VERIFIED_EXAPTATION_STRICT",
            "parent_checkpoint": PARENT_CHECKPOINT,
            "workload_sha256": workload_sha,
            "workload_was_frozen_in_parent_commit": True,
            "workload_contains_no_encoded_answer": True,
            "classification": {"reuse": False, "exaptation": True, "expansion": False},
            "A": {
                "K_A": source,
                "frozen_fingerprint": frozen_fingerprint,
                "frozen_digest": frozen_digest,
                "original_scope": frozen_source["repair"]["scope"],
                "original_contract": frozen_source["repair"]["contract"],
                "original_verifier": frozen_source["evidence"]["verifier"],
            },
            "B": {
                "cold": cold.verdict,
                "typed_residual": residual,
                "B_acquisition_budget": 2,
                "warm": developed.verdict,
                "K_B": role,
                "K_B_dependency": source,
                "K_C": child,
                "K_C_dependency": role,
            },
            "heldout": {
                "acquisition_budget": 0,
                "verdict": heldout_result.verdict,
                "execution_trace": trace,
            },
            "behavioral_identity": {
                "source_distinct_implementation": "direct-vieta-factor-program",
                "source_hash": direct_hash,
                "same_behavioral_class": same_class,
                "protected_observations": observations,
                "not_available_to_developer": True,
            },
            "controls": {
                "same_size_sham_K_B": sham_evidence.verdict,
                "same_size_serialized_bytes": len(canonical(asdict(real))),
                "wrong_direction_adapter": wrong_evidence.verdict,
                "missing_K_A_executable_body": missing.verdict,
                "unrelated_removal": unrelated_verdict,
                "raw_history_reconstruction_same_B_budget": raw_history.verdict,
                "fixed_policy_matched_B_budget": fixed,
                "restored_lineage": restored_heldout.verdict,
            },
            "revocation": {
                "removed": sorted(removed),
                "history_preserved": True,
                "restored_same_K_A_identity": restored_source.retained == (source,),
                "recovery_metric_delta": recovery_metric_delta,
            },
            "developmental_cost": costs,
            "limits": [
                "workload is repository-preregistered in the parent commit but not independently administered",
                "finite supplied proof-program and role languages",
                "protected behavioral equivalence is bounded to the frozen train and held-out observations",
                "Python execution is not Lean-verified; existing proof-program Lean semantics remain separate authority",
                "zero acquisition budget is not zero execution cost",
                "does not decide metaphysical discovery versus creation",
            ],
        }
        store.close()
        return result


if __name__ == "__main__":
    print(json.dumps(qualify_strict(), indent=2, sort_keys=True))
