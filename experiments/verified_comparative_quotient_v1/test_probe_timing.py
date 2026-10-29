"""Finite red controls for decision-time identifiability and probe provenance.

This is a toy protocol calibration, NOT a new model-capability benchmark.
"""

import unittest

from probe_timing import (
    possible_worlds,
    common_optimal_actions,
    evaluate_probe,
    check_admissible_probe,
    lawful_choice,
    legitimate_measurement,
    oracle_relabelled_as_bit,
)


WORLD_OPT = {0: frozenset({"A"}), 1: frozenset({"A"}),
             2: frozenset({"B"}), 3: frozenset({"B"})}
INSTRUMENTS = {
    "diagnostic": (0, 0, 1, 1),
    "distractor": (0, 1, 0, 1),
}


class DecisionTimingTests(unittest.TestCase):
    def test_public_state_has_no_guaranteed_optimum(self):
        self.assertEqual(common_optimal_actions(WORLD_OPT, (0, 1, 2, 3)), frozenset())

    def test_legitimate_diagnostic_produces_soluble_final_transcripts(self):
        classes = evaluate_probe(INSTRUMENTS, "diagnostic", (0, 1, 2, 3))
        self.assertEqual(classes, {0: (0, 1), 1: (2, 3)})
        self.assertEqual({bit: common_optimal_actions(WORLD_OPT, cls)
                          for bit, cls in classes.items()},
                         {0: frozenset({"A"}), 1: frozenset({"B"})})
        for bit, cls in classes.items():
            self.assertIn(lawful_choice(WORLD_OPT, cls), common_optimal_actions(WORLD_OPT, cls))

    def test_irrelevant_probe_cannot_guarantee_final_choice(self):
        classes = evaluate_probe(INSTRUMENTS, "distractor", (0, 1, 2, 3))
        self.assertEqual(classes, {0: (0, 2), 1: (1, 3)})
        for cls in classes.values():
            self.assertEqual(common_optimal_actions(WORLD_OPT, cls), frozenset())
            self.assertIsNone(lawful_choice(WORLD_OPT, cls))

    def test_explicit_oracle_message_is_not_a_registered_measurement(self):
        self.assertTrue(check_admissible_probe(INSTRUMENTS, "diagnostic", cost=1))
        self.assertFalse(check_admissible_probe(INSTRUMENTS, "oracle_answer", cost=1))
        self.assertFalse(check_admissible_probe(INSTRUMENTS, "diagnostic", cost=0))

    def test_same_visible_bits_cannot_prove_feedback_provenance(self):
        """Source readout and optimum-derived oracle can be observationally identical."""
        for world in WORLD_OPT:
            self.assertEqual(legitimate_measurement(INSTRUMENTS, world),
                             oracle_relabelled_as_bit(WORLD_OPT, world))
        self.assertFalse(check_admissible_probe(INSTRUMENTS, "oracle_answer", cost=1))

    def test_transcript_restricts_worlds_without_revealing_hidden_opt_field(self):
        self.assertEqual(possible_worlds(INSTRUMENTS, (0, 1, 2, 3),
                                         (("diagnostic", 0),)), (0, 1))
        self.assertEqual(possible_worlds(INSTRUMENTS, (0, 1, 2, 3),
                                         (("diagnostic", 1),)), (2, 3))


if __name__ == "__main__":
    unittest.main(verbosity=2)
