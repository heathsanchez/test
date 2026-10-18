"""Frozen no-network contracts: source-neutral per-case identity and finite import composition.

The original Deer-flow production/test and original Mistral method are NOT
modified here. This is an exposed-source retrospective experiment only.
"""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock
from . import g2_deer_import_composition_v2 as target

CASES="""<?xml version="1.0"?>
<testsuites><testsuite name="pytest" tests="4">
 <testcase classname="tests.test_contract.TestAPI" name="test_api[bad]"><failure message="bad"/></testcase>
 <testcase classname="tests.test_contract.TestAPI" name="test_api[good]"/>
 <testcase classname="tests.test_contract" name="test_validator[bad]"><failure message="bad"/></testcase>
 <testcase classname="tests.test_contract" name="test_validator[good]"/>
</testsuite></testsuites>"""
NODES=["backend/tests/test_contract.py::TestAPI::test_api",
       "backend/tests/test_contract.py::test_validator"]
SRC1=b'import re\nRULE = re.compile(r"^[a-z]+$")\ndef validate(x): return RULE.match(x)\n'
SRC2=b'import re\nRULE = re.compile(r"^[A-Z]+$")\ndef validate(x): return RULE.match(x)\n'
SRC3=b'def unused(x):return False\n'
FILES={
 "backend/app/gateway/routers/agents.py":SRC1,
 "backend/packages/harness/deerflow/agents/memory/backends/deermem/deermem/core/paths.py":SRC2,
 "backend/packages/harness/deerflow/config/agents_config.py":SRC3,
}
TEST=b"""from app.gateway.routers.agents import RULE
from deerflow.agents.memory.backends.deermem.deermem.core.paths import validate
from deerflow.config.agents_config import AgentConfig
def test_validator(): assert True
class TestAPI:
    def test_api(self): assert True
"""


