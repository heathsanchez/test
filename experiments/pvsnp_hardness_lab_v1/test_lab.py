import json
import unittest
from pathlib import Path

from experiment import build_evidence
from lab import (
    circuit_size_upper_bound,
    enumerate_nand,
    evaluate_witness,
    input_masks,
    minimum_exclusion_core,
    nand,
    parity_subcube_certificate,
    retained_parity_lower_bound,
    singleton_relaxation_cost,
    structural_signature,
    truth_table,
)


class ExactNandLabTests(unittest.TestCase):
    def test_compact_evidence_record_replays_the_claims(self):
        evidence = build_evidence()
        self.assertEqual(evidence["n3_exact"]["new_functions"], [3, 6, 13, 26, 43, 48])
        self.assertEqual(evidence["n4_transfer"]["new_functions"], [4, 10, 31, 98, 293])
        self.assertEqual(evidence["metric_collision"]["sizes"], [2, 3])
        self.assertEqual(evidence["coavailability_residual"]["xor_costs"], [3, 4])
        self.assertEqual(evidence["global_consistency"]["minimum_core_rows"], [1, 2, 3, 4, 5, 6])
        self.assertEqual(evidence["imported_theorem_transfer"]["with_theorem_lower_bound"], 9)
        self.assertIsNone(evidence["imported_theorem_transfer"]["without_theorem"])
        self.assertEqual(evidence["classification"], "FINITE_SIGNAL")
        self.assertEqual(
            json.loads(Path(__file__).with_name("evidence.json").read_text()), evidence
        )

    def test_truth_table_encoding_and_nand_are_literal(self):
        self.assertEqual(input_masks(3), (0xAA, 0xCC, 0xF0))
        self.assertEqual(nand(0xAA, 0xCC, 3), 0x77)

    def test_every_free_input_has_a_replayable_zero_gate_witness(self):
        result = enumerate_nand(4, 0)
        for mask in input_masks(4):
            self.assertEqual(evaluate_witness(4, result.witnesses[mask]), mask)

    def test_exact_available_set_bfs_matches_independent_census(self):
        result = enumerate_nand(3, 5)
        self.assertEqual(result.state_counts, [1, 6, 36, 206, 1252, 8188])
        self.assertEqual(result.new_function_counts, [3, 6, 13, 26, 43, 48])
        self.assertEqual(len(result.min_size), 139)

    def test_witnesses_replay_and_separate_a_metric_collision(self):
        result = enumerate_nand(3, 4)
        for mask in (0x8F, 0xEA, 0x66):
            self.assertEqual(evaluate_witness(3, result.witnesses[mask]), mask)
        self.assertEqual(result.min_size[0x8F], 2)
        self.assertEqual(result.min_size[0xEA], 3)
        self.assertEqual(result.min_size[0x66], 4)
        self.assertEqual(structural_signature(0x8F, 3), structural_signature(0xEA, 3))

    def test_singleton_costs_are_not_compositionally_sufficient(self):
        result = enumerate_nand(3, 4)
        self.assertEqual(singleton_relaxation_cost(0x66, 3, result.min_size), 3)
        self.assertEqual(result.min_size[0x66], 4)

    def test_majority_needs_a_six_row_global_consistency_core(self):
        result = enumerate_nand(3, 3)
        majority = truth_table(3, lambda bits: int(sum(bits) >= 2))
        core = minimum_exclusion_core(majority, set(result.min_size), 8)
        self.assertEqual(core, (1, 2, 3, 4, 5, 6))
        for omitted in core:
            rows = tuple(row for row in core if row != omitted)
            self.assertTrue(
                any(all(((candidate ^ majority) >> row) & 1 == 0 for row in rows)
                    for candidate in result.min_size)
            )

    def test_parity_subcube_capability_transfers_beyond_enumerated_n3(self):
        parity4 = truth_table(4, lambda bits: sum(bits) & 1)
        cert = parity_subcube_certificate(parity4, 4)
        self.assertIsNotNone(cert)
        self.assertEqual(cert.free_variables, (0, 1, 2, 3))
        self.assertEqual(retained_parity_lower_bound(parity4, 4), 9)
        self.assertIsNone(retained_parity_lower_bound(parity4, 4, enabled=False))

    def test_gated_parity_reuses_the_same_certificate(self):
        gated_parity4 = truth_table(
            5, lambda bits: bits[4] & ((bits[0] ^ bits[1] ^ bits[2] ^ bits[3]))
        )
        cert = parity_subcube_certificate(gated_parity4, 5)
        self.assertIsNotNone(cert)
        self.assertEqual(len(cert.free_variables), 4)
        self.assertEqual(retained_parity_lower_bound(gated_parity4, 5), 9)
        self.assertEqual(circuit_size_upper_bound(gated_parity4, 5), 14)


if __name__ == "__main__":
    unittest.main()
