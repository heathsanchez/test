"""Fail-closed contract for the C87 unfinished source recursor census."""
import importlib.util
from pathlib import Path
import unittest


def load_trial():
    file = Path(__file__).with_name("c87_pending_major_trial.py")
    spec = importlib.util.spec_from_file_location("c87_pending_major_trial", file)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


GOOD = ('NUCLEUS_C87_PENDING:{"seq":2,"stage":"owner-exhausted",'
        '"parents":65,"finish_parents":34,"major_parents":31,'
        '"projected_parents":0,"major_const_names":{"147":28,"66":3},'
        '"major_nonconst":0,"owner_remaining":0}')


class PendingMajorContract(unittest.TestCase):
    def test_accepts_exact_histogram_without_inventing_names(self):
        result = load_trial().parse_c87_pending([GOOD])
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["major_const_names"], {"147": 28, "66": 3})
        self.assertEqual(result[0]["major_parents"], 31)

    def test_rejects_missing_or_inconsistent_owner_counts(self):
        with self.assertRaises(AssertionError):
            load_trial().parse_c87_pending([])
        for bad in (
            GOOD.replace('"147":28', '"147":27'),
            GOOD.replace('"finish_parents":34', '"finish_parents":35'),
            GOOD.replace('"owner_remaining":0', '"owner_remaining":5'),
            GOOD.replace('"stage":"owner-exhausted"', '"stage":"major-exposure"'),
        ):
            with self.subTest(bad=bad):
                with self.assertRaises(AssertionError):
                    load_trial().parse_c87_pending([bad])


if __name__ == "__main__":
    unittest.main()
