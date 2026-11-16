import unittest

from scripts.c233_trace_diff import compare_trace_lines


def event(seq, kind, left, right, budget, attempts=32, outcome="pending", depth=8, ctx=8):
    return (
        f"NUCLEUS_C233_DECISION:seq={seq}:kind={kind}:left={left}:right={right}"
        f":budget={budget}:attempts={attempts}:outcome={outcome}:depth={depth}:ctx={ctx}"
    )


class C233TraceDiffTests(unittest.TestCase):
    def test_budget_drift_alone_is_not_a_path_divergence(self):
        left = [event(0, "work", "term8@4", "term5@2", 27),
                event(1, "reducible", "term8@4", "term5@2", 25, 31, "both-proven")]
        right = [event(0, "work", "term8@4", "term5@2", 34),
                 event(1, "reducible", "term8@4", "term5@2", 31, 30, "both-proven")]
        result = compare_trace_lines(left, right)
        self.assertEqual(result["status"], "SAME_OBSERVED_PATH")
        self.assertEqual(result["compared_events"], 2)

    def test_first_source_operand_or_branch_difference_is_retained(self):
        low = [event(0, "work", "pi", "pi", 27),
               event(1, "reducible", "term8@4", "term1@2", 22, outcome="both-proven")]
        high = [event(0, "work", "pi", "pi", 34),
                event(1, "reducible", "term12@4", "term5@2", 29, outcome="left-unknown")]
        result = compare_trace_lines(low, high)
        self.assertEqual(result["status"], "FIRST_DIVERGENCE")
        self.assertEqual(result["index"], 1)
        self.assertEqual(result["low"]["left"], "term8@4")
        self.assertEqual(result["high"]["outcome"], "left-unknown")

    def test_missing_or_shortened_path_does_not_prove_divergence(self):
        a = [event(0, "work", "pi", "pi", 27)]
        b = a + [event(1, "reducible", "term8@4", "term1@2", 20)]
        self.assertEqual(compare_trace_lines([], b)["status"], "UNKNOWN")
        self.assertEqual(compare_trace_lines(a, b)["status"], "INCOMPLETE_PATH")

    def test_malformed_trace_is_unknown_not_silently_ignored(self):
        valid = [event(0, "work", "pi", "pi", 27)]
        self.assertEqual(
            compare_trace_lines(valid, ["NUCLEUS_C233_DECISION:seq=0:kind=work"])["status"],
            "UNKNOWN",
        )

    def test_captured_context_change_is_a_real_path_difference(self):
        low = [event(0, "work", "term8@4", "term5@2", 27, ctx=8)]
        high = [event(0, "work", "term8@4", "term5@2", 34, ctx=10)]
        self.assertEqual(compare_trace_lines(low, high)["status"], "FIRST_DIVERGENCE")

    def test_truncated_recording_is_unknown_even_with_matching_prefix(self):
        prefix = [event(0, "work", "term8@4", "term5@2", 27)]
        self.assertEqual(compare_trace_lines(prefix + ["NUCLEUS_C233_TRUNCATED"], prefix)["status"], "UNKNOWN")


if __name__ == "__main__":
    unittest.main()
