"""Frozen, source-free acceptance contracts for minimum-sufficient authority V4.

Authored before the V4 selector implementation. Selection is NOT native admission.
Previously exposed V3 cases are development diagnostics, not prospective wins.
"""
import hashlib
import importlib
import unittest
from . import native_environment_selection_v3 as v3

v4 = importlib.import_module("research.unified_consequence_runtime.native_environment_selection_v4")

def profile(name="modern", python="3.12.14", pytest="8.4.1", packages=()):
    return {"id":name, "python_version":python, "python_implementation":"CPython",
            "pytest_version":pytest, "packages":["pytest=="+pytest,*packages],"plugins":[]}

def catalog(*profiles):
    return {"schema":"UDM_NATIVE_ENVIRONMENT_CATALOG_V3","profiles":list(profiles)}

META=b'[project]\nrequires-python=">=3.12"\n'
MALFORMED=b"if True:\n\tpass\n    pass\n"

class FrozenV4Contracts(unittest.TestCase):
    def choose(self, files, *profiles):
        return v4.select_profile(files,catalog(*(profiles or (profile(),))))

    def test_A01_unparseable_python_fixture_is_identified_not_executed(self):
        files={"pyproject.toml":META,"tests/data/broken.py":MALFORMED,
               "src/app.py":b"VALUE = 42\n"}
        result=self.choose(files)
        self.assertEqual(result["status"],"CANDIDATE_SOURCE_ENVIRONMENT")
        self.assertEqual(result["selected_profile"]["id"],"modern")
        self.assertEqual(result["constraints"]["deferred_python_sources"],
                         {"tests/data/broken.py":hashlib.sha256(MALFORMED).hexdigest()})
        self.assertEqual(result["constraints"]["source_sha256"],
                         v3.derive_constraints(files)["source_sha256"])
        self.assertNotIn("PASS_NATIVE",str(result))

    def test_A02_old_selector_remains_original_negative(self):
        files={"pyproject.toml":META,"tests/fixtures/invalid.py":MALFORMED}
        self.assertEqual(v3.select_profile(files,catalog(profile()))["reason"],
                         "UNKNOWN_SOURCE_PARSER")
        self.assertEqual(self.choose(files)["status"],"CANDIDATE_SOURCE_ENVIRONMENT")

    def test_A03_malformed_protected_test_still_refused(self):
        files={"pyproject.toml":META,"tests/test_bad.py":MALFORMED}
        self.assertEqual(self.choose(files)["reason"],"UNKNOWN_SOURCE_PARSER")

    def test_A04_malformed_conftest_still_refused(self):
        files={"pyproject.toml":META,"tests/conftest.py":MALFORMED}
        self.assertEqual(self.choose(files)["reason"],"UNKNOWN_SOURCE_PARSER")

    def test_A05_malformed_setup_metadata_still_refused(self):
        files={"setup.py":MALFORMED,"pyproject.toml":META}
        self.assertEqual(self.choose(files)["reason"],"UNKNOWN_SOURCE_PARSER")

    def test_A06_malformed_source_module_still_refused(self):
        files={"pyproject.toml":META,"src/critical.py":MALFORMED,
               "tests/test_it.py":b"from critical import value\n"}
        self.assertEqual(self.choose(files)["reason"],"UNKNOWN_SOURCE_PARSER")

    def test_A07_fixture_api_reference_does_not_force_legacy_runtime(self):
        files={"pyproject.toml":META,
               "tests/data/unsupported_api.py":b"import pytest\nx=pytest.collect.File\n"}
        result=self.choose(files)
        self.assertEqual(result["status"],"CANDIDATE_SOURCE_ENVIRONMENT")
        self.assertEqual(result["selected_profile"]["id"],"modern")

    def test_A08_executable_api_reference_still_constrains_runtime(self):
        files={"setup.py":b'from setuptools import setup\nsetup(python_requires=">=3.6")\n',
               "tests/conftest.py":b"import pytest\nclass Dummy(pytest.collect.File): pass\n"}
        result=self.choose(files,profile("old","3.6.12","5.4.3"),profile())
        self.assertEqual(result["status"],"CANDIDATE_SOURCE_ENVIRONMENT")
        self.assertEqual(result["selected_profile"]["id"],"old")

    def test_A09_dynamic_metadata_is_not_silently_accepted(self):
        files={"setup.py":b"from setuptools import setup\nsetup(python_requires=get_version())\n"}
        self.assertEqual(self.choose(files)["reason"],"UNKNOWN_DYNAMIC_METADATA")

    def test_A10_unsupported_metadata_grammar_remains_unknown(self):
        files={"pyproject.toml":b'[project]\nrequires-python=">=3.12"\n'
               b'[dependency-groups]\ntests=[{ mystery = "test" }]\n'}
        self.assertEqual(self.choose(files)["reason"],"UNKNOWN_DEPENDENCY_GROUP")

    def test_A11_incompatible_catalog_does_not_magically_gain_profile(self):
        self.assertEqual(self.choose({"pyproject.toml":META},
                         profile("legacy","3.6.12","5.4.3"))["status"],"UNKNOWN")

    def test_A12_invalid_catalog_does_not_gain_authority(self):
        result=self.choose({"pyproject.toml":META},
                           profile(packages=["attrs>=20"]))
        self.assertEqual(result["reason"],"UNKNOWN_CATALOG_AUTHORITY")

    def test_A13_forged_file_identity_is_not_conflated_with_role(self):
        files={"pyproject.toml":META,"tests/data/case.py":MALFORMED}
        changed={**files,"tests/data/case.py":MALFORMED+b"# altered\n"}
        self.assertNotEqual(self.choose(files)["constraints"]["source_sha256"],
                            self.choose(changed)["constraints"]["source_sha256"])

    def test_A14_unrecognized_fixture_location_is_not_bypassed(self):
        files={"pyproject.toml":META,"unknown_folder/possibly_executed.py":MALFORMED}
        self.assertEqual(self.choose(files)["reason"],"UNKNOWN_SOURCE_PARSER")

    def test_A15_fixture_role_never_overrides_original_unparseable_test(self):
        files={"pyproject.toml":META,"tests/fixtures/test_malicious.py":MALFORMED}
        self.assertEqual(self.choose(files)["reason"],"UNKNOWN_SOURCE_PARSER")

    def test_A16_unrecognized_pytest_conftest_placement_is_not_bypassed(self):
        files={"pyproject.toml":META,"tests/data/conftest.py":MALFORMED}
        self.assertEqual(self.choose(files)["reason"],"UNKNOWN_SOURCE_PARSER")

    def test_A17_source_data_preserves_invalid_bytes_and_explicit_scope(self):
        files={"pyproject.toml":META,"testdata/input_case.py":b"\xff\x00"}
        result=self.choose(files)
        self.assertEqual(result["status"],"CANDIDATE_SOURCE_ENVIRONMENT")
        self.assertEqual(result["constraints"]["deferred_python_sources"]["testdata/input_case.py"],
                         hashlib.sha256(b"\xff\x00").hexdigest())

if __name__ == "__main__":
    unittest.main()
