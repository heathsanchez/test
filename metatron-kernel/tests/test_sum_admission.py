"""Real exported SourceInfo obligations; no checker-name special cases."""
import copy
import json
import os
import pathlib
import subprocess
import unittest
from slice_no_confusion import slice_prefix


class ClosedSumAdmission(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.binary = os.environ['NUCLEUS_SUM_BINARY']
        root = pathlib.Path(os.environ.get('NUCLEUS_CORPUS', '/tmp/current'))
        cls.sources = [root/'good/init-prelude.ndjson', root/'good/perf/grind-ring-5.ndjson']
        cls.rows = [json.loads(s) for s in slice_prefix(cls.sources[0], 'Lean.SourceInfo').splitlines()]

    def run_rows(self, rows):
        p = subprocess.run([self.binary], input=''.join(json.dumps(r)+'\n' for r in rows),
                           text=True, capture_output=True, timeout=60)
        self.assertIn(p.returncode, (0, 1, 2), p.stderr)
        return p.returncode

    def block(self, rows):
        return [r['inductive'] for r in rows if 'inductive' in r][-1]

    def expr(self, rows, i):
        return next(r for r in rows if r.get('ie') == i)

    def test_real_prefixes_close(self):
        for source in self.sources:
            with self.subTest(source=source.name):
                rows = [json.loads(s) for s in slice_prefix(source, 'Lean.SourceInfo').splitlines()]
                self.assertEqual(self.run_rows(rows), 0, 'SourceInfo prefix must close')

    def test_renaming_preserves_admission(self):
        r=copy.deepcopy(self.rows)
        next(x for x in r if x.get('in')==1691)['str']['str']='ClosedSumRenamed'
        self.assertEqual(self.run_rows(r), 0)

    def test_wrong_minor_field_type(self):
        r=copy.deepcopy(self.rows)
        # The synthetic third field has optParam Bool false, not Nat.
        self.expr(r, 8080)['forallE']['type']=8016
        self.assertNotEqual(self.run_rows(r),0)

    def test_every_rule_annotation(self):
        for i in list(range(8094,8102))+list(range(8102,8109))+list(range(8109,8113)):
            r=copy.deepcopy(self.rows)
            self.expr(r,i)['lam']['type']=0
            self.assertNotEqual(self.run_rows(r),0, f'rule annotation {i}')

    def test_universe_recursive_open_fields(self):
        # Change the constructor alone: these must not acquire admission.
        for typ in (0,8053,5):
            r=copy.deepcopy(self.rows)
            self.expr(r,8057)['forallE']['type']=typ
            self.assertNotEqual(self.run_rows(r),0)

    def test_metadata(self):
        for key,value in [('isRec',True),('isReflexive',True),('isUnsafe',True),
                          ('numIndices',1),('numNested',1),('numParams',1)]:
            r=copy.deepcopy(self.rows); self.block(r)['types'][0][key]=value
            self.assertNotEqual(self.run_rows(r),0, key)
        for key,value in [('numParams',1),('numIndices',1),('numMinors',2),
                          ('numMotives',2),('k',True),('isUnsafe',True)]:
            r=copy.deepcopy(self.rows); self.block(r)['recs'][0][key]=value
            self.assertNotEqual(self.run_rows(r),0,key)
        for key,value in [('ctor',1691),('nfields',3)]:
            r=copy.deepcopy(self.rows); self.block(r)['recs'][0]['rules'][0][key]=value
            self.assertNotEqual(self.run_rows(r),0,key)


if __name__ == '__main__':
    unittest.main()
