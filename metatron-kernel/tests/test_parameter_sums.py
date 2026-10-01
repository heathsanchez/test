import copy
import json
import os
import pathlib
import subprocess
import unittest
from slice_no_confusion import slice_prefix

OBLIGATIONS=[('perf/magma-list-deep-n21','Option'),('perf/magma-list-deep-n36','Option'),('perf/fueled-chain','Except')]

class ParameterSums(unittest.TestCase):
    def rows(self, name, target):
        root=pathlib.Path(os.environ.get('NUCLEUS_CORPUS','/tmp/current'))
        return list(map(json.loads,slice_prefix(root/'good'/(name+'.ndjson'),target).splitlines()))

    def run_rows(self,rows):
        p=subprocess.run([os.environ['NUCLEUS_SUM_BINARY']],input=''.join(json.dumps(r)+'\n'for r in rows),text=True,capture_output=True,timeout=60)
        self.assertIn(p.returncode,(0,1,2),p.stderr)
        return p.returncode

    def test_real_parameter_prefixes_close(self):
        for name,target in OBLIGATIONS:
            with self.subTest(name=name):self.assertEqual(self.run_rows(self.rows(name,target)),0)

    def test_renamed_parameter_sums_close(self):
        for name,target in OBLIGATIONS[::2]:
            r=self.rows(name,target)
            b=[x['inductive']for x in r if 'inductive'in x][-1]
            n=b['types'][0]['name']
            next(x for x in r if x.get('in')==n)['str']['str']='RenamedParameterSum'
            self.assertEqual(self.run_rows(r),0)

    def test_parameter_sum_metadata(self):
        for name,target in OBLIGATIONS[::2]:
            base=self.rows(name,target)
            for key,val in [('numParams',0),('numIndices',1),('numNested',1),('isRec',True),('isReflexive',True),('isUnsafe',True)]:
                r=copy.deepcopy(base);b=[x['inductive']for x in r if 'inductive'in x][-1]
                b['types'][0][key]=val
                self.assertNotEqual(self.run_rows(r),0)

    def test_parameter_rule_annotations(self):
        for name,target in OBLIGATIONS[::2]:
            base=self.rows(name,target);b=[x['inductive']for x in base if 'inductive'in x][-1]
            expr={x['ie']:x for x in base if 'ie'in x}
            for rule in b['recs'][0]['rules']:
                t=rule['rhs']
                while 'lam'in expr[t]:
                    r=copy.deepcopy(base)
                    next(x for x in r if x.get('ie')==t)['lam']['type']=b['types'][0]['type']
                    self.assertNotEqual(self.run_rows(r),0)
                    t=expr[t]['lam']['body']

if __name__=='__main__':unittest.main()
