import unittest
from causal_report import classify
class Report(unittest.TestCase):
    def test_shape_without_route_is_unresolved(self):
        block={'types':[{'isRec':False,'numIndices':0,'numNested':0,'isUnsafe':False,'isReflexive':False}], 'ctors':[{},{}], 'recs':[]}
        self.assertEqual(classify(block,[])['status'],'NO_REGISTERED_PATH')
    def test_shape_plus_measured_route_is_candidate_only(self):
        block={'types':[{'isRec':False,'numIndices':0,'numNested':0,'isUnsafe':False,'isReflexive':False}], 'ctors':[{},{}], 'recs':[]}
        events=[dict(kind='admission-route-miss',truncated=False)]
        self.assertEqual(classify(block,events)['status'],'CANDIDATE_PATH')
    def test_truncation_blocks_claim(self):
        self.assertEqual(classify({},[dict(truncated=True)])['status'],'UNRESOLVED_INCOMPLETE_TRACE')
