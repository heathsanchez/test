"""V124 adversarial tests: proof claims require matching *typed* authority."""
import json
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path

from research.collatz_ros_future_controller_v123 import make_join, dump
from research.collatz_ros_future_controller_v124 import (
    ADMISSION, TypedController, bootstrap, migrate, open_state, DIRECT,
    COMPOSED,
)


class TypedWarrantTests(unittest.TestCase):
    def setUp(self):
        self.c = bootstrap()
        self.core = Path("research/collatz_ros_state_v123.json")

    def test_migrates_exact_persistent_V123(self):
        prior = json.loads(self.core.read_text())
        self.assertEqual(prior["schema"], "COLLATZ_ROS_LAWFUL_FUTURE_V123")
        self.assertEqual(len(prior["joins"]), 4)
        self.assertEqual(self.c.state["admission_schema"], ADMISSION)
        self.assertEqual(self.c.state["controller_revision"], 2)
        self.assertEqual(self.c.state["global_collatz"], "UNKNOWN")
        self.assertIs(self.c.state["qed"], False)
        self.assertIs(self.c.state["universal_event_producer_proved"], False)
        self.assertEqual(len(self.c.state["joins"]), 7)
        self.assertEqual(self.c.state["residuals"][1]["remaining_classes"], 159938)
        self.c.audit()

    def test_new_exact_witnesses_and_safe_composition(self):
        active = self.c.state["joins"]
        joins = {(z["source"], z["earlier"]): z for z in active}
        self.assertEqual(tuple(joins[7, 5][x] for x in
            ("source_clock","earlier_clock","common")), (7,0,5))
        self.assertEqual(tuple(joins[5, 4][x] for x in
            ("source_clock","earlier_clock","common")), (2,0,4))
        self.assertEqual(tuple(joins[7, 4][x] for x in
            ("source_clock","earlier_clock","common")), (9,0,4))
        self.assertEqual(joins[7, 5]["support"], "v124_exact_replay")
        self.assertEqual(joins[7, 4]["support"], "v123_composition_theorem")
        self.assertEqual(joins[7, 4]["origin"], COMPOSED)
        self.assertEqual(joins[7, 4]["parents"],
            [joins[7, 5]["id"], joins[5, 4]["id"]])
        self.assertEqual(self.c.reclose(), 0)

    def test_unrelated_formal_source_cannot_launder_a_true_witness(self):
        # These are mathematically TRUE joins, but neither cited theorem
        # establishes that *particular* direct witness.
        false_formal = make_join(5,4,2,0,"v122_exact_first_join_27",
            "LEAN_FORMAL_SOURCE27_EXACT_FIRST_CLOCK")
        with self.assertRaisesRegex(ValueError,"unrelated formal theorem"):
            self.c.add(false_formal)
        schema_subst = make_join(7,5,7,0,"v120_phase_schema", DIRECT)
        with self.assertRaisesRegex(ValueError,"bounded-exact"):
            self.c.add(schema_subst)
        quotient_subst = make_join(7,5,7,0,"v66_future_quotient", DIRECT)
        with self.assertRaises(ValueError):
            self.c.add(quotient_subst)
        self.c.audit()

    def test_correct_arithmetic_with_false_parent_proof_is_not_a_certificate(self):
        # 7->4 @ 9,0 is true, yet cannot be claimed to follow from
        # the 11->3 and 3->2 witnesses.
        first = next(j for j in self.c.state["joins"]
                     if (j["source"],j["earlier"])==(11,3))
        second = next(j for j in self.c.state["joins"]
                      if (j["source"],j["earlier"])==(3,2))
        fake = make_join(7,4,9,0,"v123_composition_theorem",COMPOSED,
                         [first["id"],second["id"]])
        with self.assertRaisesRegex(ValueError,"interface does not connect|NOT entailed"):
            self.c.add(fake)
        self.c.audit()

    def test_source_authority_binds_specific_clocks(self):
        wrong = make_join(27,23,59,0,"v123_bounded_arithmetic",
                          "LEAN_FORMAL_SOURCE27_EXACT_FIRST_CLOCK")
        with self.assertRaisesRegex(ValueError,"unrelated formal"):
            self.c.add(wrong)
        self.assertEqual(self.c.status(27)["source_clock"],59)

    def test_tampered_join_id_parent_or_scope_breaks_restart(self):
        for mutation in ("id","parents","support","origin"):
            state = deepcopy(self.c.state)
            w = next(x for x in state["joins"] if x["source"]==27)
            if mutation=="id":
                w["id"]="f"*20
            elif mutation=="parents":
                w["parents"]=["fake_parent"]
            elif mutation=="support":
                w["support"]="v66_future_quotient"
            elif mutation=="origin":
                w["origin"]=DIRECT
            with self.assertRaises(ValueError):
                TypedController(state)

    def test_unregistered_authority_is_not_warrant(self):
        state = deepcopy(self.c.state)
        state["support"]["fictional_formal"] = {
            "run":1,"sha":"0"*40,"status":"WARRANTED_FORMAL",
            "scope":"prove every natural converges"}
        with self.assertRaises(ValueError):
            TypedController(state)
        state = deepcopy(self.c.state)
        state["support"]["v122_exact_first_join_27"]["sha"]="0"*40
        with self.assertRaises(ValueError):
            TypedController(state)

    def test_archived_parent_cannot_be_reintroduced_as_live(self):
        derived = next(x for x in self.c.state["joins"] if
                       (x["source"],x["earlier"])==(7,4))
        archived = self.c.revoke("v124_exact_replay")
        self.assertEqual(archived,3)
        self.assertEqual(len(self.c.state["joins"]),4)
        self.assertEqual(self.c.status(7)["status"],
                         "UNKNOWN_UNDER_CURRENT_WARRANTS")
        with self.assertRaisesRegex(ValueError,"revoked parent"):
            self.c.add(derived)
        self.c.audit()

    def test_formal_composition_support_revocation_is_scoped(self):
        archived = self.c.revoke("v123_composition_theorem")
        self.assertEqual(archived,1)
        self.assertEqual(len(self.c.state["joins"]),6)
        self.assertEqual(self.c.status(7)["earlier"],5)
        self.assertEqual(self.c.status(27)["earlier"],23)
        self.c.audit()

    def test_origin_without_authorized_type_cannot_be_replayed(self):
        s=deepcopy(self.c.state)
        j=s["joins"][0]
        j["origin"]="THEOREM_PROVED_GLOBALLY"
        with self.assertRaises(ValueError):
            TypedController(s)

    def test_exact_v123_checkpoint_is_not_mutated_and_v124_restores(self):
        initial=self.core.read_bytes()
        with tempfile.TemporaryDirectory() as td:
            a=Path(td)/"v124-state.json"
            b=Path(td)/"v124-restart.json"
            da=dump(self.c,a)
            restored=open_state(a)
            db=dump(restored,b)
            self.assertEqual(da,db)
            self.assertEqual(a.read_bytes(),b.read_bytes())
            self.assertEqual(self.core.read_bytes(),initial)
            self.assertFalse(restored.admit_direct(7,5,7,0))
            self.assertEqual(restored.reclose(),0)

    def test_new_generator_remains_bounded_and_conjecture_unknown(self):
        self.assertEqual(self.c.state["support"]["v124_exact_replay"]["status"],
                         "BOUNDED_EXACT")
        self.assertEqual(self.c.state["support"]["v123_composition_theorem"]["status"],
                         "WARRANTED_FORMAL")
        self.assertEqual(self.c.state["global_collatz"],"UNKNOWN")
        with self.assertRaises(ValueError):
            self.c.admit_direct(2,1,0,0)  # T^0(2)!=1


if __name__ == "__main__":
    unittest.main()
