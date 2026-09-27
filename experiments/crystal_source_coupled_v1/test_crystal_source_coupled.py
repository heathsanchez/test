import importlib.util, pathlib, unittest
P=pathlib.Path(__file__).with_name("crystal_source_coupled.py")
S=importlib.util.spec_from_file_location("c",P); c=importlib.util.module_from_spec(S); S.loader.exec_module(c)

class CrystalTests(unittest.TestCase):
    def test_affine_trace(self):
        for n in range(3,80):
            for k,y,q,b,*_ in c.actual_trace(n,30):
                self.assertEqual((2**k)*y,(3**q)*n+b)
    def test_records_are_pre_exit(self):
        for n,row,lab in c.build_records(range(3,100),post=20,future=20,reverse=60):
            basin=c.lower_basin(n,60)
            self.assertIsNone(c.exit_at(n,row[1],basin))
            self.assertIn(lab[0],("EXIT","UNKNOWN"))
    def test_crystal_is_bounded_discovery(self):
        z=c.run(range(3,100))
        self.assertGreater(z["actual_pre_exit_states"],0)
        self.assertIn("impure_classes",z["crystal"])
if __name__=="__main__": unittest.main()