class V2ImportCompositionFrozen(unittest.TestCase):
    def parse(self,xml=CASES,selectors=NODES):
        return target.parse_native_cases(xml.encode(),selectors)

    def test_01_four_parameter_cases_keep_identity(self):
        v=self.parse()
        self.assertEqual(len(v),4)
        self.assertEqual(list(v.values()).count("FAIL"),2)
        self.assertEqual(list(v.values()).count("PASS"),2)
        self.assertEqual(len(set(v)),4)

    def test_02_duplicate_junit_case_rejected(self):
        self.assertRaises(ValueError,self.parse,CASES.replace(
            '<testcase classname="tests.test_contract.TestAPI" name="test_api[good]"/>',
            '<testcase classname="tests.test_contract.TestAPI" name="test_api[bad]"/>'))

    def test_03_unexpected_case_and_missing_selected_function_rejected(self):
        changed=CASES.replace('test_validator[bad]','test_other[bad]')
        self.assertRaises(ValueError,self.parse,changed)
        self.assertRaises(ValueError,self.parse,CASES,NODES[:1])

    def test_04_skips_errors_xfail_and_no_junit_refused(self):
        for token in ('<skipped/>','<error/>','<skipped type="pytest.xfail"/>'):
            changed=CASES.replace('name="test_api[good]"/>',
                                  'name="test_api[good]">'+token+'</testcase>')
            with self.subTest(token=token),self.assertRaises(ValueError):
                self.parse(changed)
        with self.assertRaises(ValueError):
            self.parse('<testsuite/>')

    def test_05_junit_permutations_are_behaviorally_equivalent(self):
        x=self.parse()
        swap=CASES.replace('name="test_api[bad]"','name="test_api[TMP]"'
                    ).replace('name="test_api[good]"','name="test_api[bad]"'
                    ).replace('name="test_api[TMP]"','name="test_api[good]"')
        self.assertNotEqual(x,self.parse(swap))

    def test_06_import_to_tracked_source_no_repo_hardcode(self):
        paths=target.imported_source_module_files(TEST,list(FILES),
              "backend/app/gateway/routers/agents.py",30)
        self.assertEqual(set(paths),set(FILES))
        self.assertEqual(len(paths),3)

    def test_07_forbid_ambiguous_source_module_mapping(self):
        other="sandbox/app/gateway/routers/agents.py"
        with self.assertRaises(ValueError):
            target.imported_source_module_files(TEST,[*FILES,other],
                "backend/app/gateway/routers/agents.py",30)

    def test_08_original_production_must_be_source_observed(self):
        with self.assertRaises(ValueError):
            target.imported_source_module_files(TEST,list(FILES),
                "backend/src/not_imported.py",30)

    def test_09_malformed_input_module_or_path_refused(self):
        for item in ("../src/app/gateway/routers/agents.py",
                     "backend/../app/gateway/routers/agents.py",
                     "backend/app//gateway/routers/agents.py",
                     "backend/app/gateway/routers/agents.py\\x00"):
            with self.subTest(item=item),self.assertRaises(ValueError):
                target.imported_source_module_files(TEST,[*FILES,item],
                    "backend/app/gateway/routers/agents.py",30)

    def test_10_unchanged_regex_generator_edits_only_pinned_original_source(self):
        candidates=target.source_catalog(FILES,list(FILES))
        self.assertEqual(len(candidates),2)
        self.assertEqual({c["path"] for c in candidates},set(FILES)-{
            "backend/packages/harness/deerflow/config/agents_config.py"})
        mask=target.render_mask(FILES,candidates,3)
        self.assertEqual(set(mask),set(FILES))
        self.assertNotEqual(mask[candidates[0]["path"]],FILES[candidates[0]["path"]])
        self.assertNotEqual(mask[candidates[1]["path"]],FILES[candidates[1]["path"]])
        self.assertEqual(mask["backend/packages/harness/deerflow/config/agents_config.py"],SRC3)
        self.assertIn(b"\\\\Z",repr(mask).encode())

    def test_11_mask_bounds_and_original_identity(self):
        catalog=target.source_catalog(FILES,list(FILES))
        self.assertEqual(target.render_mask(FILES,catalog,0),FILES)
        for mask in (-1,4,5,True):
            with self.subTest(mask=mask),self.assertRaises(ValueError):
                target.render_mask(FILES,catalog,mask)

    def test_12_complete_table_monotone_minimal_and_ledger_tie(self):
        old=self.parse()
        keys=list(old)
        broken=[k for k,v in old.items() if v=="FAIL"]
        self.assertEqual(len(broken),2)
        table={0:old,
               1:{**old,broken[0]:"PASS"},
               2:{**old,broken[1]:"PASS"},
               3:{k:"PASS" for k in keys}}
        result=target.evaluate_lattice(table,2)
        self.assertEqual(result["status"],"WARRANTED_FINITE_TABLE_SOURCE_NEUTRAL")
        self.assertEqual(result["selected_mask"],3)
        self.assertEqual(result["fully_informed_ledger"],"TIE_EQUAL_INFORMATION")

    def test_13_no_automatic_promotion_from_intermediate_green(self):
        old=self.parse()
        broken=[k for k,v in old.items() if v=="FAIL"]
        table={0:old,1:{**old,broken[0]:"PASS"},
               2:{**old,broken[0]:"PASS"},3:{**old,broken[0]:"PASS"}}
        result=target.evaluate_lattice(table,2)
        self.assertEqual(result["status"],"REJECTED_NO_COMPLETE_FINITE_REPAIR")
        self.assertIsNone(result["selected_mask"])

    def test_14_nonmonotone_full_table_cannot_be_warranted(self):
        old=self.parse();fail=[k for k,v in old.items() if v=="FAIL"]
        baseline_good=[k for k,v in old.items() if v=="PASS"][0]
        table={0:old,1:{**old,fail[0]:"PASS"},
               2:{**old,baseline_good:"FAIL",fail[1]:"PASS"},
               3:{k:"PASS" for k in old}}
        self.assertEqual(target.evaluate_lattice(table,2)["status"],
                         "UNKNOWN_NONMONOTONE_FINITE_CONSEQUENCES")

    def test_15_missing_or_extra_mask_and_case_refused(self):
        old=self.parse()
        for table in ({0:old},{0:old,1:old,2:old,3:{**old,"extra":"PASS"}}):
            with self.subTest(table=table),self.assertRaises(ValueError):
                target.evaluate_lattice(table,2)

    def test_17_unqualified_standard_library_imports_cannot_bind_random_repo_suffix(self):
        # 'types' is imported from the stdlib, NOT backend/vendor/a/types.py.
        # A one-component import has no uniquely source-certified package scope.
        paths=[*FILES,"backend/vendor/a/types.py","backend/vendor/b/types.py"]
        source=b"from types import SimpleNamespace\n"+TEST
        observed=target.imported_source_module_files(source,paths,
                      "backend/app/gateway/routers/agents.py",30)
        self.assertEqual(set(observed),set(FILES))
        self.assertFalse(any(p.endswith("/types.py") for p in observed))

    def test_18_only_source_grammar_eligible_files_count_toward_six_file_cap(self):
        # Original tests can import many nonmutatable helpers. Limit observed
        # source files by the actually admitted unchanged primitive grammar.
        extra={f"backend/vendor/helper_{i}.py": b"def helper(): return None\n"
               for i in range(8)}
        universe={**FILES,**extra}
        catalog=target.source_catalog(universe,list(universe))
        self.assertEqual(len(universe),11)
        self.assertEqual(len({c["path"] for c in catalog}),2)
        self.assertLessEqual(len({c["path"] for c in catalog}),6)

    def test_16_original_contract_and_method_identity_unchanged(self):
        proto=target.frozen()
        self.assertEqual(proto["schema"],"G2_DEERFLOW_EXPOSED_IMPORT_COMPOSITION_V2_PRETEST")
        self.assertEqual(proto["verdict"]["G2"],"UNKNOWN")
        self.assertEqual(proto["method"]["grammar"].split(";")[0],
                         "strict_terminal_anchor ONLY")


if __name__=="__main__":
    unittest.main()
