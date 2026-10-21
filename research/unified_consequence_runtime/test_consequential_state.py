import unittest
from research.unified_consequence_runtime.consequential_state import normalized_state, withdraw

class NormalizationTests(unittest.TestCase):
    def test_original_warrants_preserved(self):
        s = normalized_state()
        self.assertEqual(len(s["capabilities"]), 4)
        self.assertEqual(len(s["residuals"]), 1)
        self.assertFalse(s["fresh_independent_verification"])
        self.assertEqual(s["action_authorization"], "NONE")

    def test_withdrawal_is_local_and_fail_closed(self):
        s = normalized_state()
        t = withdraw(s, "depth5")
        self.assertEqual(len(t["capabilities"]), 3)
        self.assertEqual(len(t["residuals"]), 2)
        self.assertEqual(len(s["capabilities"]), 4)
        self.assertEqual({x["name"] for x in t["capabilities"]},
                         {"depth4", "mda", "runtime"})

if __name__ == "__main__":
    unittest.main()
