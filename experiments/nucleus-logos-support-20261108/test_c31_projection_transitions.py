import unittest

from probe_c31_projection_transitions import parse_record


class C31ObserverParseTests(unittest.TestCase):
    def test_source_and_charge_are_kept_distinct(self):
        record = parse_record(
            "NUCLEUS_C31_PROJECTION:seq=8:depth=15:step=2:source=stuck:field=0:spine=2:"
            "origin=expr=ExprId(1):env=900:levels=0:binding=bvar=0:node=812:"
            "receiver=hops=2:max_index=0:terminal=app:arity=2:"
            "head=Some(Const { name: NameId(1), levels: [] }):expr=ExprId(55):env=20:"
            "result=UNKNOWN:owner_before=Some(1000):owner_after=Some(752):charged=Some(248)"
        )
        self.assertEqual(record["source"], "stuck:field=0:spine=2")
        self.assertEqual(record["origin"], "expr=ExprId(1):env=900:levels=0:binding=bvar=0:node=812")
        self.assertEqual(record["charged"], 248)
        self.assertEqual(record["result"], "UNKNOWN")

    def test_unrelated_output_is_not_an_observation(self):
        self.assertIsNone(parse_record("NUCLEUS_C29_MAJOR_STEP:seq=0"))

    def test_unpaid_source_work_is_rejected(self):
        with self.assertRaises(AssertionError):
            parse_record(
                "NUCLEUS_C31_PROJECTION:seq=0:depth=1:step=0:source=stuck:field=0:"
                "origin=expr=ExprId(1):receiver=app:result=UNKNOWN:"
                "owner_before=Some(100):owner_after=Some(90):charged=Some(0)"
            )


if __name__ == "__main__":
    unittest.main()
