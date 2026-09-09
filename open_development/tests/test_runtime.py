from __future__ import annotations

from dataclasses import asdict
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest

from open_development import Developer, Evidence, EvidenceStore, Obligation, Repair
from open_development.finite import FiniteAdapter
from open_development.runtime import assessment_claim, digest
from open_development.lean_gate import certificate_source


SPEC = json.loads((Path(__file__).resolve().parents[1] / "examples/finite.json").read_text())


class ToyAdapter:
    """A deterministic contract fixture, not an external scientific result."""
    name = "toy"
    verifier_id = "toy-exhaustive-v1"

    def __init__(self):
        self.calls = 0
        self.bad = None

    def assess(self, state, obligation):
        claim = assessment_claim(state, obligation)
        kinds = {r["repair"]["kind"] for r in state["capabilities"].values()}
        needed = "policy" if obligation.kind == "method" else "capability"
        if needed in kinds:
            return Evidence("verified", claim, self.verifier_id, {"witness": needed}, scope=self.name)
        return Evidence("unknown", claim, self.verifier_id, {"exhaustive": True},
                        {"missing": needed}, self.name)

    def propose(self, state, obligation, residual):
        kind = residual["missing"]
        dependencies = tuple(state["policies"].values()) if kind == "capability" else ()
        yield Repair(kind, kind + "-v1", {"operation": kind}, self.name, dependencies)

    def verify(self, state, obligation, repair):
        self.calls += 1
        claim = repair.id
        if self.bad == "claim":
            claim = "wrong"
        verifier = "wrong-verifier" if self.bad == "verifier" else self.verifier_id
        certificate = {"complete": True, "repair": repair.id}
        if self.bad == "replay" and self.calls % 2 == 0:
            certificate["different"] = True
        if self.bad == "unknown":
            return Evidence("unknown", claim, verifier, None, scope=self.name)
        return Evidence("verified", claim, verifier, certificate, scope=self.name)

    def attach(self, state, repair, evidence):
        return {"operation": repair.payload["operation"]}


class RuntimeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / "state.sqlite"
        self.store = EvidenceStore(self.path)

    def tearDown(self):
        self.store.close()
        self.tmp.cleanup()

    def test_finite_acquire_reuse_and_restart(self):
        adapter = FiniteAdapter(SPEC)
        dev = Developer(self.store, adapter)
        first = Obligation("finite", {"task": "first", "actual_world": "1"}, 4)
        result = dev.run(first)
        self.assertEqual(result.verdict, "verified")
        self.assertEqual(len(result.retained), 1)
        self.assertEqual(result.evidence.certificate["trace"][-1]["intervention_id"], "b")
        self.store.close()
        self.store = EvidenceStore(self.path)
        second = dev.__class__(self.store, adapter).run(
            Obligation("finite", {"task": "second", "actual_world": "1"}, 4))
        self.assertEqual(second.verdict, "verified")
        self.assertEqual(second.retained, ())
        self.assertEqual(len(self.store.state()["capabilities"]), 1)
        self.assertEqual(len(self.store.state()["observations"]), 1)

    def test_cold_budget_and_exact_ablation(self):
        adapter = FiniteAdapter(SPEC)
        dev = Developer(self.store, adapter)
        task = Obligation("finite", {"task": "first", "actual_world": "0"}, 1)
        cold = dev.run(Obligation("finite", task.target, 0))
        self.assertEqual(cold.verdict, "unknown")
        self.assertEqual(cold.retained, ())
        warm = dev.run(task)
        self.assertEqual(warm.verdict, "verified")
        self.assertEqual(len(warm.retained), 1)
        self.store.revoke(warm.retained[0], "exact ancestor ablation")
        again = dev.run(Obligation("finite", task.target, 0))
        self.assertEqual(again.verdict, "unknown")
        self.assertEqual(self.store.state()["observations"], [])
        events = self.store.events()
        self.assertTrue(any(e["type"] == "revoke" for e in events))
        self.assertTrue(any(e["type"] == "admit" for e in events))

    def test_same_transition_develops_method_and_object(self):
        adapter = ToyAdapter()
        dev = Developer(self.store, adapter)
        method = dev.run(Obligation("toy", {"task": "improve-selection"}, 2, "method"))
        self.assertEqual(method.verdict, "verified")
        policy_id = method.retained[0]
        self.assertEqual(self.store.state()["policies"]["toy"], policy_id)
        obj = dev.run(Obligation("toy", {"task": "solve"}, 2))
        self.assertEqual(obj.verdict, "verified")
        self.assertEqual(len(obj.retained), 1)
        dependent = self.store.state()["capabilities"][obj.retained[0]]
        self.assertEqual(dependent["repair"]["dependencies"], [policy_id])
        removed = self.store.revoke(policy_id, "policy ablation")
        self.assertEqual(set(removed), {policy_id, obj.retained[0]})
        self.assertEqual(self.store.state()["capabilities"], {})
        self.assertEqual(dev.run(Obligation("toy", {"task": "solve"}, 0)).verdict, "unknown")

    def test_reject_unbound_and_unreplayable_candidates(self):
        for bad in ("claim", "verifier", "replay", "unknown"):
            with self.subTest(bad=bad):
                adapter = ToyAdapter()
                adapter.bad = bad
                result = Developer(self.store, adapter).run(Obligation("toy", {}, 1))
                self.assertEqual(result.verdict, "unknown")
                self.assertEqual(result.retained, ())
                self.assertEqual(self.store.state()["capabilities"], {})

    def test_empty_generator_is_unknown_not_impossibility(self):
        spec = dict(SPEC)
        spec["candidate_probes"] = []
        result = Developer(self.store, FiniteAdapter(spec)).run(
            Obligation("finite", {"task": "first", "actual_world": "1"}, 4))
        self.assertEqual(result.verdict, "unknown")
        self.assertEqual(result.retained, ())
        self.assertEqual(len(self.store.state()["capabilities"]), 0)

    def test_model_identity_blocks_cross_model_reuse(self):
        a = Developer(self.store, FiniteAdapter(SPEC))
        a.run(Obligation("finite", {"task": "first", "actual_world": "1"}, 2))
        changed = json.loads(json.dumps(SPEC))
        changed["probes"]["identity"] = [1, 0, 2]
        b = Developer(self.store, FiniteAdapter(changed))
        result = b.run(Obligation("finite", {"task": "first", "actual_world": "1"}, 0))
        self.assertEqual(result.verdict, "unknown")

    def test_hash_chain_detects_damage(self):
        self.store.append({"type": "assessment", "evidence": {"verdict": "unknown"}})
        self.store.db.execute("UPDATE events SET payload=? WHERE seq=1", ('{"type":"forged"}',))
        self.store.db.commit()
        with self.assertRaises(ValueError):
            self.store.events()
        with self.assertRaises(ValueError):
            self.store.append({"type": "assessment"})
        self.store.close()
        with self.assertRaises(ValueError):
            EvidenceStore(self.path)
        self.store = EvidenceStore(Path(self.tmp.name) / "clean.sqlite")

    def test_budget_and_scope(self):
        dev = Developer(self.store, ToyAdapter())
        with self.assertRaises(ValueError):
            dev.run(Obligation("other", {}, 1))
        with self.assertRaises(ValueError):
            dev.run(Obligation("toy", {}, -1))
        result = dev.run(Obligation("toy", {}, 0))
        self.assertEqual(result.verdict, "unknown")
        self.assertEqual(result.retained, ())

    def test_lean_gate_rejection_is_not_promoted(self):
        class FakeGate:
            verifier_id = "lean-test-gate"
            def verify(self, tables, old, candidate):
                return None
        adapter = FiniteAdapter(SPEC, FakeGate())
        result = Developer(self.store, adapter).run(
            Obligation("finite", {"task": "first", "actual_world": "1"}, 2))
        self.assertEqual(result.verdict, "unknown")
        self.assertEqual(result.retained, ())
        self.assertEqual(self.store.state()["capabilities"], {})

    def test_lean_authority_is_not_interchangeable_with_finite_only(self):
        plain = FiniteAdapter(SPEC)
        result = Developer(self.store, plain).run(
            Obligation("finite", {"task": "first", "actual_world": "1"}, 1))
        self.assertEqual(len(result.retained), 1)
        class FakeGate:
            verifier_id = "lean-test-gate"
            def verify(self, tables, old, candidate):
                return None
        strict = FiniteAdapter(SPEC, FakeGate())
        cold = Developer(self.store, strict).run(
            Obligation("finite", {"task": "first", "actual_world": "1"}, 0))
        self.assertEqual(cold.verdict, "unknown")

    def test_same_repair_can_be_requalified_under_new_authority(self):
        plain = FiniteAdapter(SPEC)
        old = Developer(self.store, plain).run(
            Obligation("finite", {"task": "first", "actual_world": "1"}, 1))
        class AcceptingGate:
            verifier_id = "rotated-lean-test-gate"
            def verify(self, tables, old, candidate):
                return {"authority": self.verifier_id, "candidate": candidate}
        strict = FiniteAdapter(SPEC, AcceptingGate())
        new = Developer(self.store, strict).run(
            Obligation("finite", {"task": "first", "actual_world": "1"}, 1))
        self.assertEqual(new.verdict, "verified")
        self.assertEqual(len(new.retained), 1)
        self.assertNotEqual(old.retained[0], new.retained[0])
        records = self.store.state()["capabilities"]
        self.assertEqual(len(records), 2)
        self.assertNotEqual(records[old.retained[0]]["evidence"]["verifier"],
                            records[new.retained[0]]["evidence"]["verifier"])

    def test_canonical_outcomes_and_generated_certificate(self):
        spec = json.loads(json.dumps(SPEC))
        spec["probes"]["identity"] = [False, 0, 1]
        adapter = FiniteAdapter(spec)
        self.assertNotEqual(adapter.domain.probes["identity"][0],
                            adapter.domain.probes["identity"][1])
        source = certificate_source(adapter.domain.probes, ("constant",), "identity")
        self.assertIn("theorem candidate_admitted", source)
        self.assertIn("theorem candidate_refines", source)
        with self.assertRaises(ValueError):
            certificate_source(adapter.domain.probes, (), "missing")

    def test_repair_identity_is_content_addressed(self):
        a = Repair("capability", "x", {"b": 2, "a": 1}, "toy")
        b = Repair("capability", "x", {"a": 1, "b": 2}, "toy")
        self.assertEqual(a.id, b.id)
        with self.assertRaises(ValueError):
            Repair("arbitrary", "x", {}, "toy")


if __name__ == "__main__":
    unittest.main()
