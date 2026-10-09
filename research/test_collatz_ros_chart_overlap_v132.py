"""V132 adversarial qualification: generic formal chart soundness is not a
license to invent chart premises or attach an unrelated family theorem.
"""
import json
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path

from research.collatz_ros_future_controller_v123 import make_join,dump
from research.collatz_ros_relational_root_v130 import ADMISSION as V130_ADMISSION
from research.collatz_ros_chart_overlap_v132 import (
    ADMISSION, CHART_ORIGIN, ROOT9_ORIGIN, ROOT9_ID,
    GENERIC_ID, CHART_EXACT_ID, ROOT9_LAW, GENERIC_COMPILER,
    ChartController, migrate, bootstrap, open_state,
    chart_hypotheses, root9_family,
)

class SourceChartTypedProofTests(unittest.TestCase):
    def setUp(self):
        self.c=bootstrap()

    def test_verified_v130_checkpoint_migrates_without_dilution(self):
        old=json.loads(Path('research/collatz_ros_state_v130.json').read_text())
        self.assertEqual(old['admission_schema'],V130_ADMISSION)
        self.assertEqual(len(old['joins']),9)
        self.assertEqual(len(self.c.state['joins']),13)
        self.assertEqual(self.c.state['admission_schema'],ADMISSION)
        self.assertEqual(self.c.state['controller_revision'],4)
        self.assertEqual(self.c.state['grammar']['revision'],3)
        self.assertEqual(self.c.state['grammar']['active'],'SOURCE_INDEXED_TWO_CLOCK')
        self.assertEqual(len(self.c.state['parametric_laws']),2)
        self.assertEqual(len(self.c.state['conditional_compilers']),1)
        self.assertEqual(len(self.c.state['chart_instances']),1)
        self.assertEqual(self.c.state['parametric_laws'][1],ROOT9_LAW)
        self.assertEqual(self.c.state['conditional_compilers'][0],GENERIC_COMPILER)
        self.assertEqual(old['negative_controls'],self.c.state['negative_controls'])
        self.assertEqual(old['residuals'],self.c.state['residuals'])
        self.assertEqual(old['support']['v122_exact_first_join_27'],
                         self.c.state['support']['v122_exact_first_join_27'])
        self.assertEqual(self.c.state['global_collatz'],'UNKNOWN')
        self.assertIs(self.c.state['qed'],False)
        self.assertIs(self.c.state['universal_event_producer_proved'],False)

    def test_formal_root9_and_generic_source15_have_distinct_authorities(self):
        joins={(q['source'],q['earlier']):q for q in self.c.state['joins']}
        v=joins[9,3]
        self.assertEqual((v['source_clock'],v['earlier_clock'],v['common']),(9,1,5))
        self.assertEqual((v['origin'],v['support']),(ROOT9_ORIGIN,ROOT9_ID))
        self.assertEqual(v['parents'],[])
        x=joins[15,3]
        self.assertEqual((x['source_clock'],x['earlier_clock'],x['common']),(8,1,5))
        self.assertEqual((x['origin'],x['support']),(CHART_ORIGIN,CHART_EXACT_ID))
        self.assertIn(x['id'],self.c.state['chart_instances'])
        self.assertEqual(self.c.state['chart_instances'][x['id']]['theorem_support'],GENERIC_ID)
        self.assertEqual(self.c.state['support'][GENERIC_ID]['status'],'WARRANTED_FORMAL')
        self.assertEqual(self.c.state['support'][CHART_EXACT_ID]['status'],'BOUNDED_EXACT')

    def test_reclose_retains_two_clocks_and_parent_ids(self):
        joins={(q['source'],q['earlier']):q for q in self.c.state['joins']}
        earlier=joins[3,2]
        for source,sc in ((9,13),(15,12)):
            child=joins[source,3]
            composite=joins[source,2]
            self.assertEqual((composite['source_clock'],composite['earlier_clock']), (sc,1))
            self.assertEqual(composite['parents'],[child['id'],earlier['id']])
            self.assertEqual(composite['support'],'v123_composition_theorem')
        self.assertEqual(self.c.reclose(),0)
        self.assertEqual(self.c.status(27)['source_clock'],59)

    def test_generic_chart_premises_are_checked_symbolically(self):
        p=chart_hypotheses(15,3,8,1,3,81,0)
        self.assertEqual((p['derived_source'],p['derived_earlier'],p['derived_endpoint']),
                         (15,3,5))
        self.assertEqual(p['source_chart']['source_slope'],768)
        self.assertEqual(p['earlier_chart']['source_slope'],162)
        self.assertEqual(p['source_chart']['endpoint_slope'],243)
        self.assertEqual(p['earlier_chart']['endpoint_slope'],243)
        self.assertEqual(p['source_chart']['odd_count'],4)
        self.assertEqual(p['earlier_chart']['odd_count'],1)
        # A fresh all-offset V131 chart instance remains bounded-exact until
        # that specific set of premises is itself checked in Lean.
        self.assertTrue(self.c.admit_chart(15,3,8,1,3,81,1))
        self.assertEqual(self.c.status(783)['earlier'],165)
        self.assertEqual(self.c.status(783)['source_clock'],8)
        self.assertEqual(self.c.status(783)['common'],248)
        self.assertFalse(self.c.admit_chart(15,3,8,1,3,81,1))

    def test_invalid_chart_slope_guard_and_endpoint_denied(self):
        invalid=[
            (15,3,8,1,3,80,0),  # unequal endpoint slope
            (15,3,8,1,3,82,0),  # unequal endpoint slope
            (21,3,3,2,1,3,0),  # source coefficient mismatch
            (3,15,8,1,3,81,0), # predecessor not smaller
            (15,3,8,1,0,81,0), # zero-slope outside active checker
            (15,3,8,1,3,81,-1),
            (15,3,8,1,3,81,1.0),
        ]
        for args in invalid:
            with self.subTest(args=args):
                with self.assertRaises(ValueError):
                    self.c.admit_chart(*args)

    def test_generic_does_not_launder_an_unrelated_formal_root9_claim(self):
        fake=make_join(15,3,8,1,ROOT9_ID,ROOT9_ORIGIN)
        with self.assertRaises(ValueError):
            self.c.add(fake)
        true_but_wrong_origin=make_join(9,3,9,1,GENERIC_ID,CHART_ORIGIN)
        with self.assertRaises(ValueError):
            self.c.add(true_but_wrong_origin)
        # A TRUE but previously unseen t=1 join cannot borrow the cached
        # t=0 generic chart evidence; its own precise premise record is needed.
        no_premises=make_join(783,165,8,1,CHART_EXACT_ID,CHART_ORIGIN)
        with self.assertRaises(ValueError):
            self.c.add(no_premises)
        self.c.audit()

    def test_formal_root9_all_offset_scope_not_a_new_universal_cover(self):
        for t in (0,1,2,7,101):
            n,p,i,j=root9_family(t)
            self.assertEqual((n,p,i,j),(9+1536*t,3+486*t,9,1))
            self.assertLess(p,n)
            self.assertEqual(n%6,p%6)
        self.assertTrue(self.c.admit_root9(1))
        self.assertEqual(self.c.status(1545)['earlier'],489)
        self.assertEqual(self.c.status(1545)['source_clock'],9)
        self.assertEqual(self.c.status(1545)['common'],734)
        self.assertFalse(self.c.admit_root9(1))
        with self.assertRaises(ValueError):
            self.c.admit_root9(-1)
        with self.assertRaises(ValueError):
            self.c.admit_root9(1.0)

    def test_corrupted_generic_premise_and_source_pin_fail_restart(self):
        original=deepcopy(self.c.state)
        valid=next(w for w in original['joins'] if w['origin']==CHART_ORIGIN)
        for kind in ('slope','odds','endpoint','missing','pin','theorem','id'):
            s=deepcopy(original)
            cid=valid['id']
            if kind=='slope':
                s['chart_instances'][cid]['earlier_chart']['endpoint_slope']=244
            elif kind=='odds':
                s['chart_instances'][cid]['source_chart']['odd_count']=5
            elif kind=='endpoint':
                s['chart_instances'][cid]['derived_endpoint']=6
            elif kind=='missing':
                del s['chart_instances'][cid]
            elif kind=='pin':
                s['support'][GENERIC_ID]['sha']='0'*40
            elif kind=='theorem':
                s['conditional_compilers'][0]['theorem']='CollatzFinal.CollatzIsProved'
            else:
                for w in s['joins']:
                    if w['id']==cid: w['id']='f'*20
            with self.subTest(kind=kind):
                with self.assertRaises(ValueError):
                    ChartController(s)

    def test_nonmatching_formal_parametric_law_rejected(self):
        s=deepcopy(self.c.state)
        s['parametric_laws'][1]['source_affine'][1]=1537
        with self.assertRaises(ValueError):
            ChartController(s)
        s=deepcopy(self.c.state)
        s['parametric_laws'].append({'claim':'all odd roots converge'})
        with self.assertRaises(ValueError):
            ChartController(s)

    def test_revoking_root9_is_precise(self):
        removed=self.c.revoke(ROOT9_ID)
        self.assertEqual(removed,2)
        self.assertEqual(len(self.c.state['joins']),11)
        self.assertEqual(self.c.status(9)['status'],'UNKNOWN_UNDER_CURRENT_WARRANTS')
        self.assertEqual(self.c.status(15)['earlier'],3)
        self.assertEqual(self.c.status(21)['earlier'],3)
        self.assertEqual(self.c.status(27)['earlier'],23)
        with self.assertRaises(ValueError):
            self.c.admit_root9(1)
        self.c.audit()

    def test_revoking_chart_arithmetic_is_precise(self):
        removed=self.c.revoke(CHART_EXACT_ID)
        self.assertEqual(removed,2)
        self.assertEqual(len(self.c.state['joins']),11)
        self.assertEqual(self.c.status(15)['status'],'UNKNOWN_UNDER_CURRENT_WARRANTS')
        self.assertEqual(self.c.status(9)['earlier'],3)
        self.assertEqual(len(self.c.state['chart_instances']),1)
        self.c.audit()

    def test_generic_formal_revocation_invalidates_all_dependents(self):
        removed=self.c.revoke(GENERIC_ID)
        self.assertEqual(removed,4)
        self.assertEqual(len(self.c.state['joins']),9)
        self.assertEqual(len(self.c.state['archived_joins']),4)
        self.assertEqual(self.c.status(9)['status'],'UNKNOWN_UNDER_CURRENT_WARRANTS')
        self.assertEqual(self.c.status(15)['status'],'UNKNOWN_UNDER_CURRENT_WARRANTS')
        self.assertEqual(self.c.status(21)['earlier'],3)
        self.assertEqual(self.c.status(27)['earlier'],23)
        self.assertEqual(self.c.revoke(GENERIC_ID),0)
        self.c.audit()

    def test_80bit_nat_and_byte_identical_restart(self):
        with tempfile.TemporaryDirectory() as td:
            a=Path(td)/'state.json'
            b=Path(td)/'restored.json'
            da=dump(self.c,a)
            db=dump(open_state(a),b)
            self.assertEqual(da,db)
            self.assertEqual(a.read_bytes(),b.read_bytes())
            self.assertIn(b'1208925819614629174706175',a.read_bytes())
            self.assertEqual(
                json.loads(a.read_text())['negative_controls'][2]['changing_source'],
                2**80-1)

    def test_previous_controller_snapshot_is_immutable(self):
        old=Path('research/collatz_ros_state_v130.json').read_bytes()
        snapshot=json.loads(old)
        restored=migrate(snapshot)
        self.assertEqual(len(restored.state['joins']),9)
        self.assertEqual(restored.state['grammar']['revision'],3)
        self.assertEqual(len(restored.state['conditional_compilers']),1)
        self.assertEqual(Path('research/collatz_ros_state_v130.json').read_bytes(),old)
        self.c.audit()

if __name__=='__main__':
    unittest.main()
