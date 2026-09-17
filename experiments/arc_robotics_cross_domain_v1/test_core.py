import unittest

from experiments.arc_robotics_cross_domain_v1.core import (
    deserialize_capability,
    discover_source_operator,
    majority3_code,
    operator_orbit,
    parity3_code,
    run_arm,
    serialize_capability,
    source_examples,
)


class ArcRoboticsCrossDomainV1Tests(unittest.TestCase):
    def test_source_discovery_uniquely_recovers_parity(self):
        code, evaluations = discover_source_operator(source_examples())
        self.assertEqual(code, parity3_code())
        self.assertGreater(evaluations, 0)

    def test_parity_transfer_orbit_contains_only_parity_and_complement(self):
        orbit = operator_orbit(parity3_code())
        self.assertEqual(len(orbit), 2)
        self.assertEqual(set(orbit), {parity3_code(), 255 ^ parity3_code()})

    def test_majority_sham_orbit_excludes_parity_family(self):
        sham = set(operator_orbit(majority3_code()))
        truth = {parity3_code(), 255 ^ parity3_code()}
        self.assertTrue(sham.isdisjoint(truth))

    def test_warm_is_exact_and_strictly_cheaper_than_cold(self):
        seed = 2026091701
        cold = run_arm('COLD', seed, n_worlds=64)
        warm = run_arm('WARM', seed, n_worlds=64)
        self.assertEqual(cold['correct'], 64)
        self.assertEqual(warm['correct'], 64)
        self.assertEqual(cold['unknown'], 0)
        self.assertEqual(warm['unknown'], 0)
        self.assertEqual(cold['calibration_interventions'], 8)
        self.assertEqual(warm['calibration_interventions'], 2)
        self.assertLess(warm['developmental_cost'], cold['developmental_cost'])

    def test_sham_is_rejected_then_falls_back_exactly(self):
        seed = 2026091702
        sham = run_arm('SHAM', seed, n_worlds=64)
        cold = run_arm('COLD', seed, n_worlds=64)
        self.assertEqual(sham['correct'], 64)
        self.assertEqual(sham['unknown'], 0)
        self.assertTrue(sham['transferred_rejected'])
        self.assertEqual(sham['calibration_interventions'], 8)
        self.assertGreater(sham['developmental_cost'], cold['developmental_cost'])

    def test_ablation_restores_exact_cold_path(self):
        seed = 2026091703
        cold = run_arm('COLD', seed, n_worlds=64)
        ablated = run_arm('ABLATION', seed, n_worlds=64)
        self.assertEqual(ablated['developmental_cost'], cold['developmental_cost'])
        self.assertEqual(ablated['operator_evaluations'], cold['operator_evaluations'])
        self.assertEqual(ablated['calibration_interventions'], 8)
        self.assertEqual(ablated['predictions'], cold['predictions'])

    def test_restart_round_trip_preserves_warm_behavior(self):
        payload = serialize_capability(parity3_code())
        restored = deserialize_capability(payload)
        self.assertEqual(restored, parity3_code())
        seed = 2026091704
        warm = run_arm('WARM', seed, n_worlds=64)
        restart = run_arm('RESTART', seed, n_worlds=64)
        self.assertEqual(restart['developmental_cost'], warm['developmental_cost'])
        self.assertEqual(restart['operator_evaluations'], warm['operator_evaluations'])
        self.assertEqual(restart['calibration_interventions'], 2)
        self.assertEqual(restart['predictions'], warm['predictions'])


if __name__ == '__main__':
    unittest.main()
