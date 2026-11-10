import tempfile
from pathlib import Path
import unittest

from c90_major_allowance import apply_c90
from c90_major_allowance_trial import parse_work


class C90PatchSafety(unittest.TestCase):
    def test_replaces_only_source_major_exposure_caps(self):
        body = '''before min(512)\nlet major_result=if self.replay_projection_major {\n    expose.min(512)\n} else {\n    expose.min(512)\n};\nlet Some(value)=major_result.proven_value() else {\nafter min(512)\n'''
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "machine.rs"
            path.write_text(body)
            apply_c90(path)
            new = path.read_text()
            self.assertEqual(new.count("min(4096)"), 2)
            self.assertEqual(new.count("min(512)"), 2)
            with self.assertRaises(AssertionError):
                apply_c90(path)

    def test_fail_closed_on_anchor_drift(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "machine.rs"
            path.write_text("no expected source major branch")
            with self.assertRaises(AssertionError):
                apply_c90(path)

    def test_work_profile(self):
        line='NUCLEUS_C47_INNER_WORK:outer_spent=457:outer_remaining=261687:exposure_transitions=828695:replay_reserved_units=26350:recursor_worklist_steps=4666:conversion_pairs=665'
        parsed=parse_work([line])
        self.assertEqual(parsed['recursor_worklist_steps'],4666)
        with self.assertRaises(AssertionError):
            parse_work([])


if __name__ == "__main__":
    unittest.main()
