"""Adversarial local routing checks over real Metatron and FLASH closure.

Synthetic graph records here deliberately have no scientific authority. Native
world mutation methods are mocked; positive scientific evidence is established
separately by test_v54_verify and the native qualification.
"""

from dataclasses import asdict
import copy
import json
from pathlib import Path
import subprocess
from unittest.mock import Mock, patch

from research.unified_consequence_runtime import test_v54_runtime as fixtures
from research.unified_consequence_runtime.developmental_machine import Capability
from research.unified_consequence_runtime.v54_source import SOURCE_COMMIT, SOURCE_PATH, SOURCE_SHA256, WORLD_PINS
from research.unified_consequence_runtime import v54_verify


O1 = {"kind": "TOKEN_REWRITE", "src": "<", "dst": "<="}
O2 = {"kind": "TOKEN_REWRITE", "src": "and", "dst": "or"}
SCOPE = {"world": "requests", "relative_path": "src/requests/utils.py", "line_no": 626, "first_word": "if"}
SOURCE = {"repository": "heathsanchez/triskelion", "commit": SOURCE_COMMIT, "path": SOURCE_PATH, "sha256": SOURCE_SHA256}


def fabricated_receipt(program, stage):
    """A self-consistent public checksum is intentionally not a native warrant."""
    receipt = {"status": "accepted", "evaluated": False, "stage": stage,
               "source_commit": SOURCE_COMMIT, "source_path": SOURCE_PATH, "source_sha256": SOURCE_SHA256,
               "program_sha256": v54_verify._sha(v54_verify._json_bytes(program)),
               "scope_sha256": v54_verify._sha(v54_verify._json_bytes(v54_verify.TASK_SCOPE)),
               "native_receipts": [], "gates": {}}
    receipt["receipt_sha256"] = v54_verify._sha(v54_verify._json_bytes(receipt))
    return receipt


