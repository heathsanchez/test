import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("budget_ladder", ROOT / "runner.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class BudgetLadderTests(unittest.TestCase):
    def test_budget_patch_changes_only_judgment_limit(self):
        source = "start\n            judgment_steps: 65_536,\nend\n"
        changed, diff = module.patch_budget(source, 524_288)
        self.assertIn("judgment_steps: 524_288", changed)
        self.assertIn("-            judgment_steps: 65_536", diff)
        self.assertIn("+            judgment_steps: 524_288", diff)
        self.assertEqual(changed.replace("524_288", "65_536"), source)

    def test_budget_patch_fail_closed_if_source_layout_changes(self):
        with self.assertRaises(ValueError):
            module.patch_budget("judgment_steps: 65_537,", 524_288)
        with self.assertRaises(ValueError):
            module.patch_budget("judgment_steps: 65_536,\njudgment_steps: 65_536,", 524_288)


if __name__ == "__main__":
    unittest.main()
