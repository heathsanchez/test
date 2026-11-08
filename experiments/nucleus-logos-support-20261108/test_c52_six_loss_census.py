"""C52 must bind each diagnostic to the final declaration of an original export."""

import unittest

from probe_c52_six_loss_census import declaration_root, frozen_case_names


class C52SixLoss(unittest.TestCase):
    def test_frozen_six_have_no_duplicate_or_missing_name(self):
        names = frozen_case_names()
        self.assertEqual(len(names), 6)
        self.assertEqual(len(set(names)), 6)
        self.assertIn("magma-list-pair-n7", names)
        self.assertIn("grind-ring-5", names)

    def test_only_final_source_declaration_is_profiled(self):
        data = b'{"ie":37,"nat":8}\n{"def":{"value":37,"type":9}}\n'
        self.assertEqual(declaration_root(data), 37)
        theorem = b'{"ie":12,"nat":8}\n{"thm":{"value":12,"type":9}}\n'
        self.assertEqual(declaration_root(theorem), 12)
        for bad in (b'{"def":{"value":37}}\n{"ie":39}\n',
                    b'{"ie":37}\n', b'{"def":{"value":"37"}}\n'):
            with self.assertRaises(ValueError):
                declaration_root(bad)


if __name__ == "__main__":
    unittest.main()
