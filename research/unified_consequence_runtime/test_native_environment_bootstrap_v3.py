"""Artifact-only bootstrap contracts; no runtime install or target access."""
import hashlib
import importlib.util
import io
from pathlib import Path
import sys
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
    with patch.dict(sys.modules, {'metadata_receipt': metadata}):
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


if __name__ == '__main__':
    unittest.main()
