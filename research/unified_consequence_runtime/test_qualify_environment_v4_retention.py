"""Pre-fix test: default collection evidence stays in the qualification packet."""
from pathlib import Path
import tempfile
import unittest
from . import qualify_environment_selection_v4 as q


class DefaultEvidenceRetentionV4(unittest.TestCase):
    def test_persistent_default_directory_is_retained_and_temp_setting_restored(self):
        self.assertTrue(hasattr(q,'retained_temporary_outputs'),'versioned evidence-retention context required')
        with tempfile.TemporaryDirectory() as folder:
            previous=tempfile.tempdir
            target=Path(folder)/'default-evidence'
            with q.retained_temporary_outputs(target):
                raw=Path(tempfile.mkdtemp(prefix='udm-v2-independent-'))/'recollection'
                raw.mkdir();(raw/'checked-report.json').write_bytes(b'{"native_calls":0,"collection_calls":1}\n')
            self.assertEqual(tempfile.tempdir,previous)
            self.assertTrue(raw.is_relative_to(target))
            self.assertTrue((raw/'checked-report.json').is_file())

    def test_original_setting_is_restored_on_failed_control(self):
        self.assertTrue(hasattr(q,'retained_temporary_outputs'),'versioned evidence-retention context required')
        with tempfile.TemporaryDirectory() as folder:
            previous=tempfile.tempdir
            with self.assertRaisesRegex(RuntimeError,'failed control'):
                with q.retained_temporary_outputs(Path(folder)/'default-evidence'):
                    raise RuntimeError('failed control')
        self.assertEqual(tempfile.tempdir,previous)


if __name__=='__main__':unittest.main()
