import unittest
from research.unified_consequence_runtime.v54_native_admission import integrate
class NativeV54Contract(unittest.TestCase):
    def setUp(self):
        self.r={"verdict":"PASS_V54_TWO_GENERATION_COMPOUNDING",
            "gates":{f"g{i}":True for i in range(9)},
            "O1":{"operator":{"kind":"TOKEN_REWRITE","src":"<","dst":"<="},"scope_word":"if"},
            "O2_target":{"operator":{"kind":"TOKEN_REWRITE","src":"and","dst":"or"}},
            "causal":{"cold":False,"after_O1_only":False,"after_O1_O2":True,
                      "O1_ablated_O2_present":False},
            "claim_boundary":"Frozen source-native token emission"}
    def test_original_causal_contract_rejects_false_gain(self):
        self.r["causal"]["after_O1_O2"]=False
        with self.assertRaises(ValueError):integrate(self.r)
    def test_original_causal_contract_rejects_wrong_scope(self):
        self.r["O1"]["scope_word"]="while"
        with self.assertRaises(ValueError):integrate(self.r)
    def test_lineage_reclosure(self):
        x=integrate(self.r)
        self.assertEqual(x["after_withdrawal"],{"O1":False,"O2":False})
        self.assertEqual(x["after_restoration"],{"O1":True,"O2":True})
        self.assertTrue(x["old_warrants_remain_revoked"])
if __name__=="__main__":unittest.main()
