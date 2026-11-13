"""The C126 source-native trace parser must reject unqualified observations."""

import unittest

from probe_c126_n7_function_type import (
    parse_traces, summarize_owner_traces, parse_app_edges, parse_arg_obligations,
)


class C126TraceTests(unittest.TestCase):
    def test_exact_source_site_and_two_budget_outcomes(self):
        sample = (
            "NUCLEUS_C126_N7_HEAD:application=8835:function=8805:argument=8834:"
            "before=65000:after=64000:context=0:pi_head=false:type_proven=false:"
            "type=Unknown\n"
            "NUCLEUS_C126_N7_HEAD:application=8835:function=8805:argument=8834:"
            "before=14000000:after=13900000:context=0:pi_head=true:type_proven=true:"
            "type=Proven\n"
        ).encode()
        result = parse_traces(sample)
        self.assertEqual(len(result), 2)
        self.assertEqual([row["pi_head"] for row in result], [False, True])
        self.assertEqual([row["charged"] for row in result], [1000, 100000])

    def test_wrong_source_site_is_rejected(self):
        invalid = (
            "NUCLEUS_C126_N7_HEAD:application=8835:function=8806:argument=8834:"
            "before=100:after=50:context=0:pi_head=false:type_proven=false:type=Unknown\n"
        ).encode()
        with self.assertRaises(AssertionError):
            parse_traces(invalid)

    def test_owner_summary_keeps_resource_counters_separate_from_typing(self):
        sample = (
            "NUCLEUS_C97_OWNER:start=1000:spent=300:major_work=200:loops=45:"
            "unique_node_env=20:repeat_node_env=5:unique_head_pending=15:repeat_head_pending=3\n"
            "NUCLEUS_C97_OWNER:start=2000:spent=100:major_work=80:loops=12:"
            "unique_node_env=10:repeat_node_env=2:unique_head_pending=8:repeat_head_pending=1\n"
            "NUCLEUS_NESTED_REPLAY_FAILURE:depth=2:head=NameId(147):major=Unknown\n"
        ).encode()
        summary = summarize_owner_traces(sample)
        self.assertEqual(summary["c97_total_spent"], 400)
        self.assertEqual(summary["c97_max_spent"], 300)
        self.assertEqual(summary["c97_repeated_node_env"], 7)
        self.assertEqual(summary["c97_repeated_head_pending"], 4)
        self.assertEqual(summary["counts"]["NUCLEUS_NESTED_REPLAY_FAILURE"], 1)

    def test_app_chain_cannot_invent_or_change_a_source_edge(self):
        source = {8805: {"fn": 8753, "arg": 8804}}
        valid = ("NUCLEUS_C129_APP_EDGE:app=8805:fun=8753:arg=8804:"
                 "before=65500:after=65400:context=0:pi_head=false:type_proven=false\n")
        result = parse_app_edges(valid.encode(), source)
        self.assertEqual(result[0]["charged"], 100)
        self.assertEqual(result[0]["app"], 8805)
        with self.assertRaises(AssertionError):
            parse_app_edges(valid.replace("arg=8804", "arg=8803").encode(), source)

    def test_app_argument_obligation_must_match_source_and_charge(self):
        sample = ("NUCLEUS_C130_APP_ARG:app=8805:fun=8753:arg=8804:"
                  "before=65500:after=65260:context=0:state=UNKNOWN:"
                  "judgment=Unknown { residual: ResidualId(\"unresolved-qualified-recursor-heads\") }\n")
        result = parse_arg_obligations(sample.encode(),
                                       {8805: {"fn": 8753, "arg": 8804}})
        self.assertEqual(result[0]["charged"], 240)
        self.assertEqual(result[0]["state"], "UNKNOWN")
        with self.assertRaises(AssertionError):
            parse_arg_obligations(sample.replace("fun=8753", "fun=8752").encode(),
                                  {8805: {"fn": 8753, "arg": 8804}})


if __name__ == "__main__":
    unittest.main()
