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

    def test_coherent_large_universe_field(self):
        r=copy.deepcopy(self.rows)
        # Change the same first field in ctor, minor and rule. Shape matches,
        # but Type itself cannot be stored by this Type 0 admission law.
        for i,kind in [(8057,'forallE'),(8074,'forallE'),(8097,'lam')]:
            self.expr(r,i)[kind]['type']=0
        self.assertNotEqual(self.run_rows(r),0)

    def test_all_iota_branches_execute(self):
        for index in range(3):
            r=self.iota_rows(index)
            self.assertEqual(self.run_rows(r),0,f'constructor {index}')

    def iota_rows(self, index):
        r=copy.deepcopy(self.rows)
        next_expr=max(x.get('ie',0) for x in r)+1
        next_name=max(x.get('in',0) for x in r)+1
        def name(s):
            nonlocal next_name
            n=next_name; next_name+=1
            r.append({'in':n,'str':{'pre':0,'str':s}})
            return n
        def expr(kind,value):
            nonlocal next_expr
            i=next_expr;next_expr+=1;r.append({'ie':i,kind:value});return i
        def const(n,us=[]):return expr('const',{'name':n,'us':us})
        def app(f,*args):
            for a in args:f=expr('app',{'fn':f,'arg':a})
            return f
        def lam(t,b):return expr('lam',{'name':0,'type':t,'body':b,'binderInfo':'default'})
        b=self.block(r)
        true=const(130);false=const(129);bool_ty=const(128)
        fields=[]
        for ctor in b['ctors']:
            ds=[];t=ctor['type']
            for _ in range(ctor['numFields']):
                p=self.expr(r,t)['forallE'];ds.append(p['type']);t=p['body']
            fields.append(ds)
        minors=[]
        for j,ds in enumerate(fields):
            m=true if j==index else false
            for d in reversed(ds):m=lam(d,m)
            minors.append(m)
        major=const(b['ctors'][index]['name'])
        for k,d in enumerate(fields[index]):
            n=name(f'sumField{index}_{k}')
            r.append({'axiom':{'name':n,'levelParams':[],'type':d,'isUnsafe':False}})
            major=app(major,const(n))
        motive=lam(const(1691),bool_ty)
        result=app(const(1700,[1]),motive,*minors,major)
        ty=app(const(45,[1]),bool_ty,result,true)
        proof=app(const(46,[1]),bool_ty,true)
        n=name(f'sumIota{index}')
        r.append({'thm':{'name':n,'levelParams':[],'all':[n],'type':ty,'value':proof}})
        return r

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
