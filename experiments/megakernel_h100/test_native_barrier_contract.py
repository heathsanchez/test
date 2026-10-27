"""Mutation and positive controls for source-pinned native LM-head barrier audit."""
import tempfile
from pathlib import Path
import unittest

from native_barrier_contract import audit_native_barriers


class BarrierContractTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / "demos/low-latency-llama").mkdir(parents=True)
        (self.root / "megakernels/demos/latency").mkdir(parents=True)
        self.header = self.root / "demos/low-latency-llama/llama.cuh"
        self.lm = self.root / "demos/low-latency-llama/rms_lm_head.cu"
        self.scheduler = self.root / "megakernels/demos/latency/scheduler.py"
        self.header.write_text("#define LLAMA_1B_NUM_LAYERS 16\ntypedef globals_t<LLAMA_1B_NUM_LAYERS, 2048> llama_1b_globals;\n")
        self.lm.write_text("while (g.Bar[{globals::num_layers - 1, OPCODE_DownProjResidual - 1, 0}] < 512) {}\n")
        self.scheduler.write_text("barriers = torch.zeros([config.num_hidden_layers, 10, 48])\n")

    def tearDown(self):
        self.tmp.cleanup()

    def audit(self, model_layers, executed_layers):
        return audit_native_barriers(self.root, model_layers, executed_layers)

    def test_native_two_layer_full_path_rejected(self):
        r = self.audit(2, 2)
        self.assertEqual(r["status"], "BLOCKED_NATIVE_BARRIER_OUT_OF_BOUNDS")
        self.assertEqual(r["lm_head_wait_barrier_layer_index"], 15)
        self.assertEqual(r["python_barrier_layer_capacity"], 2)
        self.assertFalse(r["eligible"])

    def test_partial_layer_excludes_unsafe_lmhead(self):
        for model, executed in ((2, 1), (3, 2), (16, 15)):
            with self.subTest(model=model, executed=executed):
                r = self.audit(model, executed)
                self.assertEqual(r["status"], "PARTIAL_NO_LMHEAD_SCOPE")
                self.assertFalse(r["lm_head_active"])
                self.assertTrue(r["eligible"])

    def test_exact_sixteen_layer_depth_is_only_full_path_admissible(self):
        r = self.audit(16, 16)
        self.assertEqual(r["status"], "ELIGIBLE_FULL_DEPTH_UNVERIFIED")
        self.assertTrue(r["barrier_index_in_bounds"])
        self.assertTrue(r["eligible"])

    def test_incorrect_scope_rejected(self):
        self.assertEqual(self.audit(2, 3)["status"], "BLOCKED_INVALID_MODEL_SCOPE")
        self.assertEqual(self.audit(0, 0)["status"], "BLOCKED_INVALID_MODEL_SCOPE")

    def test_unknown_native_macro_rejected(self):
        self.header.write_text(self.header.read_text().replace("LAYERS 16", "LAYERS UNKNOWN"))
        self.assertEqual(self.audit(2, 2)["status"], "UNKNOWN_SOURCE_CONTRACT")

    def test_mutated_wait_index_rejected(self):
        self.lm.write_text(self.lm.read_text().replace("num_layers - 1", "num_layers - 2"))
        self.assertEqual(self.audit(16, 16)["status"], "UNKNOWN_SOURCE_CONTRACT")

    def test_missing_python_allocation_provenance_rejected(self):
        self.scheduler.write_text("barriers = torch.zeros([17, 10, 48])\n")
        self.assertEqual(self.audit(16, 16)["status"], "UNKNOWN_SOURCE_CONTRACT")


if __name__ == "__main__":
    unittest.main()
