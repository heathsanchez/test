#!/usr/bin/env python3
import importlib.util, pathlib, sys, unittest
path=pathlib.Path(__file__).with_name("discriminator.py")
spec=importlib.util.spec_from_file_location("discriminator",path)
d=importlib.util.module_from_spec(spec);spec.loader.exec_module(d)
class EngineTests(unittest.TestCase):
 def test_finite_domain_including_empty(self):
  self.assertEqual(d.strings("ab",2),["","a","b","aa","ab","ba","bb"])
 def test_product_and_budget(self):
  self.assertEqual(len(d.domain([{"name":"s","type":"strings","alphabet":"ab","maxlen":2},
   {"name":"x","type":"literals","values":[True,False]}])),14)
  with self.assertRaisesRegex(ValueError,"DOMAIN_BUDGET"):
   d.domain([{"name":"s","type":"strings","alphabet":"ab","maxlen":5}])
 def test_preserve_distinct_unknowns(self):
  self.assertEqual(d.comparison({"status":"TIMEOUT_UNKNOWN"},{"status":"VALUE","value":1}),"UNKNOWN")
  self.assertEqual(d.comparison({"status":"PROCESS_ERROR"},{"status":"VALUE","value":1}),"UNKNOWN")
  self.assertEqual(d.comparison({"status":"VALUE","value":[]},{"status":"VALUE","value":[""]}),"DIFFERENT")
  self.assertEqual(d.comparison({"status":"VALUE","value":"Y"},{"status":"VALUE","value":"Y"}),"EQUAL")
 def test_template_no_custom_logic(self):
  self.assertEqual(d.expand("split({{separator}})",{"separator":"a"},"/tmp"),'split("a")')
  with self.assertRaisesRegex(ValueError,"UNBOUND"):
   d.expand("bad({{unknown}})",{},"/tmp")
 def test_frozen_schema_rejects_generic_misstatement(self):
  with self.assertRaisesRegex(ValueError,"WRONG_MANIFEST"):
   d.execute({"schema":"invalid","sources":[]},"/tmp")
if __name__=="__main__":unittest.main()
