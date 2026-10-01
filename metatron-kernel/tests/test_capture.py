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
        boundaries=[e for e in events if e['kind']=='boundary']
        self.assertTrue(boundaries,'missing failed typed comparison: terminal boundary absent')
        scope=boundaries[-1]['scope']
        failures=[e for e in events if e['kind']=='typed-comparison' and e['scope']==scope]
        self.assertTrue(failures,'missing failed typed comparison')
        for e in failures:
            for field in ['expression','inferred','expected','context','frame','policy','budget','result']:
                self.assertIn(field,e['detail'])

    def test_three_sum_families_reuse_existing_recursor_check(self):
        binary=os.environ.get('NUCLEUS_DIAGNOSTIC_BINARY')
        if not binary: self.skipTest('CI supplies pinned binary and corpus')
        for name in ['perf/magma-list-deep-n21','perf/fueled-chain','init-prelude']:
            with (pathlib.Path('/tmp/current/good')/(name+'.ndjson')).open('rb') as f:
                r=subprocess.run([binary],stdin=f,capture_output=True,timeout=240,env=os.environ|{'NUCLEUS_TRACE_CAUSAL':'1'})
            self.assertEqual(r.returncode,2)
            events=[json.loads(x.split(':',1)[1]) for x in r.stderr.decode().splitlines() if x.startswith('NUCLEUS_CAUSAL:')]
            boundaries=[e for e in events if e['kind']=='boundary']
            self.assertTrue(boundaries,'missing existing recursor probe')
            probes=[e for e in events if e['scope']==boundaries[-1]['scope'] and e['kind']=='existing-recursor-shape']
            self.assertEqual([e['detail'] for e in probes],['passed=true'])
