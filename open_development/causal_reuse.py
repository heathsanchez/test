"""Frozen bounded executable-dependency control; no external task novelty claim."""
from copy import deepcopy
import json
from pathlib import Path
import tempfile

from .composition import ProofCompositionAdapter
from .runtime import Developer, EvidenceStore, Obligation


def qualify():
    stages = json.loads((Path(__file__).parent / "examples/proof.json").read_text())["stages"]
    third = {"polynomial": {"1": "1", "3": "-1"}, "domain": ["interval", "0", "1"]}
    fourth = {"polynomial": {"1": "2", "2": "1", "3": "-1"},
              "domain": ["interval", "0", "1"]}
    obligation = lambda target, budget: Obligation("proof-composition", target, budget, "method")
    adapter = ProofCompositionAdapter()
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "state.sqlite"
        store = EvidenceStore(path)
        dev = Developer(store, adapter)
        assert dev.run(obligation(fourth, 0)).verdict == "unknown"
        first = dev.run(obligation(stages[0], 2))
        second = dev.run(obligation(stages[1], 1))
        parent = second.retained[0]
        state = store.state()
        # Inspect proposed O3 before admission: it executes O2 on a new input.
        pending = adapter.assess(state, obligation(third, 0))
        assert pending.verdict == "unknown"
        assert pending.certificate["execution_trace"] == [parent]
        disabled = deepcopy(state)
        disabled["capabilities"][parent]["repair"]["payload"]["body"] = {"op": "fit-square"}
        blocked = adapter.assess(disabled, obligation(third, 1))
        assert blocked.verdict == "unknown"
        assert blocked.residual["class"] == "BOUNDED_PROGRAM_NOT_FOUND"
        learned = dev.run(obligation(third, 1))
        assert first.verdict == second.verdict == learned.verdict == "verified"
        child = learned.retained[0]
        store.close()
        store = EvidenceStore(path)
        warm = Developer(store, adapter).run(obligation(fourth, 0))
        assert warm.verdict == "verified" and not warm.retained
        assert warm.evidence.certificate["execution_trace"] == [child, parent]
        state = store.state()
        poly, domain = adapter._problem(obligation(fourth, 0))
        assert adapter.execute(state, child, poly, domain) is not None

        # Surgical evaluator interventions, NOT ledger edits or valid admissions.
        # IDs, statuses, contracts, and dependency lists remain unchanged.
        sham = deepcopy(state)
        sham["capabilities"][parent]["repair"]["payload"]["body"] = {"op": "fit-square"}
        assert adapter.execute(sham, child, poly, domain) is None
        assert adapter.assess(sham, obligation(fourth, 0)).verdict == "unknown"
        missing_body = deepcopy(state)
        del missing_body["capabilities"][parent]["repair"]["payload"]["body"]
        assert adapter.execute(missing_body, child, poly, domain) is None
        # Removing an unrelated ray program must NOT break the interval chain.
        unrelated = deepcopy(state)
        del unrelated["capabilities"][first.retained[1]]
        assert adapter.execute(unrelated, child, poly, domain) is not None
        assert adapter.execute(state, child, poly, domain) is not None  # restoration
        removed = store.revoke(parent, "executable parent ablation")
        assert set(removed) == {parent, child}
        assert Developer(store, adapter).run(obligation(fourth, 0)).verdict == "unknown"
        assert any(e["type"] == "admit" and e["record"]["id"] == parent for e in store.events())
        store.close()
        return {"claim": "retained procedure body is a causal execution dependency",
                "verifier": adapter.verifier_id, "restart": True,
                "warm": "verified", "acquisition_budget": 0,
                "execution_trace": warm.evidence.certificate["execution_trace"],
                "sham_body": "unknown", "missing_body": "unknown",
                "unrelated_removal": "verified", "restored_body": "verified",
                "exact_revocation": "unknown", "history_preserved": True,
                "limits": ["supplied finite instruction set and designed polynomial tasks",
                           "zero acquisition budget is not zero execution cost",
                           "exact rational replay; Python interpreter not Lean-verified",
                           "not independently authored prospective exaptation"]}


if __name__ == "__main__":
    print(json.dumps(qualify(), indent=2))
