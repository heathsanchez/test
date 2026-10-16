"""Independent V4 obligation: preserve all V3 selectors; defer only undecidable non-setup
syntax, while native execution retains collection, import and assertion authority.
This source is committed before the implementation.
"""
from __future__ import annotations

import copy
import hashlib
import importlib
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from .test_native_environment_selection_v3 import (
    NativeEnvironmentSelectionV3, catalog, profile,
)

MODULE = 'research.unified_consequence_runtime.native_environment_selection_v4'
METADATA = b'[project]\nrequires-python = ">=3.11"\n'
BAD = b'if True:\n\tvalue=1\n        value=2\n'


class AllPriorV3SelectorContracts(NativeEnvironmentSelectionV3):
    """Replay every inherited V3 behavioral and adversarial selector contract."""

    def setUp(self):
        self.selector = importlib.import_module(MODULE)


class V4SourceMeaningSeparation(unittest.TestCase):
    def setUp(self):
        self.selector = importlib.import_module(MODULE)
        self.catalog = catalog(profile())

    def files(self, invalid_path='examples/invalid.py'):
        return {'pyproject.toml': METADATA, invalid_path: BAD}

    def test_data_blob_is_hashed_and_deferred_without_becoming_executable_authority(self):
        files = self.files()
        receipt = self.selector.select_profile(files, self.catalog)
        self.assertEqual(receipt['status'], 'CANDIDATE_SOURCE_ENVIRONMENT', receipt)
        deferred = receipt['constraints']['deferred_source_parse']
        self.assertEqual(deferred, [{
            'path': 'examples/invalid.py',
            'sha256': hashlib.sha256(BAD).hexdigest(),
            'kind': 'UNPARSEABLE_UNTIL_NATIVE_EXECUTION',
        }])
        self.assertEqual(receipt['constraints']['source_sha256'],
                         self.selector._hash(self.selector._canonical({
                             name: hashlib.sha256(raw).hexdigest()
                             for name, raw in sorted(files.items())
                         }).encode()))
        self.assertEqual(self.selector.validate_selection(files, self.catalog, receipt), receipt)
        changed = copy.deepcopy(files)
        changed['examples/invalid.py'] += b'# mutated\n'
        with self.assertRaises(ValueError):
            self.selector.validate_selection(changed, self.catalog, receipt)

    def test_malformed_setup_metadata_remains_unknown(self):
        receipt = self.selector.select_profile(self.files('setup.py'), self.catalog)
        self.assertEqual(receipt['status'], 'UNKNOWN')
        self.assertEqual(receipt['reason'], 'UNKNOWN_SOURCE_PARSER')

    def test_malformed_collected_test_is_not_redefined_as_a_native_pass(self):
        receipt = self.selector.select_profile(self.files('tests/test_broken.py'), self.catalog)
        self.assertEqual(receipt['status'], 'CANDIDATE_SOURCE_ENVIRONMENT')
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / 'tests').mkdir()
            (root / 'tests/test_broken.py').write_bytes(BAD)
            native = self.run_pytest(root)
            self.assertNotEqual(native.returncode, 0)
            self.assertIn('ERROR', native.stdout + native.stderr)

    def test_data_fixture_is_harmless_until_executable_import_is_attempted(self):
        files = self.files('fixtures/bad.py')
        receipt = self.selector.select_profile(files, self.catalog)
        self.assertEqual(receipt['status'], 'CANDIDATE_SOURCE_ENVIRONMENT')
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / 'fixtures').mkdir()
            (root / 'fixtures/__init__.py').write_text('')
            (root / 'fixtures/bad.py').write_bytes(BAD)
            (root / 'tests').mkdir()
            test = root / 'tests/test_fixture.py'
            test.write_text(
                'from pathlib import Path\n'
                'def test_raw_data():\n'
                '    assert b"\\tvalue=1" in Path("fixtures/bad.py").read_bytes()\n'
            )
            harmless = self.run_pytest(root)
            self.assertEqual(harmless.returncode, 0, harmless.stdout + harmless.stderr)
            self.assertIn('1 passed', harmless.stdout)
            test.write_text(
                'import fixtures.bad\n'
                'def test_import():\n'
                '    assert True\n'
            )
            imported = self.run_pytest(root)
            self.assertNotEqual(imported.returncode, 0)
            self.assertIn('TabError', imported.stdout + imported.stderr)

    @staticmethod
    def run_pytest(root):
        env = dict(os.environ, PYTEST_DISABLE_PLUGIN_AUTOLOAD='1',
                   PYTHONDONTWRITEBYTECODE='1', PYTHONPATH=str(root))
        return subprocess.run(
            [sys.executable, '-B', '-m', 'pytest', '-q', '-p', 'no:cacheprovider'],
            cwd=root, env=env, capture_output=True, text=True, timeout=45,
        )


if __name__ == '__main__':
    unittest.main()
