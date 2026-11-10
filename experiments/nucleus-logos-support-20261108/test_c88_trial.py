"""C88 exact suspended-major identity: same recursor is insufficient."""
import importlib.util
from pathlib import Path
import unittest


def module():
    path = Path(__file__).with_name("c88_exact_pending_trial.py")
    spec = importlib.util.spec_from_file_location("c88_exact_pending_trial", path)
    loaded = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(loaded)
    return loaded


LINE = ('NUCLEUS_C88_EXACT_PENDING:{"seq":2,"major_parents":5,'
        '"unique_exact_neutrals":3,"exact_repeats":2,'
        '"full_captured_spine_and_environment":true,'
        '"same_source_name_alone_insufficient":true}')


class PendingIdentity(unittest.TestCase):
    def test_identifies_exact_repeats_not_name_only(self):
        result = module().parse_c88([LINE])
        self.assertEqual(result[0]["exact_repeats"], 2)
        self.assertEqual(result[0]["unique_exact_neutrals"], 3)

    def test_rejects_missing_or_inconsistent_partitions(self):
        with self.assertRaises(AssertionError):
            module().parse_c88([])
        for bad in (
            LINE.replace('"unique_exact_neutrals":3', '"unique_exact_neutrals":4'),
            LINE.replace('"full_captured_spine_and_environment":true', '"full_captured_spine_and_environment":false'),
            LINE.replace('"same_source_name_alone_insufficient":true', '"same_source_name_alone_insufficient":false'),
        ):
            with self.subTest(bad=bad):
                with self.assertRaises(AssertionError):
                    module().parse_c88([bad])


if __name__ == "__main__":
    unittest.main()
