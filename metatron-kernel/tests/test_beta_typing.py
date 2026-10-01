import json,os,pathlib,subprocess,unittest
from slice_no_confusion import slice_prefix
OBLIGATIONS=['perf/magma-list-pair-n7','perf/magma-list-pair-n21','perf/magma-list-deep-n21','perf/magma-list-deep-n36','perf/fueled-chain']
class BetaTyping(unittest.TestCase):
    def run_data(self,data):
        q=subprocess.run([os.environ['NUCLEUS_SUM_BINARY']],input=data,text=True,capture_output=True,timeout=60)
        self.assertIn(q.returncode,(0,1,2),q.stderr)
        return q.returncode
    def test_dependent_identity_application(self):
        p=pathlib.Path(__file__).parent/'fixtures/dependent-application.ndjson'
        self.assertEqual(self.run_data(p.read_text()),0)
    def test_shared_matcher_prefix(self):
        for name in OBLIGATIONS:
            with self.subTest(name=name):
                p=pathlib.Path(os.environ.get('NUCLEUS_CORPUS','/tmp/current'))/'good'/(name+'.ndjson')
                self.assertEqual(self.run_data(slice_prefix(p,'Nat.decEq.match_1')),0)
if __name__=='__main__':unittest.main()
