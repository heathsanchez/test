import unittest
from pathlib import Path

from scripts.check_ledger import load_records, validate_records


ROOT = Path(__file__).resolve().parents[1]
REQUIRED = {
    "id": "TEST-001",
    "date": "2026-09-22",
    "arena_sha": "a" * 40,
    "baseline": {"kind": "test"},
    "obstruction": {"fixture": "test"},
    "residual_class": "format",
    "capability": "test capability",
    "competing_explanation": "test alternative",
    "falsifier": "test falsifier",
    "ablation": "test ablation",
    "protected_suite": ["test"],
    "primary_metric": "retired_instructions",
    "decision_rule": "retain only on a qualified improvement",
    "implementation_commit": None,
    "qualification": None,
    "performance": None,
}


def seed_record(*, decision: str) -> dict:
    return {**REQUIRED, "decision": decision}


class LedgerTests(unittest.TestCase):
    def test_seed_ledger_is_valid(self):
        records = load_records(ROOT / "evidence/ledger.jsonl")
        self.assertEqual(validate_records(records), [])

    def test_retained_entry_requires_obstruction_falsifier_and_run(self):
        record = seed_record(decision="retained")
        for field in ("obstruction", "falsifier", "qualification"):
            with self.subTest(field=field):
                damaged = dict(record)
                damaged.pop(field)
                self.assertTrue(validate_records([damaged]))


if __name__ == "__main__":
    unittest.main()
