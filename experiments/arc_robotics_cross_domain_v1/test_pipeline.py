import unittest

from experiments.arc_robotics_cross_domain_v1.core import run_arm
from experiments.arc_robotics_cross_domain_v1.run import derive_seed
from experiments.arc_robotics_cross_domain_v1.score import score_results
from experiments.arc_robotics_cross_domain_v1.validate import validate_results


class ArcRoboticsPipelineTests(unittest.TestCase):
    def test_derive_seed_is_deterministic_and_provenance_sensitive(self):
        a = derive_seed('abc123', '77')
        b = derive_seed('abc123', '77')
        c = derive_seed('abc123', '78')
        self.assertEqual(a, b)
        self.assertNotEqual(a, c)
        self.assertGreaterEqual(a, 0)

    def test_score_requires_full_causal_pattern(self):
        seed = 2026091711
        rows = [run_arm(arm, seed, 64) for arm in ('COLD', 'WARM', 'SHAM', 'ABLATION', 'RESTART')]
        scored = score_results(rows)
        self.assertTrue(scored['primary']['primary_pass'])
        self.assertEqual(scored['summary']['WARM']['developmental_cost'], 5)
        self.assertEqual(scored['summary']['COLD']['developmental_cost'], 518)
        self.assertEqual(scored['summary']['SHAM']['developmental_cost'], 533)
        self.assertEqual(scored['summary']['ABLATION']['developmental_cost'], 518)
        self.assertEqual(scored['summary']['RESTART']['developmental_cost'], 5)

    def test_validate_accepts_exact_packet_and_rejects_corrupted_warm(self):
        seed = 2026091712
        rows = [run_arm(arm, seed, 64) for arm in ('COLD', 'WARM', 'SHAM', 'ABLATION', 'RESTART')]
        metadata = {
            'schema': 'arc.robotics.cross_domain.v1',
            'seed': seed,
            'seed_provenance': {'github_sha': 'deadbeef', 'github_run_id': '99'},
            'n_worlds': 64,
            'llm_used': False,
        }
        validate_results(rows, metadata)

        broken = [dict(row) for row in rows]
        warm = next(row for row in broken if row['arm'] == 'WARM')
        warm['correct'] = 63
        with self.assertRaises(AssertionError):
            validate_results(broken, metadata)


if __name__ == '__main__':
    unittest.main()
