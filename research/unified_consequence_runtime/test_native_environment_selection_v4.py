"""V4 source-role deferral and source-bound independently executing controls."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from . import native_environment_selection_v3 as old
from . import native_environment_selection_v4 as new
from . import native_environment_v4 as admission

PYPROJECT = b'''[project]
name = "fixture-only"
requires-python = ">=3.11"
'''
BROKEN_DATA = b"if True:\n\tvalue = 1\n    value = 2\n"


def catalog(*profiles):
    return {"schema": new.CATALOG_SCHEMA, "profiles": list(profiles)}


def profile(name="modern", python="3.12.14", pytest="8.4.1"):
    return {"id": name, "python_version": python, "python_implementation": "CPython",
            "pytest_version": pytest, "packages": ["pytest==" + pytest], "plugins": []}


class StaticSourceRoleContracts(unittest.TestCase):
    def setUp(self):
        self.files = {"pyproject.toml": PYPROJECT,
                      "tests/data/broken_fixture.py": BROKEN_DATA,
                      "src/fixture_only/__init__.py": b"VERSION = 1\n"}
        self.catalog = catalog(profile())

    def test_malformed_python_as_data_does_not_prevent_candidate_environment(self):
        old_result = old.select_profile(self.files,
                                        {"schema": old.CATALOG_SCHEMA, "profiles": [profile()]})
        self.assertEqual(old_result["reason"], "UNKNOWN_SOURCE_PARSER")
        result = new.select_profile(self.files, self.catalog)
        self.assertEqual(result["status"], "CANDIDATE_SOURCE_ENVIRONMENT")
        self.assertEqual(result["schema"], new.SELECTION_SCHEMA)
        self.assertEqual(result["constraints"]["schema"], new.CONSTRAINT_SCHEMA)
        self.assertEqual(result["constraints"]["deferred_python_sources"], [{
            "path": "tests/data/broken_fixture.py",
            "sha256": hashlib.sha256(BROKEN_DATA).hexdigest(),
            "status": "UNKNOWN_STATIC_ROLE_NATIVE_COLLECTION_REQUIRED"}])
        self.assertEqual(new.validate_selection(self.files, self.catalog, result), result)

    def test_deferred_bytes_are_in_full_source_identity_and_cannot_be_forged(self):
        first = new.select_profile(self.files, self.catalog)
        altered = dict(self.files)
        altered["tests/data/broken_fixture.py"] = BROKEN_DATA + b"# different data\n"
        second = new.select_profile(altered, self.catalog)
        self.assertNotEqual(first["constraints"]["source_sha256"],
                            second["constraints"]["source_sha256"])
        with self.assertRaisesRegex(ValueError, "UNKNOWN_SELECTION_IDENTITY"):
            new.validate_selection(altered, self.catalog, first)
        forged = json.loads(json.dumps(first))
        forged["constraints"]["deferred_python_sources"] = []
        with self.assertRaisesRegex(ValueError, "UNKNOWN_SELECTION_IDENTITY"):
            new.validate_selection(self.files, self.catalog, forged)

    def test_setup_py_syntax_failure_still_refuses_metadata_authority(self):
        files = dict(self.files)
        files["setup.py"] = BROKEN_DATA
        result = new.select_profile(files, self.catalog)
        self.assertEqual(result["status"], "UNKNOWN")
        self.assertEqual(result["reason"], "UNKNOWN_SOURCE_PARSER")

    def test_parseable_legacy_pytest_api_remains_a_constraint(self):
        from .test_native_environment_selection_v3 import LEGACY
        files = {"setup.py": LEGACY,
                 "tox.ini": b"[tox]\nenvlist = py{35,36}-{without,with}-extensions\n[testenv]\ndeps = pytest\n",
                 "tests/conftest.py": b"import pytest\nC = pytest.collect.File\n"}
        options = catalog(profile("legacy", "3.6.12", "5.4.3"), profile())
        result = new.select_profile(files, options)
        self.assertEqual(result["status"], "CANDIDATE_SOURCE_ENVIRONMENT")
        self.assertEqual(result["selected_profile"]["id"], "legacy")
        self.assertIn("pytest<6", [r["requirement"] for r in
                                   result["constraints"]["requirements"]])

    def test_dynamic_setup_metadata_is_not_made_trusted_by_deferral(self):
        files = dict(self.files)
        files["setup.py"] = b"setup(python_requires=compute_version())\n"
        result = new.select_profile(files, self.catalog)
        self.assertEqual(result["reason"], "UNKNOWN_DYNAMIC_METADATA")

    def test_versioned_adapter_reuses_original_native_executor(self):
        from . import native_execution_v3
        self.assertIs(admission.execution, native_execution_v3)
        self.assertIs(admission.selection, new)
        self.assertEqual(admission._guard(), None)


class IndependentlyExecutedPytestContracts(unittest.TestCase):
    """Selection is not execution authority: pytest observes imports and failures."""

    def run_suite(self, *, import_bad=False, fail_protected=False):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root/"pytest.ini").write_text("[pytest]\ntestpaths = tests\n")
            (root/"tests/data").mkdir(parents=True)
            (root/"tests/data/broken_fixture.py").write_bytes(BROKEN_DATA)
            (root/"tests/test_protected.py").write_text(
                ("import importlib.util\nfrom pathlib import Path\n"
                 "p=Path(__file__).parent/'data/broken_fixture.py'\n"
                 "s=importlib.util.spec_from_file_location('data',p)\n"
                 "s.loader.exec_module(importlib.util.module_from_spec(s))\n")
                if import_bad else ("def test_protected():\n"
                + ("    assert 1 == 2\n" if fail_protected else "    assert True\n")))
            env = {**os.environ, "PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1",
                   "PYTHONDONTWRITEBYTECODE": "1"}
            process = subprocess.run([sys.executable, "-m", "pytest", "-q", "-p",
                                      "no:cacheprovider", "--tb=short"],
                                     cwd=root, env=env, capture_output=True, text=True,
                                     timeout=35)
            return process.returncode, process.stdout+process.stderr

    def test_native_collection_ignores_uncollected_fixture_data(self):
        code, output = self.run_suite()
        self.assertEqual(code, 0, output)
        self.assertIn("1 passed", output)

    def test_native_import_of_malformed_fixture_fails_closed(self):
        code, output = self.run_suite(import_bad=True)
        self.assertNotEqual(code, 0, output)
        self.assertTrue("TabError" in output or "IndentationError" in output, output)

    def test_protected_assertion_failure_remains_visible(self):
        code, output = self.run_suite(fail_protected=True)
        self.assertEqual(code, 1, output)
        self.assertIn("1 failed", output)


if __name__ == "__main__":
    unittest.main()