class V54AdversarialRoutingTests(fixtures.V54RuntimeTests):
    def setUp(self):
        super().setUp()
        # All routes that can mutate producer worlds are intercepted, including
        # target preparation during restoration.
        self.runtime.session.target_scope = Mock(return_value=copy.deepcopy(SCOPE))
        self.runtime.session.apply_operator = Mock(return_value={"fixture": "no native effect"})
        self.runtime.session.prepare_target = Mock(return_value={})
        self.runtime.session.prepare_warm = Mock(return_value={})
        self.runtime.session.cold_search = Mock(return_value=[])
        self.runtime.session.warm_search = Mock(return_value={"operator": O2})

    def capability(self, label="O1", *, source=None, operation="v54.token_rewrite", world_pins=None, declared_parents=(), graph_parents=None, target_scope=None, evidence_fields=None):
        machine = self.runtime.machine
        operator = O1 if label == "O1" else O2
        program = {"operators": [operator], "scope_word": "if"}
        graph_parents = declared_parents if graph_parents is None else graph_parents
        support = machine.append("source_support", {"source_commit": SOURCE_COMMIT,
            "source_sha256": SOURCE_SHA256, "operator": operator, "label": label, "generation": 1,
            "supersedes": None}, (self.runtime.source, *graph_parents))
        receipt = fabricated_receipt(program, "o1" if label == "O1" else "o2")
        if evidence_fields:
            receipt.update(evidence_fields)
            receipt.pop("receipt_sha256", None)
            receipt["receipt_sha256"] = v54_verify._sha(v54_verify._json_bytes(receipt))
        verification = machine.append("independent_native_verification", {
            "receipt": machine.put(receipt),
            "program": machine.put(program)}, (support,))
        descriptor = Capability(operation, source or dict(SOURCE),
            {"target": dict(target_scope or SCOPE), "world_pins": world_pins or dict(WORLD_PINS),
             "authority_ceiling": self.runtime.authority_ceiling,
             "authorization": "LOCAL_RESEARCH_EXECUTION_ONLY"},
            machine.put({"label": label, "acquisition_source": self.runtime.session.source_provenance}),
            machine.put(operator), 1, (support, *declared_parents), (verification,),
            "CAPABILITY_LANGUAGE_EXTENSION", None)
        node = machine.append("executable_capability", asdict(descriptor), (support, verification, *graph_parents))
        machine.flush()
        return node, descriptor

    def assert_no_native_mutation(self):
        self.runtime.session.apply_operator.assert_not_called()
        self.runtime.session.prepare_target.assert_not_called()
        self.runtime.session.prepare_warm.assert_not_called()
        self.runtime.session.cold_search.assert_not_called()

    def test_cold_constructor_checks_source_authority_before_mutation(self):
        self.runtime.machine.append("revoke", {"target": self.runtime.source, "reason": "withdrawn source"})
        self.runtime.machine.flush()
        with self.assertRaises((PermissionError, ValueError)):
            self.runtime.construct_next()
        self.assert_no_native_mutation()

    def test_warm_constructor_validates_class_before_preparation(self):
        node, _ = self.capability(operation="other.executable_class")
        with self.assertRaises((PermissionError, ValueError)):
            self.runtime.construct_next(node)
        self.assert_no_native_mutation()

    def test_same_source_hash_does_not_authorize_wrong_commit(self):
        node, _ = self.capability(source=dict(SOURCE, commit="0" * 40))
        with self.assertRaises((PermissionError, ValueError)):
            self.runtime.apply(node)
        self.assert_no_native_mutation()

    def test_changed_native_world_pins_cannot_replay_capability(self):
        node, _ = self.capability(world_pins=dict(WORLD_PINS, requests="0" * 40))
        with self.assertRaises((PermissionError, ValueError)):
            self.runtime.apply(node)
        self.assert_no_native_mutation()

    def test_live_closure_does_not_make_fabricated_native_receipt_authoritative(self):
        node, _ = self.capability()
        self.assertIn(node, self.runtime.machine.mt.live_ids(self.runtime.machine.log))
        self.assertIn(node, self.runtime.machine.flash_live_ids())
        with self.assertRaises((PermissionError, ValueError)):
            self.runtime.apply(node)
        self.assert_no_native_mutation()

    def test_declared_revoked_ancestor_cannot_be_omitted_from_graph_premises(self):
        parent, parent_cap = self.capability()
        child, _ = self.capability("O2", declared_parents=(parent,), graph_parents=())
        self.runtime.machine.append("revoke", {"target": parent_cap.dependencies[0], "reason": "ancestor removed"})
        self.runtime.machine.flush()
        self.assertNotIn(parent, self.runtime.machine.mt.live_ids(self.runtime.machine.log))
        self.assertIn(child, self.runtime.machine.mt.live_ids(self.runtime.machine.log))
        with self.assertRaises((PermissionError, ValueError)):
            self.runtime.apply(child)
        self.assert_no_native_mutation()

    def test_source_withdrawal_during_content_checks_blocks_mutation(self):
        node, cap = self.capability()
        original_get = self.runtime.machine.get
        def get_then_withdraw(key):
            result = original_get(key)
            if key == cap.program:
                self.runtime.machine.append("revoke", {"target": cap.dependencies[0], "reason": "withdrawn before effect"})
                self.runtime.machine.flush()
            return result
        with patch.object(self.runtime.machine, "get", side_effect=get_then_withdraw):
            with self.assertRaises((PermissionError, ValueError)):
                self.runtime.apply(node)
        self.assert_no_native_mutation()

    def test_withdrawal_after_O1_effect_blocks_following_warm_search(self):
        node, cap = self.capability()
        def apply_then_withdraw(_):
            self.runtime.machine.append("revoke", {"target": cap.dependencies[0], "reason": "withdrawn before warm search"})
            self.runtime.machine.flush()
            return {}, "fixture-effect"
        # This fixture isolates the second mutation boundary after the O1
        # application; validation and source execution have separate tests.
        with patch.object(self.runtime, "_validated", return_value=(cap, "O1", O1)):
            with patch.object(self.runtime, "apply", side_effect=apply_then_withdraw):
                with self.assertRaises((PermissionError, ValueError)):
                    self.runtime.construct_next(node)
        self.runtime.session.warm_search.assert_not_called()

    def test_content_addressed_program_corruption_fails_before_mutation(self):
        node, cap = self.capability()
        (self.runtime.machine.state / "objects" / cap.program).write_text(json.dumps(dict(O1, dst="==")))
        with self.assertRaises((PermissionError, ValueError)):
            self.runtime.apply(node)
        self.assert_no_native_mutation()

    def test_corrupted_native_evidence_is_read_before_mutation(self):
        node, cap = self.capability()
        evidence = next(n for n in self.runtime.machine.log if n.id == cap.evidence[0])
        (self.runtime.machine.state / "objects" / evidence.payload["receipt"]).write_text('{"status":"accepted"}')
        with self.assertRaises((PermissionError, ValueError)):
            self.runtime.apply(node)
        self.assert_no_native_mutation()

    def test_restore_validates_source_and_class_before_loading_executable_data(self):
        node, _ = self.capability(operation="other.executable_class")
        before = dict(self.runtime.session.env)
        with self.assertRaises((PermissionError, ValueError)):
            self.runtime.restore_session([node])
        self.assertEqual(before, self.runtime.session.env)
        self.assertFalse(self.runtime.session._acquired)
        self.assert_no_native_mutation()

    def test_restore_batch_failure_does_not_partially_seed_acquired_operators(self):
        first, _ = self.capability()
        second, second_cap = self.capability("O2", declared_parents=(first,))
        (self.runtime.machine.state / "objects" / second_cap.program).unlink()
        before = dict(self.runtime.session.env)
        with self.assertRaises((PermissionError, ValueError, FileNotFoundError)):
            self.runtime.restore_session([first, second])
        self.assertEqual(before, self.runtime.session.env)
        self.assertFalse(self.runtime.session._acquired)
        self.assert_no_native_mutation()

    def test_restore_binds_target_row_before_native_preparation(self):
        evidence = {"evaluated": True, "gates": {"fixture_native_evidence": True},
                    "verifier_source_sha256": v54_verify._sha(Path(v54_verify.__file__).read_bytes()),
                    "native_receipts": [{"label": "requests_iter_slices:breaking_site:626:44"}]}
        wrong_scope = dict(SCOPE, line_no=627)
        first, _ = self.capability(target_scope=wrong_scope, evidence_fields=evidence)
        second, _ = self.capability("O2", declared_parents=(first,), target_scope=wrong_scope, evidence_fields=evidence)
        # Treat native test evaluation as an opaque trusted fixture and isolate
        # its binding to the restoration target. This is not native evidence.
        with patch.object(self.runtime, "_native_evidence_valid", return_value=True):
            with self.assertRaises((PermissionError, ValueError)):
                self.runtime.restore_session([first, second])
        self.assert_no_native_mutation()

    def test_native_consequence_requires_exact_ancestor_chain_before_verification(self):
        first, _ = self.capability()
        second, _ = self.capability("O2")
        with patch.object(self.runtime, "independent_verify", return_value={"status": "accepted"}) as verify:
            with self.assertRaises((PermissionError, ValueError)):
                self.runtime.native_consequence([first, second])
        verify.assert_not_called()
        self.assert_no_native_mutation()

    def test_wrong_target_task_replay_fails_before_mutation(self):
        node, _ = self.capability()
        with self.assertRaises((PermissionError, ValueError)):
            self.runtime.apply(node, dict(SCOPE, world="rich", relative_path="rich/highlighter.py"))
        self.assert_no_native_mutation()

    def test_recomputed_receipt_checksum_cannot_replace_native_execution_evidence(self):
        program = {"operators": [O1], "scope_word": "if"}
        fake = fabricated_receipt(program, "o1")
        def write_fabricated_process_output(command, **kwargs):
            out = Path(command[command.index("--out") + 1])
            out.write_text(json.dumps(fake))
            return subprocess.CompletedProcess(command, 0)
        with patch("research.unified_consequence_runtime.v54_runtime.subprocess.run", side_effect=write_fabricated_process_output):
            with self.assertRaises((PermissionError, ValueError)):
                self.runtime.independent_verify(program, "o1")
        self.assert_no_native_mutation()

