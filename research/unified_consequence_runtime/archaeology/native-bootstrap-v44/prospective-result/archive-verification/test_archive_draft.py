"""Data-only draft checks. These tests never invoke a source-native task."""
import importlib.util
from pathlib import Path
import tempfile
import unittest

DRAFT=Path(__file__).with_name('archive_evidence_v44.py')
REPO=Path('/workspace/udm-v54')


def load():
    assert DRAFT.is_file(), 'V44 final archive draft is absent'
    spec=importlib.util.spec_from_file_location('_v44_archive_draft',DRAFT)
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class DataArchiveChecks(unittest.TestCase):
    def test_data_bytes_and_link_metadata_are_retained_without_execution(self):
        m=load()
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary)
            source=root/'source';source.mkdir()
            (source/'never_execute.py').write_text("raise RuntimeError('ARCHIVED DATA WAS EXECUTED')\n")
            (source/'data').write_bytes(b'opaque-data\x00\xff')
            (source/'link').symlink_to('data')
            archive=root/'raw.tar.gz';manifest=root/'raw.manifest.json';readback=root/'raw.readback.json'
            result=m.pack(REPO,source,archive,manifest,readback,root/'summary.json')
            self.assertEqual(result['original_verdict']['status'],'PASS')
            self.assertTrue(result['original_verdict']['source_lstat_and_bytes_verified'])
            self.assertEqual(result['original_verdict']['source_counts'],{'file':2,'directory':0,'symlink':1})
            self.assertEqual(result['verdicts'],{f'G{i}':'UNKNOWN' for i in range(2,7)})
            self.assertEqual((source/'never_execute.py').read_text(),"raise RuntimeError('ARCHIVED DATA WAS EXECUTED')\n")
    def test_bad_archive_bytes_fail_without_source_execution(self):
        m=load()
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);source=root/'source';source.mkdir()
            (source/'data').write_bytes(b'opaque')
            archive=root/'raw.tar.gz';manifest=root/'raw.manifest.json'
            m.pack(REPO,source,archive,manifest,root/'readback.json',root/'summary.json')
            archive.write_bytes(archive.read_bytes()+b'forged-trailing-data')
            with self.assertRaises((ValueError,AssertionError)):
                m.cas_verifier(REPO).verify(archive,manifest,None)
    def test_forged_expectation_is_refused_before_source_audit(self):
        m=load()
        with tempfile.TemporaryDirectory() as temporary:
            path=Path(temporary)/'expected.json';path.write_text('{}')
            with self.assertRaises(ValueError):
                m.check(REPO,path,'0'*64,'0'*40,Path(temporary)/'output',None)


if __name__=='__main__':unittest.main()
