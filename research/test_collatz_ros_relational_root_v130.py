"""V130 adversarial tests: compile one V129 all-offset ROOT RELATION as typed
law, never mistake its chosen representative for a lower-source witness.
"""
import json
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path

from research.collatz_ros_future_controller_v123 import make_join,dump
from research.collatz_ros_future_controller_v124 import ADMISSION as V124_ADMISSION
from research.collatz_ros_relational_root_v130 import (
    ADMISSION,RELATIONAL_ORIGIN,RELATIONAL_SUPPORT,FROZEN_LAW,
    RelationalController,bootstrap,migrate,open_state,rooted_family
)

class RelationalRootV130Tests(unittest.TestCase):
    def setUp(self):
        self.c=bootstrap()

    def test_prior_state_and_all_live_warrants_are_preserved(self):
        source=json.loads(Path('research/collatz_ros_state_v124.json').read_text())
        self.assertEqual(source['admission_schema'],V124_ADMISSION)
        self.assertEqual(len(source['joins']),7)
        self.assertEqual(len(self.c.state['joins']),9)
        self.assertEqual(self.c.state['admission_schema'],ADMISSION)
        self.assertEqual(self.c.state['controller_revision'],3)
        self.assertEqual(self.c.state['grammar']['revision'],2)
        self.assertIn('PREFERRED_ROOT_SELECTOR',
                      self.c.state['grammar']['rejected_as_complete'])
        self.assertEqual(self.c.state['parametric_laws'],[FROZEN_LAW])
        self.assertEqual(source['negative_controls'],
                         self.c.state['negative_controls'])
        self.assertEqual(source['residuals'],self.c.state['residuals'])
        self.assertEqual(source['support']['v122_exact_first_join_27'],
                         self.c.state['support']['v122_exact_first_join_27'])
        self.assertEqual(self.c.state['global_collatz'],'UNKNOWN')
        self.assertFalse(self.c.state['qed'])
        self.assertFalse(self.c.state['universal_event_producer_proved'])

    def test_only_one_parametric_law_not_an_enumerated_corpus(self):
        self.assertEqual(len(self.c.state['parametric_laws']),1)
        self.assertEqual(self.c.state['parametric_laws'][0]['source_affine'],[21,72])
        self.assertEqual(self.c.state['parametric_laws'][0]['earlier_affine'],[3,12])
        self.assertEqual(self.c.state['parametric_laws'][0]['endpoint_affine'],[8,27])
        self.assertEqual(self.c.state['parametric_laws'][0]['support'],RELATIONAL_SUPPORT)
        self.assertEqual(self.c.state['support'][RELATIONAL_SUPPORT]['run'],37984356667)
        self.assertEqual(self.c.state['support']['v128_preferred_root_incomplete']['run'],
                         37983621550)

    def test_true_21_to_3_consequence_and_reclose_21_to_2(self):
        witnesses={(j['source'],j['earlier']):j for j in self.c.state['joins']}
        w=witnesses[21,3]
        self.assertEqual((w['source_clock'],w['earlier_clock'],w['common']), (3,2,8))
        self.assertEqual((w['support'],w['origin']),
                         (RELATIONAL_SUPPORT,RELATIONAL_ORIGIN))
        self.assertEqual(w['parents'],[])
        v=witnesses[21,2]
        self.assertEqual((v['source_clock'],v['earlier_clock'],v['common']),(7,2,2))
        self.assertEqual(v['parents'],[w['id'],witnesses[3,2]['id']])
        self.assertEqual(v['support'],'v123_composition_theorem')
        self.assertEqual(self.c.reclose(),0)

    def test_all_offset_law_instantiation_not_extra_root_assumption(self):
        for t in (0,1,2,7,15,100):
            n,p,a,b=rooted_family(t)
            self.assertEqual(n,21+72*t)
            self.assertEqual(p,3+12*t)
            self.assertEqual((a,b),(3,2))
            self.assertLess(p,n)
            self.assertEqual(p%6,n%6)
            self.assertEqual(n%6,3)
        self.assertTrue(self.c.admit_odd_root_family(1))
        self.assertEqual(self.c.status(93)['earlier'],15)
        self.assertEqual(self.c.status(93)['source_clock'],3)
        self.assertEqual(self.c.reclose(),0)
        self.assertFalse(self.c.admit_odd_root_family(1))

    def test_formal_authority_cannot_be_laundered(self):
        # This is an actual true join, but not one of V129's theorem instances.
        unrelated=make_join(21,2,7,2,RELATIONAL_SUPPORT,RELATIONAL_ORIGIN)
        with self.assertRaisesRegex(ValueError,'family slope'):
            self.c.add(unrelated)
        # This is a true V129 family instance but NOT a license to cite V122.
        wrong=make_join(21,3,3,2,'v122_exact_first_join_27',RELATIONAL_ORIGIN)
        with self.assertRaisesRegex(ValueError,'EXACT formal source'):
            self.c.add(wrong)
        # A generic quotient theorem cannot be represented as a direct leaf.
        with self.assertRaises(ValueError):
            self.c.add(make_join(21,3,3,2,'v66_future_quotient',RELATIONAL_ORIGIN))

    def test_forged_all_offset_slope_source_clock_and_parameter(self):
        for q in ((21,3,2,2),(21,3,3,1),(93,3,3,2),(21,15,3,2)):
            # Some edits are false arithmetically, other true but outside theorem;
            # neither can be independently admitted under the V129 proof pin.
            try:
                w=make_join(*q,RELATIONAL_SUPPORT,RELATIONAL_ORIGIN)
            except ValueError:
                continue
            with self.assertRaises(ValueError):
                self.c.add(w)
        with self.assertRaises(ValueError):
            self.c.admit_odd_root_family(-1)
        with self.assertRaises(ValueError):
            self.c.admit_odd_root_family(1.0)

    def test_revoke_V129_archives_direct_and_dependent_not_other_warrants(self):
        removed=self.c.revoke(RELATIONAL_SUPPORT)
        self.assertEqual(removed,2)
        self.assertEqual(len(self.c.state['joins']),7)
        self.assertEqual(len(self.c.state['archived_joins']),2)
        self.assertEqual(self.c.status(21)['status'],
                         'UNKNOWN_UNDER_CURRENT_WARRANTS')
        self.assertEqual(self.c.status(27)['earlier'],23)
        self.assertEqual(self.c.status(11)['earlier'],3)
        self.assertEqual(self.c.status(7)['earlier'],5)
        with self.assertRaises(ValueError):
            self.c.admit_odd_root_family(2)
        self.c.audit()

    def test_corrupted_root_law_and_pins_rejected_on_restart(self):
        for mutate in ('law_slope','proof_sha','support','source','schema'):
            state=deepcopy(self.c.state)
            if mutate=='law_slope':
                state['parametric_laws'][0]['source_affine'][1]=73
            elif mutate=='proof_sha':
                state['support'][RELATIONAL_SUPPORT]['sha']='0'*40
            elif mutate=='support':
                state['support'][RELATIONAL_SUPPORT]['scope']='all Collatz proven'
            elif mutate=='source':
                w=next(v for v in state['joins'] if v['source']==21 and v['earlier']==3)
                w['earlier']=2
            else:
                state['admission_schema']='GLOBAL_COLLATZ_PROVED'
            with self.assertRaises(ValueError):
                RelationalController(state)

    def test_restart_byte_identical_and_large_nat_preserved(self):
        with tempfile.TemporaryDirectory() as td:
            out=Path(td)/'state.json'
            restored=Path(td)/'restored.json'
            a=dump(self.c,out)
            b=dump(open_state(out),restored)
            self.assertEqual(a,b)
            self.assertEqual(out.read_bytes(),restored.read_bytes())
            state=json.loads(out.read_text())
            self.assertEqual(
                state['negative_controls'][2]['changing_source'],
                2**80-1)
            self.assertFalse(open_state(out).admit_odd_root_family(0))

    def test_migration_must_start_from_exact_V124_typed_contract(self):
        stale=deepcopy(self.c.state)
        del stale['parametric_laws']
        with self.assertRaises(ValueError):
            migrate(stale)
        baseline=json.loads(Path('research/collatz_ros_state_v124.json').read_text())
        baseline['joins'][0]['common']=9999
        with self.assertRaises(ValueError):
            migrate(baseline)


if __name__=='__main__': unittest.main()
