"""C85 trial contract: a missed/ambiguous census must not be promoted."""
import importlib.util
from pathlib import Path
import unittest


MODULE = Path(__file__).with_name("c85_completion_trial.py")


def load_trial():
    spec = importlib.util.spec_from_file_location("c85_completion_trial", MODULE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class C85TrialContract(unittest.TestCase):
    def test_completed_census_parses_without_counting_partial_one_step(self):
        data = load_trial().parse_c85_summary([
            'NUCLEUS_C85_COMPLETED:{"completed":3,"unique_exact":2,'
            '"repeated_exact":1,"repeated_inclusive_work":97,'
            '"one_step_exits":5,"cache_hits":2,"unkeyed_completions":0,"overflow":0,'
            '"limit":8192,"completed_inclusive_work":175,'
            '"goal_counts":{"Completed":2,"OneStep":1},'
            '"source_authority_preserved":true,"exact_structural_comparison":true,'
            '"completed_only":true,"inclusive_cost_not_realizable_savings":true}'
        ])
        self.assertEqual(data["repeated_exact"], 1)
        self.assertEqual(data["repeated_inclusive_work"], 97)
        self.assertEqual(data["one_step_exits"], 5)
        self.assertEqual(data["unkeyed_completions"], 0)
        self.assertTrue(data["exact_completion_coverage"])

    def test_keyless_completions_are_visible_as_incomplete_coverage(self):
        line = ('NUCLEUS_C85_COMPLETED:{"completed":0,"unique_exact":0,'
                '"repeated_exact":0,"repeated_inclusive_work":0,'
                '"one_step_exits":0,"cache_hits":0,"unkeyed_completions":2,"overflow":0,'
                '"limit":8192,"completed_inclusive_work":0,'
                '"goal_counts":{"Completed":0,"OneStep":0},'
                '"source_authority_preserved":true,"exact_structural_comparison":true,'
                '"completed_only":true,"inclusive_cost_not_realizable_savings":true}')
        data = load_trial().parse_c85_summary([line])
        self.assertEqual(data["unkeyed_completions"], 2)
        self.assertFalse(data["exact_completion_coverage"])

    def test_missing_or_duplicate_report_fails_closed(self):
        for lines in ([], ['NUCLEUS_C85_COMPLETED:{}'] * 2):
            with self.subTest(lines=lines):
                with self.assertRaises(AssertionError):
                    load_trial().parse_c85_summary(lines)

    def test_inconsistent_partition_or_overflow_cannot_be_promoted(self):
        base = ("NUCLEUS_C85_COMPLETED:{\"completed\":3,\"unique_exact\":2,"
                "\"repeated_exact\":1,\"repeated_inclusive_work\":97,"
                "\"one_step_exits\":5,\"cache_hits\":2,\"overflow\":0,"
                "\"limit\":8192,\"completed_inclusive_work\":175,"
                "\"goal_counts\":{\"Completed\":1,\"OneStep\":1},"
                "\"source_authority_preserved\":true,\"exact_structural_comparison\":true,"
                "\"completed_only\":true,\"inclusive_cost_not_realizable_savings\":true}")
        with self.assertRaises(AssertionError):
            load_trial().parse_c85_summary([base])
        with self.assertRaises(AssertionError):
            load_trial().parse_c85_summary([base.replace('"overflow":0', '"overflow":1')])


if __name__ == "__main__":
    unittest.main()
