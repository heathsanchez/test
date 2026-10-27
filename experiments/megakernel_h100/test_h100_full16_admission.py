"""CPU-only full-architecture admission controls."""
import ast
from pathlib import Path
import unittest

from h100_architecture_audit import audit_sources, classify, ELIGIBLE, REJECTED


class Full16ContractTests(unittest.TestCase):
    def test_source_uses_pinned_16_layer_cuda_geometry(self):
        gate = Path(__file__).with_name("gpu_megakernel_gate.py").read_text()
        worker = Path(__file__).with_name("runpod_flash_h100_bridge.py").read_text()
        ast.parse(gate)
        ast.parse(worker)
        self.assertIn('(16, 16)', gate)
        self.assertIn('if lm_head_active:', gate)
        self.assertIn('REJECTED_INVALID_LMHEAD_ARCHITECTURE', gate)
        self.assertIn('elif probe_kind == "full16":', worker)
        self.assertIn('report["status"] = "PASS_FULL16"', worker)
        self.assertIn('allowed = ("PASS_FULL16",)', worker)
        self.assertIn('"fixture_layers": num_layers', gate)
        self.assertIn('"executed_layers": layer_limit', gate)

    def test_full_short_fixtures_rejected_not_gpu_failures(self):
        facts = audit_sources(
            "#define LLAMA_1B_NUM_LAYERS 16\n",
            "EXPECTED_ARRIVAL_COUNT = 512\n"
            "while (g.Bar[{globals::num_layers - 1, OPCODE_DownProjResidual - 1, 0}]) {}",
            "barriers = torch.zeros([config.num_hidden_layers, 10, 48])\n"
            "if nlayers == globs.num_hidden_layers:",
        )
        self.assertEqual(classify(facts, 2, 2), REJECTED)
        self.assertEqual(classify(facts, 16, 16), ELIGIBLE)


if __name__ == "__main__":
    unittest.main()
