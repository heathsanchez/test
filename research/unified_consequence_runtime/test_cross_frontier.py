"""Original FLASH projection controls, not new source-native science.

Small receipt fixtures exercise bookkeeping and adversarial admission. The
whole-stack qualification separately supplies actual original native receipts.
"""
from dataclasses import asdict
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from research.unified_consequence_runtime import cross_frontier as cf
from research.unified_consequence_runtime.developmental_machine import Capability, Machine


CONTRACT = {"input_type": "NativeTomlProgramFamily", "output_type": "NativeCoherenceClassification",
            "authority_snapshot": "udm-native-observation-v1",
            "verifier_id": "original-independent-tomllib-audit-v1"}


class _FixtureNativeAdapter:
    """No native result asserted; simulates a domain admission boundary for tests."""
    def __init__(self, machine):
        self.machine = machine

    def validate(self, cap_id):
        if cap_id not in self.machine.mt.live_ids(self.machine.log):
            raise PermissionError("test capability is withdrawn")
        cap = self.machine.descriptor(cap_id)
        self.machine.get(cap.program)
        return cap


class CrossFrontierTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="udm-frontier-projection-test-")
        self.addCleanup(self.temp.cleanup)
        self.state = Path(self.temp.name) / "state"
        self.components = Path(os.environ.get("UDM_COMPONENTS", "/workspace/components"))
        self.evaluator = Path(os.environ.get("UDM_EVALUATOR", "/workspace/repos/webarena-verified"))
        self.config = Path(os.environ.get("UDM_ASSETS", "/workspace/archaeology/depth5-original")) / "config.json"
        self.machine = Machine(self.components, self.state, self.evaluator, self.config)
        self.adapter = _FixtureNativeAdapter(self.machine)
        # These are explicitly fixture-only projection tests. Native science
        # qualification uses the two actual adapters without this substitution.
        patched = patch.object(cf, "_validator_source", return_value=Path(__file__))
        patched.start()
        self.addCleanup(patched.stop)

    def register(self, name, *, profile=None, contract=None):
        return cf.register_frontier(self.machine, name, contract=contract or CONTRACT,
            profile=profile or name, request={"typed_fixture": name})

    def capability(self, generation=1, *, profiles=("tomlkit:B", "tomlkit:C"),
                   operation="flash.native_observation"):
        program = self.machine.put({"fixture_only": True, "generation": generation})
        observation = self.machine.put({"fixture_only": True, "input": "A"})
        receipt = self.machine.put({"fixture_only": True, "independent_native_science": "NOT_CLAIMED"})
        source = self.machine.append("source_support", {"generation": generation, "fixture": True})
        verified = self.machine.append("native_observation_verification",
            {"program": program, "receipt": receipt}, (source,))
        cap = Capability(operation, {"repository": "fixture", "commit": "fixture"},
            {"frontier_contract": CONTRACT, "frontier_profiles": list(profiles)},
            observation, program, generation, (source,), (verified,), "REPRESENTATION_REFINEMENT")
        cap_id = self.machine.append("executable_capability", asdict(cap), (source, verified))
        self.machine.flush()
        return cap_id, verified, source

    def publish(self, cap, verified, **changes):
        args = {"contract": CONTRACT, "profiles": ["tomlkit:B", "tomlkit:C"],
                "verification_id": verified, "validate": self.adapter.validate}
        args.update(changes)
        return cf.publish_frontier_route(self.machine, cap, **args)

    def refresh(self):
        self.machine.frontiers = cf.reclose_frontiers(self.machine)
        return self.machine.frontiers

    def test_one_admitted_event_recloses_two_preexisting_frontiers_only(self):
        self.register("B", profile="tomlkit:B")
        self.register("C", profile="tomlkit:C")
        self.register("unrelated", profile="other-native-family")
        self.register("wrong-authority", profile="tomlkit:B",
                      contract=CONTRACT | {"authority_snapshot": "different"})
        before = self.refresh()
        self.assertTrue(all(row["status"] == "UNKNOWN_SEARCH" for row in before["frontiers"].values()))
        cap, verified, _ = self.capability()
        self.publish(cap, verified)
        after = self.machine.frontiers
        self.assertEqual(after["frontiers"]["B"]["capability_id"], cap)
        self.assertEqual(after["frontiers"]["C"]["capability_id"], cap)
        self.assertEqual(after["changed_frontiers"], ["B", "C"])
        self.assertEqual(after["flash_radius"], 2)
        self.assertEqual(after["frontiers"]["unrelated"], before["frontiers"]["unrelated"])
        self.assertEqual(after["frontiers"]["wrong-authority"], before["frontiers"]["wrong-authority"])

    def test_wrong_contract_and_profile_publications_are_rejected(self):
        self.register("B", profile="tomlkit:B")
        cap, verified, _ = self.capability()
        with self.assertRaisesRegex(ValueError, "contract.*scope"):
            self.publish(cap, verified, contract=CONTRACT | {"verifier_id": "self-certified"})
        with self.assertRaisesRegex(ValueError, "profile.*scope"):
            self.publish(cap, verified, profiles=["unverified-source:D"])
        self.assertEqual(cf.require_frontier_route(self.machine, "B")["status"], "UNKNOWN_SEARCH")
        self.assertFalse(any(node.kind == cf.PUBLICATION for node in self.machine.log))

    def test_ancestor_withdrawal_restore_new_generation_and_unrelated_survival(self):
        for label in ("B", "C"):
            self.register(label, profile="tomlkit:" + label)
        self.register("unrelated", profile="independent")
        old, verified, ancestor = self.capability()
        independent, iv, _ = self.capability(9, profiles=("independent",))
        self.publish(old, verified)
        self.publish(independent, iv, profiles=["independent"])
        self.refresh()
        self.machine.append("revoke", {"target": ancestor, "reason": "exact test ancestor withdrawal"})
        self.machine.flush()
        cut = self.refresh()
        self.assertEqual(cut["frontiers"]["B"]["status"], "UNKNOWN_SEARCH")
        self.assertEqual(cut["frontiers"]["C"]["status"], "UNKNOWN_SEARCH")
        self.assertEqual(cut["frontiers"]["unrelated"]["capability_id"], independent)
        self.assertTrue(any(set(event["reopened"]) == {"B", "C"}
                            for event in cut["original_flash_events"]))
        restored, fresh, _ = self.capability(2)
        self.publish(restored, fresh)
        self.assertNotEqual(restored, old)
        self.assertEqual(cf.require_frontier_route(self.machine, "B")["capability_id"], restored)
        self.assertNotIn(old, self.machine.mt.live_ids(self.machine.log))

    def test_distinct_lawful_candidates_preserve_unknown_choice(self):
        self.register("B", profile="tomlkit:B")
        first, fv, _ = self.capability(1)
        second, sv, _ = self.capability(2)
        self.publish(first, fv)
        self.publish(second, sv)
        choice = cf.require_frontier_route(self.machine, "B")
        self.assertEqual(choice["status"], "UNKNOWN_CHOICE")
        self.assertEqual(set(choice["candidates"]), {first, second})
        self.assertIsNone(choice["capability_id"])
        self.assertEqual(choice["expressivity"], "UNKNOWN")

    def test_missing_or_forged_native_evidence_cannot_publish(self):
        self.register("B", profile="tomlkit:B")
        cap, verified, _ = self.capability()
        wrong = self.machine.append("native_observation_verification",
            {"program": self.machine.put({"different": True}),
             "receipt": self.machine.put({"self_report": True})})
        self.machine.flush()
        with self.assertRaisesRegex(ValueError, "independent native evidence"):
            self.publish(cap, wrong)
        with self.assertRaisesRegex(ValueError, "this machine"):
            self.publish(cap, verified, validate=lambda _: True)
        with self.assertRaises((KeyError, StopIteration, PermissionError)):
            self.publish("missing", verified)

    def test_altered_program_and_receipt_are_rejected(self):
        self.register("B", profile="tomlkit:B")
        cap_id, verified, _ = self.capability()
        cap = self.machine.descriptor(cap_id)
        program = self.machine.state / "objects" / cap.program
        original = program.read_bytes()
        program.write_text('{"forged":true}')
        with self.assertRaisesRegex(ValueError, "changed"):
            self.publish(cap_id, verified)
        program.write_bytes(original)
        receipt_id = next(node for node in self.machine.log if node.id == verified).payload["receipt"]
        (self.machine.state / "objects" / receipt_id).write_text('{"forged":true}')
        with self.assertRaisesRegex(ValueError, "changed"):
            self.publish(cap_id, verified)

    def test_forged_projection_parent_is_rejected_during_reclosure(self):
        self.register("B", profile="tomlkit:B")
        cap, verified, _ = self.capability()
        pub = self.publish(cap, verified)
        payload = next(node.payload for node in self.machine.log if node.id == pub)
        self.machine.append(cf.PUBLICATION, payload, (cap,))
        with self.assertRaisesRegex(ValueError, "causal dependencies"):
            self.machine.flush()

    def test_revocation_during_route_validation_blocks_route(self):
        self.register("B", profile="tomlkit:B")
        cap, verified, ancestor = self.capability()
        self.publish(cap, verified)
        def withdraw(_):
            self.machine.append("revoke", {"target": ancestor, "reason": "between checks"})
            self.machine.flush()
            return True
        with self.assertRaisesRegex(PermissionError, "changed during validation"):
            cf.require_frontier_route(self.machine, "B", validate=withdraw)

    def test_derived_cache_cannot_grant_a_route(self):
        self.register("B", profile="tomlkit:B")
        (self.state / "native-frontiers.json").write_text('{"frontiers":{"B":{"status":"READY"}}}')
        result = cf.require_frontier_route(self.machine, "B")
        self.assertEqual(result["status"], "UNKNOWN_SEARCH")
        self.assertIsNone(result["capability_id"])

    def test_stale_validator_bytes_cannot_retain_frontier_readiness(self):
        self.register("B", profile="tomlkit:B")
        cap, verified, _ = self.capability()
        self.publish(cap, verified)
        changed = Path(self.temp.name) / "altered_native_adapter.py"
        changed.write_bytes(Path(__file__).read_bytes() + b"\n# changed after admission\n")
        with patch.object(cf, "_validator_source", return_value=changed):
            with self.assertRaisesRegex(ValueError, "validator source changed"):
                cf.require_frontier_route(self.machine, "B")

    def test_separate_process_rebuilds_routes_from_same_immutable_log(self):
        self.register("B", profile="tomlkit:B")
        cap, verified, _ = self.capability()
        self.publish(cap, verified)
        script = """import json,sys
from pathlib import Path
from research.unified_consequence_runtime.developmental_machine import Machine
from research.unified_consequence_runtime import cross_frontier as cf
from research.unified_consequence_runtime import test_cross_frontier
cf._validator_source=lambda _: Path(test_cross_frontier.__file__)
m=Machine(*[Path(x) for x in sys.argv[1:]])
print(json.dumps(cf.require_frontier_route(m,'B')))
"""
        completed = subprocess.run([sys.executable, "-c", script, str(self.components), str(self.state),
                                    str(self.evaluator), str(self.config)],
                                   check=True, capture_output=True, text=True)
        result = json.loads(completed.stdout)
        self.assertEqual(result["status"], "READY")
        self.assertEqual(result["capability_id"], cap)

    def test_frontier_identity_and_authority_are_preserved(self):
        registration = self.register("B", profile="tomlkit:B")
        self.assertEqual(self.register("B", profile="tomlkit:B"), registration)
        with self.assertRaisesRegex(ValueError, "identity conflict"):
            self.register("B", profile="tomlkit:C")
        self.machine.append("revoke", {"target": registration, "reason": "independent obligation withdrawn"})
        self.machine.flush()
        self.assertEqual(cf.require_frontier_route(self.machine, "B")["status"], "UNKNOWN_MISSING_AUTHORITY")


if __name__ == "__main__":
    unittest.main()
