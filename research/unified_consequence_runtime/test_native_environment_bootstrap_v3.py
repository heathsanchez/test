"""Artifact-only bootstrap contracts; no runtime install or target access."""
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import sys
import subprocess
import tempfile
import unittest
from unittest.mock import patch
import warnings
import zipfile


HERE = Path(__file__).resolve().parent / 'archaeology/native-environment-v3/bootstrap'


def load_bootstrap():
    def load(name, path):
        spec = importlib.util.spec_from_file_location(name, path)
        module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
        return module
    metadata = load('bootstrap_metadata_receipt_v3', HERE / 'metadata_receipt.py')
    cache = load('bootstrap_stdlib_cache_v3', HERE / 'stdlib_cache.py')
    with patch.dict(sys.modules, {'metadata_receipt': metadata, 'stdlib_cache': cache}):
        return load('bootstrap_prepare_runtimes_v3', HERE / 'prepare_runtimes.py')


class BootstrapWheelMetadataV3(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bootstrap = load_bootstrap()

    @staticmethod
    def wheel(entries, expected_metadata):
        stream = io.BytesIO()
        with warnings.catch_warnings():
            warnings.simplefilter('ignore', UserWarning)
            with zipfile.ZipFile(stream, 'w') as wheel:
                for name, raw in entries:
                    wheel.writestr(name, raw)
        raw = stream.getvalue()
        return raw, {'filename': 'fixture-1.0-py3-none-any.whl', 'url': 'https://fixture.invalid/wheel',
                     'sha256': hashlib.sha256(raw).hexdigest(), 'size': len(raw),
                     'metadata_sha256': hashlib.sha256(expected_metadata).hexdigest()}

    def download(self, entries, expected_metadata):
        raw, record = self.wheel(entries, expected_metadata)
        class Response(io.BytesIO):
            status = 200
            def geturl(self): return record['url']
        with tempfile.TemporaryDirectory() as folder, \
                patch.object(self.bootstrap.urllib.request, 'urlopen', return_value=Response(raw)):
            receipt = self.bootstrap.download(record, Path(folder))
            self.assertEqual(receipt['sha256'], record['sha256'])
            self.assertEqual(receipt['bytes'], record['size'])
            self.assertTrue(receipt['tls_verification'])
            return receipt

    def test_one_top_level_metadata_with_multiple_vendored_metadata_is_accepted(self):
        raw = b'Metadata-Version: 2.1\nName: fixture\nVersion: 1.0\n'
        self.download([('fixture-1.0.dist-info/METADATA', raw),
                       ('fixture/_vendor/one-2.dist-info/METADATA', b'vendored one'),
                       ('fixture/_vendor/two-3.dist-info/METADATA', b'vendored two')], raw)

    def test_one_top_level_metadata_without_vendors_is_accepted(self):
        raw = b'Name: fixture\nVersion: 1.0\n'
        self.download([('fixture-1.0.dist-info/METADATA', raw)], raw)

    def test_vendored_metadata_cannot_replace_missing_top_level_metadata(self):
        raw = b'Name: fixture\nVersion: 1.0\n'
        with self.assertRaisesRegex(ValueError, 'one.*METADATA'):
            self.download([('fixture/_vendor/fixture-1.0.dist-info/METADATA', raw)], raw)

    def test_wrong_top_level_digest_cannot_use_matching_vendored_digest(self):
        raw = b'Name: fixture\nVersion: 1.0\n'
        with self.assertRaisesRegex(ValueError, 'metadata digest differs'):
            self.download([('fixture-1.0.dist-info/METADATA', b'Name: changed\n'),
                           ('fixture/_vendor/fixture-1.0.dist-info/METADATA', raw)], raw)

    def test_multiple_top_level_distribution_metadata_records_are_refused(self):
        raw = b'Name: fixture\nVersion: 1.0\n'
        with self.assertRaisesRegex(ValueError, 'one.*METADATA'):
            self.download([('fixture-1.0.dist-info/METADATA', raw),
                           ('other-2.0.dist-info/METADATA', b'Name: other\n')], raw)

    def test_duplicate_top_level_archive_record_is_refused(self):
        raw = b'Name: fixture\nVersion: 1.0\n'
        with self.assertRaisesRegex(ValueError, 'one.*METADATA'):
            self.download([('fixture-1.0.dist-info/METADATA', raw),
                           ('fixture-1.0.dist-info/METADATA', raw)], raw)


class BootstrapStdlibPreparationV3(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bootstrap = load_bootstrap()

    def test_original_compiler_warms_all_modes_and_retains_syntax_failures(self):
        self.assertTrue(callable(getattr(self.bootstrap, 'warm_runtime', None)),
                        'source-preserving runtime preparation is required')
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder); stdlib = root/'stdlib'; stdlib.mkdir()
            source = stdlib/'original_probe.py'; source.write_bytes(Path(__import__('keyword').__file__).read_bytes())
            original = source.read_bytes(); (stdlib/'invalid_syntax.py').write_text('def invalid(:\n')
            for excluded in ('site-packages', 'dist-packages'):
                (stdlib/excluded).mkdir(); (stdlib/excluded/'excluded.py').write_text('VALUE = 1\n')
            outside = root/'outside'; outside.mkdir(); (outside/'excluded.py').write_text('VALUE = 1\n')
            (stdlib/'linked-directory').symlink_to(outside, target_is_directory=True)
            with patch.object(self.bootstrap, 'runtime_import_roots', return_value=[str(stdlib)]):
                receipt = self.bootstrap.warm_runtime(sys.executable, root/'receipt.json')
            self.assertEqual(receipt['status'], 'PREPARED_STDLIB_BYTECODE')
            self.assertEqual(source.read_bytes(), original)
            self.assertEqual(receipt['source_manifest_before'], receipt['source_manifest_after'])
            self.assertEqual(receipt['compilation']['compiled'], 3)
            self.assertEqual(len(receipt['compilation']['failures']), 3)
            self.assertTrue(all(row['exception'] == 'SyntaxError' for row in receipt['compilation']['failures']))
            self.assertEqual(len(list((stdlib/'__pycache__').glob('original_probe*.pyc'))), 3)
            self.assertFalse(list(outside.rglob('*.pyc')))
            self.assertFalse(list((stdlib/'site-packages').rglob('*.pyc')))
            self.assertFalse(list((stdlib/'dist-packages').rglob('*.pyc')))

    def test_host_rejects_nonbytecode_source_change_from_compiler_process(self):
        self.assertTrue(callable(getattr(self.bootstrap, 'warm_runtime', None)))
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder); stdlib = root/'stdlib'; stdlib.mkdir(); source = stdlib/'probe.py'
            source.write_text('VALUE = 1\n')
            def changed(*_, **__):
                source.write_text('VALUE = 2\n')
                return subprocess.CompletedProcess([], 0, json.dumps({'compiled': 0, 'failures': []}), '')
            with patch.object(self.bootstrap, 'runtime_import_roots', return_value=[str(stdlib)]), \
                    patch.object(self.bootstrap.subprocess, 'run', side_effect=changed):
                with self.assertRaisesRegex(ValueError, 'source.*changed|nonbytecode'):
                    self.bootstrap.warm_runtime(sys.executable, root/'receipt.json')
            receipt = json.loads((root/'receipt.json').read_text())
            self.assertEqual(receipt['status'], 'UNKNOWN_STDLIB_SOURCE_CHANGED')

    def test_post_fixture_audit_names_added_cache_bytes(self):
        self.assertTrue(callable(getattr(self.bootstrap, 'audit_runtime_freeze', None)),
                        'post-fixture host byte differences must be retained')
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder); source = root/'probe.py'; source.write_text('VALUE = 1\n')
            record = {'interpreter': sys.executable, 'import_roots': [str(root)],
                      'identity': {'executable_sha256': hashlib.sha256(Path(sys.executable).read_bytes()).hexdigest()},
                      'stdlib_files': [[str(source), hashlib.sha256(source.read_bytes()).hexdigest()]]}
            cache = root/'probe.pyc'; cache.write_bytes(b'new executable cache')
            result = self.bootstrap.audit_runtime_freeze({'runtimes': {'fixture': record}})
            self.assertEqual(result['status'], 'UNKNOWN_RUNTIME_BYTES_CHANGED')
            self.assertEqual(result['runtimes']['fixture']['added'], [str(cache)])
            self.assertEqual(result['runtimes']['fixture']['changed'], [])

    def test_optional_absent_build_time_destshared_root_does_not_hide_stdlib(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder); stdlib = root/'stdlib'; stdlib.mkdir()
            (stdlib/'probe.py').write_text('VALUE = 1\n')
            missing = root/'absent-build-prefix/lib-dynload'
            with patch.object(self.bootstrap, 'runtime_import_roots', return_value=[str(stdlib), str(missing)]):
                receipt = self.bootstrap.warm_runtime(sys.executable, root/'receipt.json')
            self.assertEqual(receipt['compilation']['compiled'], 3)
            self.assertFalse(missing.exists())


if __name__ == '__main__':
    unittest.main()
