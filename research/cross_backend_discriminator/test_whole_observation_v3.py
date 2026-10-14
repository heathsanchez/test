import pathlib,importlib.util,unittest,sys
p=pathlib.Path(__file__).with_name("whole_observation_v3.py")
sys.path.insert(0,str(p.parent))
spec=importlib.util.spec_from_file_location("whole_v3",p)
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class WholeSource(unittest.TestCase):
 def test_single_complete_go_raw_expression_not_nested_fragments(self):
  b=chr(96)
  full='match("(?<key>.*?)"; "g") | .captures'
  d='+++ b/pkg/example/operator_test.go\n+ expression: '+b+full+b+', expected: []string{"ok"}\n'
  r=m.observations(d)
  self.assertEqual(len(r),1)
  self.assertEqual(r[0]["program"],full)
  self.assertEqual(r[0]["source_role"],"GO_FULL_EXPRESSION_FIELD")
 def test_docs_explicit_expected_relation(self):
  b=chr(96)
  d='+++ b/docs/example.dj\n+- '+b+'[1,2,3] | .[] --> 1 2 3'+b+'\n'
  r=m.observations(d)
  self.assertEqual(len(r),1)
  self.assertEqual(r[0]["program"],"[1,2,3] | .[]")
 def test_syntactic_program_absent_is_unknown(self):
  self.assertEqual(m.observations('+++ b/pkg/source.go\n+ expr: "abc"\n'),[])
 def test_no_cross_input_invention_from_regex_literal(self):
  b=chr(96)
  d='+++ b/pkg/example/operator_test.go\n+ expression: '+b+'capture("(?<value>.+)";"g") | .captures'+b+'\n'
  r=m.observations(d)
  self.assertEqual(len(r),1)
  self.assertNotEqual(r[0]["program"],"(?<value>.+)")
 def test_original_rust_test_macro(self):
  d='+++ b/path/tests.rs\n+ yields!(idx, ".[[]]", json!([]));\n'
  self.assertTrue(any(v["program"]==".[[]]" for v in m.observations(d)))
 def test_existing_native_executor_keeps_unknown_distinct(self):
  self.assertEqual(m.old.compare({"status":"PROCESS_ERROR"},{"status":"VALUE","values":[[]]}),"UNKNOWN_INCOMPLETE")
if __name__=="__main__":unittest.main()
