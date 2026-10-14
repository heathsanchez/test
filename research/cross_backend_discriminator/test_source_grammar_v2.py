import unittest,importlib.util,pathlib
p=pathlib.Path(__file__).with_name("source_grammar_v2.py")
s=importlib.util.spec_from_file_location("g",p);g=importlib.util.module_from_spec(s);s.loader.exec_module(g)
class V2(unittest.TestCase):
 def test_rust_bracket_and_dot_candidate_without_operation_names(self):
  d='+++ b/tests/cases.rs\n+ yields!(k, "[1,2,3][[]]", json!([]));\n+ yields!(k, ".a", json!({"a":1}));\n'
  lit,inputs,loc=g.test_literals(d)
  self.assertIn("[1,2,3][[]]",lit);self.assertIn(".a",lit)
  self.assertIn([],inputs);self.assertIn({"a":1},inputs)
  self.assertGreater(len(loc),0)
 def test_go_raw_string_test(self):
  tick=chr(96)
  d='+++ b/operator_test.go\n+ assert('+tick+'.[[1]]'+tick+', "{}")\n'
  lit,inputs,_=g.test_literals(d)
  self.assertIn(".[[1]]",lit)
  self.assertIn({},inputs)
 def test_no_source_test_no_claim(self):
  self.assertEqual(g.test_literals('+++ b/src/prod.rs\n+ x="[1][[]]";\n')[0],[])
 def test_zero_outputs_not_same_as_one_empty_array(self):
  self.assertEqual(g.compare({"status":"VALUE","values":[]},{"status":"VALUE","values":[[]]}),"DIFFERENT")
  self.assertEqual(g.compare({"status":"PROCESS_ERROR"},{"status":"VALUE","values":[1]}),"UNKNOWN_INCOMPLETE")
 def test_native_syntax_oracle(self):
  self.assertTrue(g.syntactic("[1,2,3][[]]"))
  self.assertFalse(g.syntactic("this is not jq syntax %"))
 def test_no_false_action_from_missing_reference(self):
  self.assertEqual(g.compare({"status":"VALUE","values":[1]},{"status":"REFERENCE_ABLATED"}),"UNKNOWN_INCOMPLETE")
if __name__=="__main__":unittest.main()
