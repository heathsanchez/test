import unittest

from open_development.causal_reuse import qualify


class ExecutableDependencyTests(unittest.TestCase):
    def test_body_intervention_restart_and_revocation(self):
        result = qualify()
        self.assertEqual(result["warm"], "verified")
        self.assertEqual(result["sham_body"], "unknown")
        self.assertEqual(len(result["execution_trace"]), 2)
