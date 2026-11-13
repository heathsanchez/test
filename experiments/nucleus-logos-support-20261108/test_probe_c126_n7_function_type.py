"""The C126 source-native trace parser must reject unqualified observations."""

import unittest

from probe_c126_n7_function_type import parse_traces


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


if __name__ == "__main__":
    unittest.main()
