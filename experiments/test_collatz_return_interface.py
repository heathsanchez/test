import importlib.util
import pathlib
import unittest

P=pathlib.Path(__file__).with_name('collatz_return_interface.py')
R=pathlib.Path(__file__).with_name('collatz_return_resonance.py')

class ReturnInterfaceTests(unittest.TestCase):
    def test_interface_exists(self):
        self.assertTrue(P.exists(), 'The exact return interface is not implemented')

    def test_countdown_domain_and_switch_reset(self):
        if not P.exists(): self.skipTest('interface absent')
        spec=importlib.util.spec_from_file_location('interface',P)
        m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
        W=((2,1,2),)
        V=((2,1,1),(1,1,2))
        cw=m.certificate(W);cww=m.certificate(W+W);cv=m.certificate(V)
        self.assertEqual((cw['A'],cw['B'],cw['D'],cw['q']), (9,1,3,(-1,1)))
        self.assertEqual(cww['q'],cw['q'])
        self.assertEqual(cww['primitive'],W)
        self.assertTrue(m.admissible(cw,15))
        self.assertFalse(m.admissible(cww,15))
        self.assertFalse(m.admissible(cv,15))
        self.assertEqual(m.replay(W,15),17)
        self.assertEqual(m.replay(V,27),23)
        self.assertEqual(m.injection(cw,cv),-12)
        self.assertEqual(m.valuation(27+1),2)
        self.assertEqual(m.valuation(23+1),3)
        x=1023
        for word in (W,W+W):
            c=m.certificate(word)
            before=m.valuation(x+1)
            x=m.replay(word,x)
            self.assertEqual(m.valuation(x+1),before-c['D'])
        self.assertEqual(m.valuation(x+1),1)
        for L in (3,4,10,100):
            x,y=m.reset_witness(L)
            self.assertEqual(m.replay(V,x),y)
            self.assertEqual(m.valuation(x+1),2)
            self.assertEqual(m.valuation(y+1),L)
        with self.assertRaises(ValueError): m.certificate(((2,1,1),))

    def test_expanding_reset_block(self):
        if not P.exists(): self.skipTest('interface absent')
        spec=importlib.util.spec_from_file_location('interface',P)
        m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
        self.assertTrue(hasattr(m,'reset_block'),'Unbounded reset-block generator is missing')
        z=m.reset_block(2,10)
        self.assertEqual((z['m0'],z['out']),(169727,181247))
        self.assertEqual(z['initial_defect_valuation'],8)
        self.assertEqual(z['final_defect_valuation'],10)
        self.assertTrue(z['no_intermediate_descent'])
        z=m.reset_block(8,27)
        self.assertGreater(z['out'],z['m0'])
        self.assertGreater(z['final_odd_part'],z['initial_odd_part'])

    def test_minimal_budget_has_explicit_exit_boundary(self):
        spec=importlib.util.spec_from_file_location('interface',P)
        m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
        self.assertTrue(hasattr(m,'repeat_budget'),'Minimal future-language budget is missing')
        W=((2,1,2),);c=m.certificate(W)
        self.assertEqual(m.repeat_budget(c,15),1)
        self.assertEqual(m.repeat_budget(c,31),1)
        self.assertEqual(m.repeat_budget(c,127),2)
        self.assertEqual(m.replay(W,15),17)
        self.assertEqual(m.replay(W,31),35)
        self.assertEqual(m.episode(4*17-1)[-1],19)
        self.assertEqual(m.episode(4*35-1)[-1],157)
        self.assertLess(19,4*15-1)
        self.assertGreater(157,4*31-1)

    def test_macro_preserves_intermediate_minimum(self):
        spec=importlib.util.spec_from_file_location('interface',P)
        m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
        self.assertTrue(hasattr(m,'jump_repetitions'),'Certified repetition jump is missing')
        W=((2,1,2),); V=((2,1,1),(1,1,2))
        c=m.certificate(W)
        result=m.jump_repetitions(c,1023)
        self.assertEqual(result['repeats'],3)
        self.assertEqual(result['out'],m.replay(W*3,1023))
        self.assertEqual(result['minimum_n'],4*1023-1)
        # Expanding complete return with an earlier decreasing prefix.
        source,_=m.reset_witness(10)
        c=m.certificate(V+W+W)
        result=m.jump_repetitions(c,source)
        self.assertGreater(result['out'],source)
        self.assertLess(result['minimum_n'],4*source-1)

    def test_nonresonant_switch_has_forced_valuation_drop(self):
        spec=importlib.util.spec_from_file_location('interface',P)
        m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
        self.assertTrue(hasattr(m,'switch_resonance'),'Exact resonance classifier is missing')
        old=m.certificate(((2,1,2),(2,2,2)))
        new=m.certificate(((2,1,2),))
        start=15; end=m.replay(new['word'],start)
        z=m.switch_resonance(old,new,start,end)
        self.assertFalse(z['same_fixed_point'])
        self.assertFalse(z['resonant'])
        self.assertFalse(z['recharge'])
        self.assertEqual((z['valuation_before'],z['injection_valuation'],new['D']), (5,4,3))
        self.assertEqual(z['valuation_after'],1)
        self.assertEqual(z['valuation_after'],min(z['valuation_before'],z['injection_valuation'])-new['D'])
        self.assertEqual(z['cancellation_depth'],0)

    def test_recharge_requires_exact_resonance(self):
        spec=importlib.util.spec_from_file_location('interface',P)
        m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
        self.assertTrue(hasattr(m,'switch_resonance'),'Exact resonance classifier is missing')
        old=m.certificate(((2,1,2),))
        new=m.certificate(((2,1,1),(1,1,2)))
        for L in (3,4,10,100):
            start,end=m.reset_witness(L)
            z=m.switch_resonance(old,new,start,end)
            self.assertTrue(z['resonant'])
            self.assertTrue(z['recharge'])
            self.assertEqual(z['valuation_before'],2)
            self.assertEqual(z['injection_valuation'],2)
            self.assertEqual(z['valuation_after'],L)
            self.assertEqual(z['cancellation_depth'],L+new['D']-2)

    def test_resonant_transition_graph_extracts_only_recursive_sccs(self):
        self.assertTrue(R.exists(),'Resonant transition graph experiment is missing')
        spec=importlib.util.spec_from_file_location('resonance',R)
        g=importlib.util.module_from_spec(spec);spec.loader.exec_module(g)
        nodes={'a','b','c','d'}
        edges={('a','b'),('b','a'),('b','c'),('d','d')}
        self.assertEqual(g.cyclic_sccs(nodes,edges),[['a','b'],['d']])

if __name__=='__main__': unittest.main()
