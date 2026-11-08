"""C56 fail-closed neutral and rigid snapshot grammar tests."""

import unittest

from probe_c56_neutral_pair import parse_neutral_observation, source_names


class NeutralPairTests(unittest.TestCase):
    def test_recovers_qualified_named_recursor(self):
        stderr = (b'NUCLEUS_C56_PAIR:seq=0:depth=2:context_depth=2:budget=256:'
                  b'left=const:NameId(5):qualified=true:arity=5:major=expr=ExprId(33):env=7:'
                  b'right=free:FreeId(2):arity=0:major=none\n')
        r = parse_neutral_observation(stderr, {5:"Decidable.rec"})
        self.assertEqual(r["neutral_pair_samples"][0]["native_names"]["5"], "Decidable.rec")

    def test_rigid_mismatch_exposes_bounded_source_shape(self):
        stderr = (b'NUCLEUS_C56_RIGID:seq=0:source_expr=ExprId(18960):source_env=71:'
                  b'context_depth=1:remaining=255727:exposed=neutral:Const:spine=4:other=pi\n')
        r = parse_neutral_observation(stderr, {})
        self.assertEqual(r["rigid_type_samples"][0]["source_expr"], 18960)
        self.assertEqual(r["rigid_type_samples"][0]["other"], "pi")

    def test_unknown_source_name_is_rejected(self):
        stderr = (b'NUCLEUS_C56_PAIR:seq=0:depth=0:context_depth=0:budget=5:'
                  b'left=const:NameId(999):qualified=true:arity=5:major=none:'
                  b'right=free:FreeId(0):arity=0:major=none\n')
        with self.assertRaises(ValueError):
            parse_neutral_observation(stderr,{})

    def test_duplicate_sequence_is_rejected(self):
        event=b'NUCLEUS_C56_RIGID:seq=0:source_expr=ExprId(1):source_env=2:context_depth=0:remaining=3:exposed=sort:other=pi\n'
        with self.assertRaises(ValueError):
            parse_neutral_observation(event+event,{})

    def test_native_name_chain(self):
        source = (b'{"in":1,"str":{"pre":0,"str":"Decidable"}}\n'
                  b'{"in":2,"str":{"pre":1,"str":"rec"}}\n')
        self.assertEqual(source_names(source)[2], "Decidable.rec")


if __name__ == "__main__":
    unittest.main()
