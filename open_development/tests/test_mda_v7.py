"""Regression gates for MDA v7 minimal warranted continuation.

Domain-independent selection logic is tested with adversarial adapters.
The true proof and finite examples use the original externally qualified
Open Development Core realizations, not hard-coded abstract 'success' flags.
"""
from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from open_development.mda_v7 import MinimalContinuation
from open_development.runtime import (
    Evidence, EvidenceStore, Obligation, IRContract, Repair, assessment_claim)
from open_development.composition import ProofCompositionAdapter
from open_development.finite import FiniteAdapter

ROOT = Path(__file__).resolve().parents[1]
STAGES = json.loads((ROOT / "examples/proof.json").read_text())["stages"]
FINITE = json.loads((ROOT / "examples/finite.json").read_text())


class CompetitionAdapter:
    """Two independently checked realizations; choice cannot be made by name."""
    name = "competition"
    contract = IRContract("Obligation", "Candidate", "Verdict",
                          "finite canonical contract", "observed candidate outcome",
                          "Certificate")
    verifier_id = "competition-v1"

    def __init__(self, mode="choice"):
        self.mode = mode
        self.calls = 0

    def assess(self, state, obligation):
        caps = [r["repair"]["payload"] for r in state["capabilities"].values()
                if r["repair"]["scope"] == self.name]
        good = bool(caps)
        if obligation.target == "prior":
            good = not any(r.get("break_prior", False) for r in caps)
        if obligation.target == "pending":
            good = False
        return Evidence("verified" if good else "unknown",
                        assessment_claim(state, obligation),
                        self.verifier_id, {"checked": True},
                        None if good else {"class": "CURRENTLY_UNRESOLVED"},
                        self.name)

    def propose(self, state, obligation, residual):
        if self.mode == "choice":
            values = [{"candidate": "alpha"}, {"candidate": "bravo"}]
        elif self.mode == "dominated":
            values = [{"candidate": "alpha"}, {"candidate": "bravo", "padding": "longer"}]
        elif self.mode == "breaker":
            values = [{"candidate": "alpha", "break_prior": True}]
        else:
            values = []
        for payload in values:
            yield Repair("observation", "proposal", payload, self.name)

    def verify(self, state, obligation, repair):
        self.calls += 1
        return Evidence("verified", repair.id, self.verifier_id,
                        {"verified": True}, scope=self.name)

    def attach(self, state, repair, evidence):
        assert evidence.verdict == "verified"
        return {"payload": repair.payload}


class MDASevenTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / "state.sqlite"
        self.store = EvidenceStore(self.path)

    def tearDown(self):
        self.store.close()
        self.tmp.cleanup()

    def obligation(self, problem, budget):
        return Obligation("proof-composition", problem, budget, "method")

    def test_qualified_three_generation_reuse_after_restart(self):
        adapter = ProofCompositionAdapter()
        dev = MinimalContinuation(self.store, adapter)
        original = self.obligation(STAGES[0], 2)
        initial = dev.run_minimal(original)
        self.assertEqual(initial.outcome, "COMMIT")
        self.assertEqual(initial.verdict, "verified")
        self.assertEqual(len(initial.retained), 2)
        self.assertEqual(initial.proposal_checks, 2)

        stage_two = dev.run_minimal(self.obligation(STAGES[1], 1),
                                    protected=(self.obligation(STAGES[0], 0),))
        self.assertEqual(stage_two.outcome, "COMMIT")
        self.assertEqual(len(stage_two.retained), 1)
        self.assertEqual(len(self.store.state()["capabilities"]), 3)

        third = {"polynomial": {"1": "1", "3": "-1"},
                 "domain": ["interval", "0", "1"]}
        from open_development.mda_v7 import _project
        state_before = self.store.state()
        evidence = adapter.assess(state_before, self.obligation(third, 1))
        child = next(adapter.propose(state_before, self.obligation(third, 1),
                                     evidence.residual))
        attested = adapter.verify(state_before, self.obligation(third, 1), child)
        virtual = _project(state_before, child, attested, adapter)
        child_id = next(reversed(virtual["capabilities"]))
        self.assertEqual(virtual["capabilities"][child_id]["repair"]["dependencies"],
                         [stage_two.retained[0]], "preview must match JSON ledger types")
        self.assertEqual(adapter.assess(virtual, self.obligation(third, 1)).verdict,
                         "verified", "projected executor must preserve dependency semantics")
        self.assertEqual(adapter.assess(virtual, self.obligation(STAGES[1], 0)).verdict,
                         "verified")
        acquire = dev.run_minimal(self.obligation(third, 1),
                                  protected=(self.obligation(STAGES[1], 0),))
        self.assertEqual(acquire.outcome, "COMMIT", repr(acquire))
        self.assertEqual(len(acquire.retained), 1)

        self.store.close()
        self.store = EvidenceStore(self.path)
        dev = MinimalContinuation(self.store, adapter)
        for a in range(2, 6):
            for b in range(2, 6):
                candidate = {"polynomial": {"1": str(a*b), "2": str(b-a), "3": "-1"},
                             "domain": ["interval", "0", "1"]}
                reused = dev.run_minimal(self.obligation(candidate, 0))
                self.assertEqual(reused.outcome, "IDENTITY", (a,b,reused))
                self.assertEqual(reused.verdict, "verified")
                self.assertEqual(reused.retained, ())
        self.assertEqual(len(self.store.state()["capabilities"]), 4)
        self.store.revoke(initial.retained[0], "constructor removal ablation")
        after = dev.run_minimal(self.obligation(third, 0))
        self.assertEqual(after.outcome, "UNKNOWN_SEARCH")

    def test_finite_question_growth_then_reuse(self):
        adapter = FiniteAdapter(FINITE)
        dev = MinimalContinuation(self.store, adapter)
        cold = dev.run_minimal(Obligation("finite", {"task": "first", "actual_world": "1"}, 0))
        self.assertEqual(cold.outcome, "UNKNOWN_SEARCH")
        learned = dev.run_minimal(Obligation("finite", {"task": "first", "actual_world": "1"}, 3))
        self.assertEqual(learned.outcome, "COMMIT")
        self.assertEqual(len(self.store.state()["observations"]), 1)
        held = dev.run_minimal(Obligation("finite", {"task": "first", "actual_world": "2"}, 0))
        self.assertEqual(held.outcome, "IDENTITY")

    def test_incomparable_minima_preserved_as_choice_not_arbitrary_commit(self):
        adapter = CompetitionAdapter("choice")
        r = MinimalContinuation(self.store, adapter).run_minimal(Obligation("competition", "target", 2))
        self.assertEqual(r.outcome, "UNKNOWN_CHOICE")
        self.assertEqual(len(r.frontier), 2)
        self.assertEqual(self.store.state()["capabilities"], {})
        self.assertEqual(adapter.calls, 4)

    def test_dominated_expansion_not_retained(self):
        adapter = CompetitionAdapter("dominated")
        r = MinimalContinuation(self.store, adapter).run_minimal(Obligation("competition", "target", 2))
        self.assertEqual(r.outcome, "COMMIT")
        self.assertEqual(len(r.retained), 1)
        self.assertEqual(self.store.state()["capabilities"][r.retained[0]]["repair"]["payload"],
                         {"candidate": "alpha"})
        already = MinimalContinuation(self.store, adapter).run_minimal(
            Obligation("competition", "target", 0))
        self.assertEqual(already.outcome, "IDENTITY")
        self.assertEqual(already.proposal_checks, 0)

    def test_new_work_cannot_erase_protected_prior_future(self):
        adapter = CompetitionAdapter("breaker")
        r = MinimalContinuation(self.store, adapter).run_minimal(
            Obligation("competition", "target", 1),
            protected=(Obligation("competition", "prior", 0),))
        self.assertEqual(r.outcome, "UNKNOWN_SEARCH")
        self.assertFalse(self.store.state()["capabilities"])

    def test_proposal_budget_is_not_a_completeness_certificate(self):
        adapter = CompetitionAdapter("choice")
        r = MinimalContinuation(self.store, adapter).run_minimal(
            Obligation("competition", "target", 1))
        self.assertEqual(r.outcome, "UNKNOWN_SEARCH")
        self.assertFalse(self.store.state()["capabilities"])

    def test_out_of_grammar_is_unknown_not_license_for_expansion(self):
        adapter = ProofCompositionAdapter()
        goal = {"polynomial": {"0": "-1", "3": "1"}, "domain": ["ray"]}
        r = MinimalContinuation(self.store, adapter).run_minimal(self.obligation(goal, 4))
        self.assertEqual(r.outcome, "UNKNOWN_SEARCH")
        self.assertFalse(r.retained)
        self.assertNotEqual(r.outcome, "OBSTRUCTION")

    def test_replay_cannot_promote_wrong_verifier(self):
        class Forged(CompetitionAdapter):
            def verify(self, state, obligation, repair):
                evidence = super().verify(state, obligation, repair)
                return Evidence("verified", repair.id, "forged-verifier",
                                evidence.certificate, scope=self.name)
        r = MinimalContinuation(self.store, Forged("dominated")).run_minimal(
            Obligation("competition", "target", 2))
        self.assertEqual(r.outcome, "UNKNOWN_SEARCH")
        self.assertEqual(self.store.state()["capabilities"], {})


if __name__ == "__main__":
    unittest.main()
