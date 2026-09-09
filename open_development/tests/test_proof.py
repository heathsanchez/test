from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest

from open_development import Developer, EvidenceStore, Obligation, ProofProcedureAdapter
from open_development.proof import check

STAGES = json.loads((Path(__file__).resolve().parents[1] / "examples/proof.json").read_text())["stages"]


class ProofProcedureTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / "proof.sqlite"
        self.store = EvidenceStore(self.path)
        self.adapter = ProofProcedureAdapter()

    def tearDown(self):
        self.store.close()
        self.tmp.cleanup()

    def obligation(self, stage, budget):
        return Obligation("proof-procedure", stage, budget, "method")

    def test_two_distinct_procedure_repairs_persist_and_revoke(self):
        first, second = STAGES
        self.assertEqual(Developer(self.store, self.adapter).run(self.obligation(first, 0)).verdict, "unknown")
        one = Developer(self.store, self.adapter).run(self.obligation(first, 3))
        self.assertEqual(one.verdict, "verified")
        self.assertEqual(self.store.state()["capabilities"][one.retained[0]]["attachment"]["procedure"],
                         "half_line_square")
        self.store.close()
        self.store = EvidenceStore(self.path)
        self.assertEqual(Developer(self.store, self.adapter).run(self.obligation(second, 0)).verdict, "unknown")
        two = Developer(self.store, self.adapter).run(self.obligation(second, 3))
        self.assertEqual(two.verdict, "verified")
        self.assertEqual(self.store.state()["capabilities"][two.retained[0]]["attachment"]["procedure"],
                         "interval_affine")
        self.assertNotEqual(one.retained[0], two.retained[0])
        self.store.revoke(two.retained[0], "held-out procedure ablation")
        self.assertEqual(Developer(self.store, self.adapter).run(self.obligation(second, 0)).verdict, "unknown")
        self.assertEqual(Developer(self.store, self.adapter).run(self.obligation(first, 0)).verdict, "verified")

    def test_cold_fixed_and_sham_controls_fail(self):
        first, second = STAGES
        fixed = ProofProcedureAdapter(("coefficientwise",))
        sham = ProofProcedureAdapter(("coefficientwise", "half_line_square"))
        self.assertEqual(Developer(self.store, fixed).run(self.obligation(first, 4)).verdict, "unknown")
        self.assertEqual(Developer(self.store, sham).run(self.obligation(second, 4)).verdict, "unknown")

    def test_certificate_replay_rejects_forgery(self):
        result = Developer(self.store, self.adapter).run(self.obligation(STAGES[0], 3))
        cert = deepcopy(result.evidence.certificate["certificate"])
        cert["D"] = "-1"
        self.assertFalse(check(STAGES[0]["polynomial"], ("ray",), cert))

    def test_unknown_outside_declared_constructor_grammar(self):
        cubic = {"polynomial": {"0": "-1", "3": "1"}, "domain": ["ray"]}
        result = Developer(self.store, self.adapter).run(self.obligation(cubic, 8))
        self.assertEqual(result.verdict, "unknown")


if __name__ == "__main__":
    unittest.main()
