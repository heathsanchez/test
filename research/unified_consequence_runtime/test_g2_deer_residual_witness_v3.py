"""V3 frozen controls: residual-sourced regex discriminator, exposed only."""
import json
from pathlib import Path
import unittest
from . import g2_deer_residual_witness_v3 as v3
from . import g2_deer_import_composition_v2 as v2

SAMPLE=b'''import pytest
@pytest.mark.parametrize("name", ["valid\\n", "valid \\n"])
def test_value(name):
    assert name
class TestAPI:
    @pytest.mark.parametrize("name", ["valid\\n", "valid\\n\\n"])
    def test_api(self,name):
        assert name
'''
JUNIT='''<testsuites><testsuite>
<testcase classname="tests.test_contract" name="test_value[valid\\n]"><failure/></testcase>
<testcase classname="tests.test_contract" name="test_value[valid \\n]"/>
<testcase classname="tests.test_contract.TestAPI" name="test_api[valid\\n]"><failure/></testcase>
<testcase classname="tests.test_contract.TestAPI" name="test_api[valid\\n\\n]"/>
</testsuite></testsuites>'''
SELECTORS=["backend/tests/test_contract.py::test_value","backend/tests/test_contract.py::TestAPI::test_api"]
RELEVANT=b'import re\nRULE=re.compile(r"^[a-z]+$")\ndef valid(s):return bool(RULE.match(s))\n'
FULLMATCH=b'import re\nRULE=re.compile(r"^[a-z]+$")\ndef valid(s):return bool(RULE.fullmatch(s))\n'
DISJOINT=b'import re\nRULE=re.compile(r"^[0-9]+$")\ndef valid(s):return bool(RULE.match(s))\n'


class FrozenWitnessV3(unittest.TestCase):
    def test_01_frozen_v3_science_scope(self):
        doc=v3.frozen()
        self.assertEqual(doc['status'],'FROZEN_BEFORE_ANY_NEW_CANDIDATE_NATIVE_RUN')
        self.assertIn('G2/G3/G4/G5/G6 UNKNOWN',doc['never_claim'])
        self.assertEqual(doc['parent_v2_run'],39166845563)

    def test_02_only_original_failed_parametrized_literal_witness(self):
        failures=v2.parse_native_cases(JUNIT.encode(),SELECTORS)
        obs=v3.source_neutral_residuals(SAMPLE,SELECTORS,failures)
        self.assertEqual(obs,['valid\n'])

    def test_03_cannot_select_on_successful_only_cases(self):
        outcomes={k:'PASS' for k in v2.parse_native_cases(JUNIT.encode(),SELECTORS)}
        with self.assertRaises(ValueError):
            v3.source_neutral_residuals(SAMPLE,SELECTORS,outcomes)

    def test_04_source_unsupported_dynamic_case_must_fail_closed(self):
        text=SAMPLE.replace(b'["valid\\\\n", "valid \\\\n"]',
                            b'[make_private_case(), "valid \\\\n"]')
        outcome=v2.parse_native_cases(JUNIT.encode(),SELECTORS)
        with self.assertRaises(ValueError):
            v3.source_neutral_residuals(text,SELECTORS,outcome)

    def test_05_only_source_match_guard_that_separates_witness_survives(self):
        sources={
          'backend/pkg/a/guard.py':RELEVANT,
          'backend/pkg/b/guard.py':RELEVANT,
          'backend/pkg/c/guard.py':FULLMATCH,
          'backend/pkg/d/guard.py':DISJOINT}
        old=v2.source_catalog(sources,list(sources))
        self.assertEqual(len(old),4)
        accepted,analysis=v3.filter_by_native_original_witnesses(sources,old,['valid\n'])
        self.assertEqual([x['path'] for x in accepted],
                         ['backend/pkg/a/guard.py','backend/pkg/b/guard.py'])
        self.assertEqual(len(analysis),4)
        self.assertTrue(all(x in old for x in accepted))

    def test_06_no_winner_specific_attribute_or_test_identity(self):
        import inspect
        s=inspect.getsource(v3)
        self.assertNotIn("AGENT_NAME_PATTERN",s)
        self.assertNotIn("reviewer",s)
        self.assertNotIn("test_custom_agent",s)

    def test_07_avoid_posthoc_syntax_widening_or_source_mutation(self):
        sources={'backend/pkg/a/guard.py':RELEVANT,
                 'backend/pkg/c/guard.py':FULLMATCH}
        immutable={k:bytes(v) for k,v in sources.items()}
        catalog=v2.source_catalog(sources,list(sources))
        v3.filter_by_native_original_witnesses(sources,catalog,['valid\n'])
        self.assertEqual(sources,immutable)
        self.assertEqual(v2.source_catalog(sources,list(sources)),catalog)

    def test_08_wrong_source_or_missing_observed_pattern_unknown(self):
        sources={'backend/pkg/a/guard.py':RELEVANT}
        original=v2.source_catalog(sources,list(sources))
        for bad in ([],['123\n']):
            with self.subTest(bad=bad):
                result,_=v3.filter_by_native_original_witnesses(sources,original,bad)
                self.assertEqual(result,[])

if __name__=="__main__":
    unittest.main()
