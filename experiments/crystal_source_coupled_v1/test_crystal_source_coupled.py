import importlib.util, pathlib, unittest
P=pathlib.Path(__file__).with_name("crystal_source_coupled.py")
S=importlib.util.spec_from_file_location("c",P); c=importlib.util.module_from_spec(S); S.loader.exec_module(c)

class CrystalTests(unittest.TestCase):
    def test_affine_trace(self):
        for n in range(3,80):
            for off,y,q,b,*_ in c.trace_features(n,20):
                k=c.zero_tail_depth(n)+off
                self.assertEqual((2**k)*y,(3**q)*n+b)
    def test_seven_exit(self):
        e=c.first_exit(7)
        self.assertIsNotNone(e)
        self.assertLessEqual(e[0],7)
    def test_census_finds_separators(self):
        z=c.census(range(3,80),post=12,future=12,reverse=40)
        self.assertGreater(z["separator_count"],0)
        self.assertEqual(z["epistemic"],"DISCOVERY_ONLY_BOUNDED")
if __name__=="__main__": unittest.main()
