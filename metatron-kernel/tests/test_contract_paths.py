import unittest
from contract_paths import Contract, plan

class Paths(unittest.TestCase):
    def test_candidate_taint_survives_downstream_warranted_leg(self):
        cs=[Contract('missing',{'seed'},{'middle'},False),Contract('known',{'middle'},{'goal'},True)]
        p=plan(cs,{'seed'},'goal')
        self.assertEqual(p['status'],'CANDIDATE_PATH')
        self.assertEqual(p['candidates'],['missing'])
        self.assertEqual(p['contracts'],['known','missing'])
    def test_shared_candidate_counted_once(self):
        cs=[Contract('shared',{'s'},{'a','b'},False),Contract('join',{'a','b'},{'g'},True)]
        self.assertEqual(plan(cs,{'s'},'g')['candidates'],['shared'])
    def test_warranted_path_wins_independent_of_registry_order(self):
        cs=[Contract('candidate',{'s'},{'g'},False),Contract('one',{'s'},{'x'},True),Contract('two',{'x'},{'g'},True)]
        self.assertEqual(plan(cs,{'s'},'g'),plan(list(reversed(cs)),{'s'},'g'))
        self.assertEqual(plan(cs,{'s'},'g')['status'],'WARRANTED_PATH')
    def test_preservation_is_not_transferable(self):
        self.assertEqual(plan([Contract('cost',{'s'},{'g'},True,'cost')],{'s'},'g')['status'],'NO_REGISTERED_PATH')
    def test_no_unseeded_cycles(self):
        cs=[Contract('a',{'b'},{'a'},True),Contract('b',{'a'},{'b'},True)]
        self.assertEqual(plan(cs,set(),'a')['status'],'NO_REGISTERED_PATH')
    def test_observed_shape_does_not_validate_premises(self):
        cs=[Contract('record',{'validated.fields','validated.rules'},{'admitted'},True)]
        self.assertEqual(plan(cs,{'observed.fields'},'admitted')['status'],'NO_REGISTERED_PATH')
    def test_duplicate_ids_rejected(self):
        with self.assertRaises(ValueError): plan([Contract('x',set(),{'a'},True),Contract('x',set(),{'b'},False)],set(),'a')
    def test_limit_is_explicit_unknown(self):
        self.assertEqual(plan([Contract('x',{'s'},{'g'},True)],{'s'},'g',limit=0)['status'],'UNKNOWN_PLANNER_LIMIT')

if __name__=='__main__': unittest.main()
