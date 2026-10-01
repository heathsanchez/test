import json,os,pathlib,subprocess,unittest
from slice_no_confusion import slice_prefix
import test_record_telescopes as records
class ProofRecords(unittest.TestCase):
    def test_nezero_prefixes(self):
        c=records.RecordTelescopes()
        for name in ['perf/magma-list-pair-n7','perf/magma-list-pair-n21']:
            with self.subTest(name=name):self.assertEqual(c.run_rows(c.rows(name,'NeZero')),0)
    def test_singleton_proof_record_execution(self):
        c=records.RecordTelescopes()
        for proj in [None,0]:
            with self.subTest(projection=proj):self.assertEqual(c.run_rows(c.witness_rows('perf/magma-list-pair-n7','NeZero',proj)),0)
if __name__=='__main__':unittest.main()
