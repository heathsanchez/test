import os,pathlib,subprocess,unittest
from slice_no_confusion import slice_prefix
class BetaSpine(unittest.TestCase):
    def test_except_monad_prefix(self):
        root=pathlib.Path(os.environ.get('NUCLEUS_CORPUS','/tmp/current'))
        data=slice_prefix(root/'good/perf/fueled-chain.ndjson','Except.instMonad')
        q=subprocess.run([os.environ['NUCLEUS_SUM_BINARY']],input=data,text=True,capture_output=True,timeout=60)
        self.assertEqual(q.returncode,0,q.stderr)
if __name__=='__main__':unittest.main()
