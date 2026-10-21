import copy
import unittest

from research.unified_consequence_runtime.integrate import check_provider_run, independent_live


class SourceAuthorityTests(unittest.TestCase):
    def setUp(self):
        self.pinned = (
            "CSLIB_NATIVE_FAIL", "heathsanchez/test", 38237298379,
            "a50f199082da91845115efb77844603dee55a465", "failure",
        )
        self.source = {
            "id": self.pinned[2], "head_sha": self.pinned[3],
            "status": "completed", "conclusion": "failure",
            "repository": {"full_name": self.pinned[1]},
            "html_url": "https://github.com/heathsanchez/test/actions/runs/38237298379"
        }

    def test_native_failure_kept_as_historical_pointer(self):
        out = check_provider_run(self.pinned, self.source)
        self.assertEqual(out["conclusion"], "failure")
        self.assertEqual(out["authority"], "HISTORICAL_POINTER_ONLY")

    def test_cannot_launder_red_into_green(self):
        wrong = copy.deepcopy(self.source)
        wrong["conclusion"] = "success"
        with self.assertRaises(AssertionError):
            check_provider_run(self.pinned, wrong)

    def test_cannot_change_pinned_source(self):
        wrong = copy.deepcopy(self.source)
        wrong["head_sha"] = "0" * 40
        with self.assertRaises(AssertionError):
            check_provider_run(self.pinned, wrong)

    def test_cannot_change_source_repository(self):
        wrong = copy.deepcopy(self.source)
        wrong["repository"]["full_name"] = "other/repo"
        with self.assertRaises(AssertionError):
            check_provider_run(self.pinned, wrong)

    def test_cannot_claim_future_result(self):
        wrong = copy.deepcopy(self.source)
        wrong["status"] = "in_progress"
        with self.assertRaises(AssertionError):
            check_provider_run(self.pinned, wrong)


if __name__ == "__main__":
    unittest.main()
