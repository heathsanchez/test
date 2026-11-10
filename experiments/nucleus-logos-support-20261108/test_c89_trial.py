import unittest

from c89_source_major_trial import parse_c89


class C89Parsing(unittest.TestCase):
    def test_source_expr_groups_are_a_partition(self):
        lines = [
            'NUCLEUS_C89_MAJOR_SOURCE:{"seq":2,"major_parents":3,"source_expr_groups":[[11,2],[42,1]],"unique_source_exprs":2,"unique_major_closures":3,"major_closure_repeats":0,"missing_major_source":0}',
        ]
        self.assertEqual(parse_c89(lines)[0]["source_expr_groups"], [[11, 2], [42, 1]])

    def test_missing_source_is_rejected(self):
        lines = [
            'NUCLEUS_C89_MAJOR_SOURCE:{"seq":2,"major_parents":3,"source_expr_groups":[[11,2]],"unique_source_exprs":1,"unique_major_closures":2,"major_closure_repeats":0,"missing_major_source":0}',
        ]
        with self.assertRaises(AssertionError):
            parse_c89(lines)

    def test_duplicate_sequence_is_rejected(self):
        line = 'NUCLEUS_C89_MAJOR_SOURCE:{"seq":1,"major_parents":1,"source_expr_groups":[[11,1]],"unique_source_exprs":1,"unique_major_closures":1,"major_closure_repeats":0,"missing_major_source":0}'
        with self.assertRaises(AssertionError):
            parse_c89([line, line])


if __name__ == "__main__":
    unittest.main()
