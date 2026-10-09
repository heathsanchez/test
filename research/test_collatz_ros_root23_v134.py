"""V134 adversarial state migration and exact source-27 causal reclosure.

V133's all-offset root23 theorem is a specifically scoped formal source.
The 27→3 and 27→2 joins are consequences of live existing certificates,
NOT independent theorem leaves or a blanket 27 residue class claim.
"""
import json,tempfile,unittest
from copy import deepcopy
from pathlib import Path

from research.collatz_ros_future_controller_v123 import make_join,dump
from research.collatz_ros_chart_overlap_v132 import ADMISSION as V132_ADMISSION,GENERIC_ID
from research.collatz_ros_root23_v134 import (
    ADMISSION,ROOT23_ORIGIN,ROOT23_SUPPORT,ROOT23_LAW,
    Root23Controller,source23_root3,migrate,bootstrap,open_state
)

class Root23StatefulV134Tests(unittest.TestCase):
    def setUp(self):
        self.c=bootstrap()

    def test_migrated_prior_warrants_exact_without_weakened_source_guards(self):
        old=json.loads(Path('research/collatz_ros_state_v132.json').read_text())
        self.assertEqual(old['admission_schema'],V132_ADMISSION)
        self.assertEqual(len(old['joins']),13)
        s=self.c.state
        self.assertEqual(s['admission_schema'],ADMISSION)
        self.assertEqual(s['controller_revision'],5)
        self.assertEqual(s['grammar']['revision'],4)
        self.assertEqual(len(s['joins']),17)
        self.assertEqual(len(s['parametric_laws']),3)
        self.assertEqual(s['parametric_laws'][-1],ROOT23_LAW)
        self.assertEqual(len(s['conditional_compilers']),1)
        self.assertEqual(len(s['chart_instances']),1)
        self.assertEqual(s['negative_controls'],old['negative_controls'])
        self.assertEqual(s['residuals'],old['residuals'])
        self.assertEqual(s['global_collatz'],'UNKNOWN')
        self.assertIs(s['qed'],False)
        self.assertIs(s['universal_event_producer_proved'],False)
        self.assertEqual(s['support'][ROOT23_SUPPORT]['run'],37988274186)

    def test_source23_parametric_and_source27_typed_consequence_chain(self):
        z={(w['source'],w['earlier']):w for w in self.c.state['joins']}
        expected={(27,23),(11,3),(3,2),(11,2),(7,5),(5,4),(7,4),
                  (21,3),(21,2),(9,3),(9,2),(15,3),(15,2),
                  (23,3),(23,2),(27,3),(27,2)}
        self.assertEqual(set(z),expected)
        self.assertEqual((z[23,3]['source_clock'],z[23,3]['earlier_clock'],z[23,3]['common']),
                         (7,1,5))
        self.assertEqual((z[27,3]['source_clock'],z[27,3]['earlier_clock'],z[27,3]['common']),
                         (66,1,5))
        self.assertEqual((z[23,2]['source_clock'],z[23,2]['earlier_clock'],z[23,2]['common']),
                         (11,1,1))
        self.assertEqual((z[27,2]['source_clock'],z[27,2]['earlier_clock'],z[27,2]['common']),
                         (70,1,1))
        self.assertEqual(z[23,3]['origin'],ROOT23_ORIGIN)
        self.assertEqual(z[23,3]['support'],ROOT23_SUPPORT)
        self.assertEqual(z[27,3]['support'],'v123_composition_theorem')
        self.assertEqual(z[27,3]['parents'],[z[27,23]['id'],z[23,3]['id']])
        self.assertEqual(z[23,2]['parents'],[z[23,3]['id'],z[3,2]['id']])
        self.assertEqual(self.c.status(27)['source_clock'],59)
        self.assertEqual(self.c.status(27)['earlier'],23)
        self.assertEqual(self.c.reclose(),0)

    def test_composed_27_to_2_proof_necessarily_depends_on_root23(self):
        z={(w['source'],w['earlier']):w for w in self.c.state['joins']}
        byid={w['id']:w for w in self.c.state['joins']}
        def all_ancestors(w):
            seen=set()
            todo=list(w['parents'])
            while todo:
                k=todo.pop()
                if k in seen:continue
                seen.add(k)
                todo.extend(byid[k]['parents'])
            return seen
        self.assertIn(z[23,3]['id'],all_ancestors(z[27,2]))
        self.assertIn(z[27,23]['id'],all_ancestors(z[27,2]))
        self.assertIn(z[3,2]['id'],all_ancestors(z[27,2]))

    def test_all_offset_formal_family_parameter_scope(self):
        for t in (0,1,2,7,127):
            n,p,a,b=source23_root3(t)
            self.assertEqual((n,p,a,b),(23+384*t,3+54*t,7,1))
            self.assertTrue(0<p<n)
            self.assertEqual(p%6,3)
        self.assertTrue(self.c.admit_source23_family(1))
        self.assertEqual(self.c.status(407)['earlier'],57)
        self.assertEqual(self.c.status(407)['source_clock'],7)
        self.assertEqual(self.c.status(407)['common'],86)
        self.assertFalse(self.c.admit_source23_family(1))
        self.assertEqual(self.c.reclose(),0)
        for x in (-1,2.0,True):
            with self.assertRaises(ValueError):
                self.c.admit_source23_family(x)

    def test_true_arithmetic_cannot_borrow_an_unrelated_Lean_theorem(self):
        # This exact (23,3) arithmetic is true, but not supported by V122.
        wrong=make_join(23,3,7,1,'v122_exact_first_join_27',ROOT23_ORIGIN)
        with self.assertRaisesRegex(ValueError,'unrelated support'):
            self.c.add(wrong)
        wrong=make_join(23,3,7,1,'v131_root9_formal_family',ROOT23_ORIGIN)
        with self.assertRaises(ValueError):
            self.c.add(wrong)
        self.c.audit()

    def test_wrong_formal_parametric_origin_or_source_rejected(self):
        true_but_outside=make_join(27,3,66,1,ROOT23_SUPPORT,ROOT23_ORIGIN)
        with self.assertRaisesRegex(ValueError,'outside V133'):
            self.c.add(true_but_outside)
        s=deepcopy(self.c.state)
        s['parametric_laws'][-1]['source_affine'][1]=385
        with self.assertRaises(ValueError):
            Root23Controller(s)
        s=deepcopy(self.c.state)
        s['support'][ROOT23_SUPPORT]['sha']='0'*40
        with self.assertRaises(ValueError):
            Root23Controller(s)

    def test_revoking_source23_only_archives_the_four_new_join_records(self):
        removed=self.c.revoke(ROOT23_SUPPORT)
        self.assertEqual(removed,4)
        self.assertEqual(len(self.c.state['joins']),13)
        self.assertEqual(len(self.c.state['archived_joins']),4)
        self.assertEqual(self.c.status(23)['status'],'UNKNOWN_UNDER_CURRENT_WARRANTS')
        self.assertEqual(self.c.status(27)['earlier'],23)
        self.assertEqual(self.c.status(27)['source_clock'],59)
        self.assertEqual(self.c.status(9)['earlier'],3)
        self.assertEqual(self.c.status(21)['earlier'],3)
        self.assertEqual(self.c.status(15)['earlier'],3)
        with self.assertRaises(ValueError):
            self.c.admit_source23_family(1)
        self.c.audit()

    def test_revoking_V131_generic_proof_revokes_source23_specialization_too(self):
        removed=self.c.revoke(GENERIC_ID)
        self.assertEqual(removed,8)
        self.assertEqual(len(self.c.state['joins']),9)
        self.assertEqual(len(self.c.state['archived_joins']),8)
        self.assertEqual(self.c.status(23)['status'],'UNKNOWN_UNDER_CURRENT_WARRANTS')
        self.assertEqual(self.c.status(9)['status'],'UNKNOWN_UNDER_CURRENT_WARRANTS')
        self.assertEqual(self.c.status(15)['status'],'UNKNOWN_UNDER_CURRENT_WARRANTS')
        self.assertEqual(self.c.status(21)['earlier'],3)
        self.assertEqual(self.c.status(27)['earlier'],23)
        self.c.audit()

    def test_80bit_negative_control_and_exact_restart(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'v134-state.json'
            q=Path(td)/'v134-restored.json'
            sha=dump(self.c,p)
            rsha=dump(open_state(p),q)
            self.assertEqual(sha,rsha)
            self.assertEqual(p.read_bytes(),q.read_bytes())
            self.assertIn(b'1208925819614629174706175',p.read_bytes())
            self.assertFalse(open_state(p).admit_source23_family(0))
        self.assertEqual(self.c.state['global_collatz'],'UNKNOWN')

    def test_source27_last_and_first_clock_are_not_conflated(self):
        z={(w['source'],w['earlier']):w for w in self.c.state['joins']}
        self.assertEqual(z[27,23]['source_clock'],59)
        self.assertEqual(z[27,3]['source_clock'],66)
        self.assertEqual(z[27,2]['source_clock'],70)
        self.assertLess(z[27,23]['source_clock'],z[27,3]['source_clock'])
        self.assertLess(z[27,3]['source_clock'],z[27,2]['source_clock'])
        self.assertEqual(self.c.state['residuals'][1]['remaining_classes'],159938)
        self.assertFalse(self.c.state['universal_event_producer_proved'])

if __name__=='__main__':unittest.main()
