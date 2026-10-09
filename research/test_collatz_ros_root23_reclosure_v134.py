"""V134 adversarial support and replay controls for formal root23 and 27 reclosure."""
from __future__ import annotations

import json
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path

from research.collatz_ros_future_controller_v123 import make_join, dump
from research.collatz_ros_chart_overlap_v132 import ADMISSION as V132_ADMISSION
from research.collatz_ros_root23_reclosure_v134 import (
    ADMISSION, ROOT23_ID, ROOT23_ORIGIN, ROOT23_LAW,
    LateRootController, bootstrap, migrate, open_state, root23_family,
)

class FormalRoot23CausalClosureTests(unittest.TestCase):
    def setUp(self):
        self.c=bootstrap()

    def bypair(self):
        return {(w["source"],w["earlier"]):w for w in self.c.state["joins"]}

    def test_v132_retained_without_requalifying_its_formal_scopes(self):
        old=json.loads(Path("research/collatz_ros_state_v132.json").read_text())
        self.assertEqual(old["admission_schema"],V132_ADMISSION)
        self.assertEqual(len(old["joins"]),13)
        self.assertEqual(self.c.state["admission_schema"],ADMISSION)
        self.assertEqual(self.c.state["controller_revision"],5)
        self.assertEqual(self.c.state["grammar"]["revision"],4)
        self.assertEqual(len(self.c.state["joins"]),17)
        self.assertEqual(len(self.c.state["parametric_laws"]),3)
        self.assertEqual(len(self.c.state["conditional_compilers"]),1)
        self.assertEqual(len(self.c.state["chart_instances"]),1)
        self.assertEqual(self.c.state["parametric_laws"][-1],ROOT23_LAW)
        self.assertEqual(old["negative_controls"],self.c.state["negative_controls"])
        self.assertEqual(old["residuals"],self.c.state["residuals"])
        for w in old["joins"]:
            self.assertIn(w,self.c.state["joins"])
        self.assertEqual(self.c.state["global_collatz"],"UNKNOWN")
        self.assertFalse(self.c.state["qed"])
        self.assertFalse(self.c.state["universal_event_producer_proved"])

    def test_typed_root23_live_source_and_exact_clocks(self):
        w=self.bypair()[23,3]
        self.assertEqual((w["source"],w["earlier"],
                          w["source_clock"],w["earlier_clock"],w["common"]),
                         (23,3,7,1,5))
        self.assertEqual(w["origin"],ROOT23_ORIGIN)
        self.assertEqual(w["support"],ROOT23_ID)
        self.assertEqual(w["parents"],[])
        self.assertEqual(self.c.state["support"][ROOT23_ID]["run"],37988274186)
        self.assertEqual(self.c.state["support"][ROOT23_ID]["sha"],
                         "b734f5c5dbb9b52ec1eea6df84e17dd20a3a97d0")

    def test_the_formally_required_delayed_source27_semantics(self):
        joins=self.bypair()
        self.assertEqual((joins[27,23]["source_clock"],
                          joins[27,23]["earlier_clock"],joins[27,23]["common"]),(59,0,23))
        self.assertEqual((joins[27,3]["source_clock"],
                          joins[27,3]["earlier_clock"],joins[27,3]["common"]),(66,1,5))
        self.assertEqual((joins[23,2]["source_clock"],
                          joins[23,2]["earlier_clock"],joins[23,2]["common"]),(11,1,1))
        self.assertEqual((joins[27,2]["source_clock"],
                          joins[27,2]["earlier_clock"],joins[27,2]["common"]),(70,1,1))
        self.assertEqual(joins[27,3]["parents"],[joins[27,23]["id"],joins[23,3]["id"]])
        self.assertEqual(joins[23,2]["parents"],[joins[23,3]["id"],joins[3,2]["id"]])
        self.assertIn(joins[27,2]["parents"][0],
            {joins[27,23]["id"],joins[27,3]["id"]})
        self.assertEqual(joins[27,2]["support"],"v123_composition_theorem")
        self.assertEqual(self.c.status(27)["earlier"],23)
        self.assertEqual(self.c.status(27)["source_clock"],59)
        self.assertEqual(self.c.reclose(),0)

    def test_no_source27_parametric_promotion_and_old_CRT_unknown(self):
        self.assertEqual([law["source_affine"] for law in self.c.state["parametric_laws"]],
                         [[21,72],[9,1536],[23,384]])
        self.assertNotIn([27,2**59],[x["source_affine"] for x in self.c.state["parametric_laws"]])
        self.assertEqual(self.c.state["residuals"][1]["remaining_classes"],159938)
        self.assertIn("UNKNOWN",self.c.state["residuals"][1]["status"])
        self.assertEqual(self.c.state["history"][-1]["no_all_offset_source27_claim"],True)

    def test_all_offset_root23_family_exactly_scoped(self):
        for t in (0,1,2,7,31,256):
            n,p,i,j=root23_family(t)
            self.assertEqual(n,23+384*t)
            self.assertEqual(p,3+54*t)
            self.assertEqual((i,j),(7,1))
            self.assertLess(p,n)
            self.assertEqual(p%6,3)
        self.assertTrue(self.c.admit_root23(1))
        self.assertEqual((self.c.status(407)["earlier"],self.c.status(407)["source_clock"],
                          self.c.status(407)["earlier_clock"],self.c.status(407)["common"]),
                         (57,7,1,86))
        self.assertFalse(self.c.admit_root23(1))
        with self.assertRaises(ValueError): self.c.admit_root23(-1)
        with self.assertRaises(ValueError): self.c.admit_root23(1.0)
        self.assertEqual(self.c.reclose(),0)

    def test_unrelated_true_other_family_is_not_v133_warrant(self):
        w=make_join(21,3,3,2,ROOT23_ID,ROOT23_ORIGIN)
        with self.assertRaises(ValueError):self.c.add(w)
        x=make_join(23,2,11,1,ROOT23_ID,ROOT23_ORIGIN)
        with self.assertRaises(ValueError):self.c.add(x)
        y=make_join(23,3,7,1,"v131_root9_formal_family",ROOT23_ORIGIN)
        with self.assertRaises(ValueError):self.c.add(y)
        with self.assertRaises(ValueError):self.c.admit_root23(True)
        self.c.audit()

    def test_revoking_v133_reopens_just_the_four_dependent_joins(self):
        count=self.c.revoke(ROOT23_ID)
        self.assertEqual(count,4)
        self.assertEqual(len(self.c.state["joins"]),13)
        self.assertEqual(len(self.c.state["archived_joins"]),4)
        pairs=self.bypair()
        for pair in ((23,3),(23,2),(27,3),(27,2)):
            self.assertNotIn(pair,pairs)
        self.assertEqual(self.c.status(27)["earlier"],23)
        self.assertEqual(self.c.status(27)["source_clock"],59)
        self.assertEqual(self.c.status(21)["earlier"],3)
        self.assertEqual(self.c.status(9)["earlier"],3)
        self.assertEqual(self.c.status(15)["earlier"],3)
        with self.assertRaises(ValueError):self.c.admit_root23(7)
        self.assertEqual(self.c.revoke(ROOT23_ID),0)
        self.c.audit()

    def test_revoking_generic_chart_legacy_keeps_root23_formal(self):
        count=self.c.revoke("v131_chart_overlap_generic")
        self.assertEqual(count,4)
        self.assertEqual(len(self.c.state["joins"]),13)
        self.assertEqual(self.c.status(23)["earlier"],3)
        self.assertEqual(self.c.status(27)["earlier"],23)
        self.assertEqual(self.c.status(9)["status"],"UNKNOWN_UNDER_CURRENT_WARRANTS")
        self.assertEqual(self.c.status(15)["status"],"UNKNOWN_UNDER_CURRENT_WARRANTS")
        self.c.audit()

    def test_corrupt_source_slope_endpoint_clock_and_formal_pin(self):
        for mode in ("affine_slope","earlier","clock","common","law","pin","id"):
            state=deepcopy(self.c.state)
            leaf=next(w for w in state["joins"] if
                      w["source"]==23 and w["earlier"]==3)
            if mode=="affine_slope":
                state["parametric_laws"][-1]["source_affine"][1]=385
            elif mode=="earlier":leaf["earlier"]=2
            elif mode=="clock":leaf["source_clock"]=8
            elif mode=="common":leaf["common"]=99
            elif mode=="law":state["parametric_laws"][-1]["theorem"]="MadeUp.QED"
            elif mode=="pin":state["support"][ROOT23_ID]["sha"]="0"*40
            else:leaf["id"]="f"*20
            with self.subTest(mode=mode):
                with self.assertRaises(ValueError):LateRootController(state)

    def test_byte_identical_restart_large_natural_and_closed_grammar(self):
        with tempfile.TemporaryDirectory() as td:
            a,b=Path(td)/"a.json",Path(td)/"b.json"
            x=dump(self.c,a)
            y=dump(open_state(a),b)
            self.assertEqual(x,y)
            self.assertEqual(a.read_bytes(),b.read_bytes())
            self.assertIn(b"1208925819614629174706175",a.read_bytes())
            self.assertEqual(len(json.loads(a.read_text())["joins"]),17)
            self.assertEqual(json.loads(a.read_text())["global_collatz"],"UNKNOWN")

    def test_only_qualified_parent_controller_is_valid_migration(self):
        state=json.loads(Path("research/collatz_ros_state_v132.json").read_text())
        migrated=migrate(state)
        self.assertEqual(len(migrated.state["joins"]),13)
        self.assertEqual(len(migrated.state["parametric_laws"]),3)
        state["joins"][0]["common"]=987654321
        with self.assertRaises(ValueError):migrate(state)


if __name__=="__main__":
    unittest.main()
