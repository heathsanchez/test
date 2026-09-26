import unittest
import collatz_crystal_future_quotient_v1 as fq

class SeparatorRefinementTests(unittest.TestCase):
    def test_separator_resolves_coarse_cycle(self):
        rows=[
            {"id":"a","exit":False,"next":["b"],"base":"control","v3":0},
            {"id":"b","exit":False,"next":["a"],"base":"control","v3":1},
            {"id":"a0","exit":True,"next":[],"base":"control","v3":0},
            {"id":"b1","exit":True,"next":[],"base":"control","v3":1}]
        result=fq.compile_with_separators(rows,("base",),("v3",))
        self.assertEqual(result["admitted_separators"],["v3"])
        self.assertEqual(result["kernel"],[])

    def test_constant_separator_is_not_admitted(self):
        rows=[
            {"id":"a","exit":False,"next":["b"],"base":"control","noise":7},
            {"id":"b","exit":False,"next":["a"],"base":"control","noise":7}]
        result=fq.compile_with_separators(rows,("base",),("noise",))
        self.assertEqual(result["admitted_separators"],[])
        self.assertTrue(result["kernel"])

    def test_unresolved_cycle_is_reported(self):
        rows=[
            {"id":"a","exit":False,"next":["b"],"base":"control"},
            {"id":"b","exit":False,"next":["a"],"base":"control"}]
        result=fq.compile_with_separators(rows,("base",),())
        self.assertEqual(result["status"],"EXACT_RECURRENT_OBSTRUCTION")
        self.assertTrue(result["obstruction"]["cycle"])

if __name__=="__main__":
    unittest.main()
