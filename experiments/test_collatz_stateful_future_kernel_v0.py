import json
import tempfile
import unittest
from pathlib import Path

import collatz_stateful_future_kernel_v0 as fk
import collatz_q0_rigid_recharge_audit as ra


class StatefulFutureKernelV0Tests(unittest.TestCase):
    def test_greatest_kernel_detects_cycle(self):
        nodes = {"a", "b", "c"}
        succ = {"a": {"b"}, "b": {"a"}, "c": set()}
        live, rounds = fk.greatest_kernel(nodes, succ)
        self.assertEqual(live, {"a", "b"})
        self.assertGreaterEqual(len(rounds), 1)

    def test_future_quotient_preserves_exit_distinction(self):
        nodes = {"a", "b", "c", "d"}
        succ = {"a": {"c"}, "b": {"c"}, "c": set(), "d": set()}
        exits = {"c"}
        classes, qnodes, qsucc, qexits, rounds = fk.refine_future_quotient(
            nodes, succ, exits)
        self.assertEqual(classes["a"], classes["b"])
        self.assertNotEqual(classes["c"], classes["d"])
        self.assertGreaterEqual(rounds, 1)

    def test_exact_active_defect_consumption(self):
        c = ra.certificate(((1, 2, 1),))
        m0 = 7
        self.assertTrue(ra.admissible(c, m0))
        m1 = ra.replay(c, m0)
        d0 = fk.defect(c, m0)
        d1 = fk.defect(c, m1)
        self.assertEqual((1 << c["D"]) * d1, c["A"] * d0)
        self.assertEqual(fk.v2z(d1), fk.v2z(d0) - c["D"])

    def test_small_exact_corpus_runs(self):
        with tempfile.TemporaryDirectory() as td:
            out = Path(td) / "evidence.json"
            evidence = fk.analyze(3, 255, 64, out)
            self.assertTrue(out.exists())
            loaded = json.loads(out.read_text())
            self.assertEqual(loaded["schema"], "COLLATZ_STATEFUL_FUTURE_KERNEL_V0")
            self.assertEqual(loaded["closure_certificate"],
                             evidence["closure_certificate"])
            self.assertIn("CONTROL", loaded["representations"])
            self.assertIn("V2_VECTOR", loaded["representations"])
            self.assertGreaterEqual(
                loaded["transport_audit"].get("active_fuel_consumption_checks", 0), 1)


if __name__ == "__main__":
    unittest.main()
