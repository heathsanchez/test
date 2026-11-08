"""C50 source-worklist loss must be visible without admitting a partial result."""

import importlib
import json
import unittest


def record(seq, stage, parents, completed=0, remaining=90):
    fields = {
        "seq": seq, "stage": stage, "recursor": 147,
        "major_expr": 11, "major_env": 70453,
        "parents": parents, "finish_parents": completed,
        "major_parents": 1 if parents else 0,
        "projected_parents": 0, "active": completed,
        "resolved": 0, "owner_remaining": remaining,
    }
    return "NUCLEUS_C50_LOST:" + json.dumps(fields)


class SourceWorklistLossTests(unittest.TestCase):
    def module(self):
        try:
            return importlib.import_module("probe_c50_loss_ledger")
        except ModuleNotFoundError:
            self.fail("C50 source-worklist loss parser is not implemented")

    def test_failing_nested_child_records_real_pending_parents(self):
        probe = self.module()
        events = probe.parse_loss_events((record(0, "major-exposure", 3, 2) + "\n").encode())
        self.assertEqual(events[0]["parents"], 3)
        self.assertEqual(probe.summarize_losses(events)["with_pending_parents"], 1)
        self.assertEqual(probe.summarize_losses(events)["first_pending_stage"], "major-exposure")

    def test_no_partial_work_is_qualified_as_completed(self):
        probe = self.module()
        events = probe.parse_loss_events((record(0, "owner-exhausted", 0) + "\n").encode())
        result = probe.summarize_losses(events)
        self.assertEqual(result["with_pending_parents"], 0)
        self.assertFalse(result["partial_state_is_a_proof"])

    def test_reject_duplicate_or_impossible_worklist(self):
        probe = self.module()
        for body in (
            record(0, "major-exposure", 1) + "\n" + record(0, "owner-exhausted", 1),
            record(0, "major-exposure", 0, 1),
            record(0, "imagined-success", 2),
        ):
            with self.subTest(body=body), self.assertRaises(ValueError):
                probe.parse_loss_events(body.encode())


if __name__ == "__main__":
    unittest.main()
