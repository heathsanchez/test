"""CPU-only architecture falsification and positive/negative controls."""
import unittest

from h100_architecture_audit import (
    audit_sources, classify, REJECTED, ELIGIBLE, PARTIAL
)


class ArchitectureAuditTests(unittest.TestCase):
    def setUp(self):
        self.cuda = "#define LLAMA_1B_NUM_LAYERS 16\n"
        self.head = ("static constexpr int EXPECTED_ARRIVAL_COUNT = 512;\n"
                     "while (g.Bar[{globals::num_layers - 1, OPCODE_DownProjResidual - 1, 0}]) {}\n")
        self.scheduler = ("barriers = torch.zeros([config.num_hidden_layers, 10, 48])\n"
                          "if nlayers == globs.num_hidden_layers:\n")
        self.facts = audit_sources(self.cuda, self.head, self.scheduler)

    def test_compiled_layer_identity(self):
        self.assertEqual(self.facts["compiled_layers"], 16)
        self.assertEqual(self.facts["arrival_threshold"], 512)

    def test_one_and_two_layer_full_models_rejected(self):
        self.assertEqual(classify(self.facts, 1, 1), REJECTED)
        self.assertEqual(classify(self.facts, 2, 2), REJECTED)
        self.assertEqual(classify(self.facts, 3, 3), REJECTED)

    def test_partial_controls_do_not_claim_lm_head(self):
        self.assertEqual(classify(self.facts, 2, 1), PARTIAL)
        self.assertEqual(classify(self.facts, 3, 2), PARTIAL)

    def test_matching_16_layer_full_is_only_eligible(self):
        self.assertEqual(classify(self.facts, 16, 16), ELIGIBLE)

    def test_invalid_counts_rejected(self):
        self.assertEqual(classify(self.facts, 2, 3), "REJECTED_UNREGISTERED_LAYER_COUNT")
        self.assertEqual(classify(self.facts, 17, 17), "REJECTED_EXCEEDS_COMPILED_LAYERS")

    def test_missing_wait_guard_fails_closed(self):
        with self.assertRaises(ValueError):
            audit_sources(self.cuda, "no lm head wait here", self.scheduler)

    def test_missing_python_barrier_dimension_fails_closed(self):
        with self.assertRaises(ValueError):
            audit_sources(self.cuda, self.head, "other scheduler")


if __name__ == "__main__":
    unittest.main()
