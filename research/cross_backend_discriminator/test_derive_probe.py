import unittest,importlib.util,pathlib,json
s=importlib.util.spec_from_file_location("miner",pathlib.Path(__file__).with_name("derive_probe.py"))
m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
class T(unittest.TestCase):
  def test_lexical_minimal_filter_and_input_without_hardcoded_operation(self):
    diff='+++ b/src/tests.rs\n+    check(r#".[[]]"#, "[]");\n+    other(".a", "{}");'
    o=m.collect(diff)
    self.assertEqual(o["status"],"CANDIDATE_SOURCE_DERIVED_PROBES")
    self.assertIn(".[[]]",o["filters"])
    self.assertIn(".a",o["filters"])
    self.assertIn([],o["inputs"])
    self.assertIn({},o["inputs"])
  def test_non_test_code_cannot_masquerade_as_frozen_test_semantics(self):
    diff='+++ b/src/main.rs\n+    let filter = ".[[]]";\n'
    self.assertEqual(m.collect(diff)["status"],"UNKNOWN_NO_SOURCE_DERIVED_FILTER")
  def test_no_test_lit_is_unknown_not_success(self):
    self.assertEqual(m.collect('+++ b/tests/tests.rs\n+    assert!(ok);\n')["filters"],[])
  def test_bounded_cartesian_domain(self):
    diff='+++ b/tests/parity.rs\n'
    for i in range(100):diff+=f'+   check(".a{i}", "[1]");\n'
    r=m.collect(diff)
    self.assertLessEqual(len(r["filters"]),42)
    self.assertLessEqual(len(r["filters"])*len(r["inputs"]),462)
  def test_invalid_quote_is_not_a_valid_semantic_discovery(self):
    self.assertEqual(m.collect('+++ b/tests/parity.rs\n+ hello("unterminated\\x00");\n')["filters"],[])
if __name__=="__main__":unittest.main()
