import unittest
from causal_report import classify
class Report(unittest.TestCase):
    def test_shape_without_route_is_unresolved(self):
        block={'types':[{'isRec':False,'numIndices':0,'numNested':0,'isUnsafe':False,'isReflexive':False}], 'ctors':[{},{}], 'recs':[]}
        self.assertEqual(classify(block,[])['status'],'NO_REGISTERED_PATH')
    def test_shape_plus_measured_route_is_candidate_only(self):
        block={'types':[{'isRec':False,'numIndices':0,'numNested':0,'isUnsafe':False,'isReflexive':False}], 'ctors':[{},{}], 'recs':[]}
        events=[dict(kind='admission-route-miss',truncated=False),dict(kind='existing-recursor-shape',truncated=False,detail='passed=true')]
        self.assertEqual(classify(block,events)['status'],'CANDIDATE_PATH')
    def test_truncation_blocks_claim(self):
        self.assertEqual(classify({},[dict(truncated=True)])['status'],'UNRESOLVED_INCOMPLETE_TRACE')

class Scope(unittest.TestCase):
    def test_capped_missing_boundary_does_not_attach_other_declarations(self):
        import tempfile,pathlib,json
        from causal_report import report
        with tempfile.TemporaryDirectory() as d:
            p=pathlib.Path(d)/'good';p.mkdir()
            (p/'x.ndjson').write_text(json.dumps({'in':1,'str':{'pre':0,'str':'X'}})+'\n'+json.dumps({'axiom':{'name':1,'type':0}})+'\n')
            event={'scope':1,'kind':'typed-comparison','truncated':False,'detail':'prior-declaration'}
            limit={'scope':2,'kind':'trace-limit','truncated':True,'detail':''}
            trace='\n'.join('NUCLEUS_CAUSAL:'+json.dumps(e) for e in (event,limit))+'\nNUCLEUS_DOWNSTREAM:name=X:stage=axiom.type:verdict=UNKNOWN:reason=budget'
            r=report(d,[dict(test='x',expected=0,candidate=2,trace=trace)])['rows'][0]
            self.assertEqual(r['events'],[])
            self.assertEqual(r['plan']['status'],'UNRESOLVED_INCOMPLETE_TRACE')
            self.assertEqual(len(r['unscoped_events']),2)

class ExistingCheck(unittest.TestCase):
    def test_shape_route_without_existing_check_is_not_composed(self):
        block={'types':[{'isRec':False,'numIndices':0,'numNested':0,'isUnsafe':False,'isReflexive':False}], 'ctors':[{},{}], 'recs':[]}
        self.assertEqual(classify(block,[dict(kind='admission-route-miss',truncated=False)])['status'],'NO_REGISTERED_PATH')
    def test_failed_existing_check_is_not_composed(self):
        block={'types':[{'isRec':False,'numIndices':0,'numNested':0,'isUnsafe':False,'isReflexive':False}], 'ctors':[{},{}], 'recs':[]}
        self.assertEqual(classify(block,[dict(kind='admission-route-miss',truncated=False),dict(kind='existing-recursor-shape',truncated=False,detail='passed=false')])['status'],'NO_REGISTERED_PATH')
