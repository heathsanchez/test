"""CI behavioral contract: exact typed failure evidence must exist on a real residual."""
import json,os,pathlib,subprocess,unittest
class Capture(unittest.TestCase):
    def test_real_bool_matcher_has_typed_comparison(self):
        binary=os.environ.get('NUCLEUS_DIAGNOSTIC_BINARY')
        if not binary: self.skipTest('CI supplies pinned binary and corpus')
        p=pathlib.Path('/tmp/current/good/perf/magma-list-pair-n7.ndjson')
        with p.open('rb') as f:
            r=subprocess.run([binary],stdin=f,capture_output=True,timeout=240,env=os.environ|{'NUCLEUS_TRACE_CAUSAL':'1'})
        self.assertEqual(r.returncode,2)
        events=[json.loads(x.split(':',1)[1]) for x in r.stderr.decode().splitlines() if x.startswith('NUCLEUS_CAUSAL:')]
        failures=[e for e in events if e['kind']=='typed-comparison']
        self.assertTrue(failures,'missing failed typed comparison')
        for e in failures:
            for field in ['expression','inferred','expected','context','frame','policy','budget','result']:
                self.assertIn(field,e['detail'])
