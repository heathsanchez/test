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

    def test_constructor_and_recursor_contracts(self):
        for name,target in OBLIGATIONS[::2]:
            base=self.rows(name,target)
            for key,val in [('numParams',0),('numIndices',1),('numMinors',1),('numMotives',2),('k',True)]:
                r=copy.deepcopy(base);b=[x['inductive']for x in r if 'inductive'in x][-1]
                b['recs'][0][key]=val
                self.assertNotEqual(self.run_rows(r),0)
            for key,val in [('cidx',9),('induct',0),('numFields',3)]:
                r=copy.deepcopy(base);b=[x['inductive']for x in r if 'inductive'in x][-1]
                b['ctors'][1][key]=val
                self.assertNotEqual(self.run_rows(r),0)
            r=copy.deepcopy(base);b=[x['inductive']for x in r if 'inductive'in x][-1]
            b['types'][0]['levelParams']=[]
            self.assertNotEqual(self.run_rows(r),0)

    def test_field_and_parameter_domains_are_checked(self):
        for name,target in OBLIGATIONS[::2]:
            base=self.rows(name,target);b=[x['inductive']for x in base if 'inductive'in x][-1]
            expr={x['ie']:x for x in base if 'ie'in x}
            for ctor in b['ctors']:
                t=ctor['type']
                for _ in range(ctor['numParams']+ctor['numFields']):
                    r=copy.deepcopy(base)
                    next(x for x in r if x.get('ie')==t)['forallE']['type']=b['types'][0]['type']
                    self.assertNotEqual(self.run_rows(r),0)
                    t=expr[t]['forallE']['body']

    def test_each_parameter_iota_branch(self):
        for name,target in OBLIGATIONS[::2]:
            for j in range(2):
                self.assertEqual(self.run_rows(self.iota_rows(name,target,j)),0)

    def iota_rows(self,name,target,index):
        r=self.rows(name,target)
        b=[x['inductive']for x in r if 'inductive'in x][-1]
        ne=max(x.get('ie',0)for x in r)+1
        nn=max(x.get('in',0)for x in r)+1
        nl=max(x.get('il',0)for x in r)+1
        r.append({'il':nl,'succ':0})
        def expr(kind,v):
            nonlocal ne
            n=ne;ne+=1;r.append({'ie':n,kind:v});return n
        def const(n,ls):return expr('const',{'name':n,'us':ls})
        def app(f,*args):
            for a in args:f=expr('app',{'fn':f,'arg':a})
            return f
        def bind(kind,t,body):return expr(kind,{'name':0,'type':t,'body':body,'binderInfo':'default'})
        prop=expr('sort',0);typ=expr('sort',nl)
        v0=expr('bvar',0);v1=expr('bvar',1)
        proposition=bind('forallE',prop,bind('forallE',v0,v1))
        other=bind('forallE',prop,prop)
        p=b['types'][0]['numParams'];levels=[0]*p;params=[prop]*p
        sum_ty=app(const(b['types'][0]['name'],levels),*params)
        motive=bind('lam',sum_ty,typ)
        minors=[]
        for j,c in enumerate(b['ctors']):
            m=prop if j==index else other
            if c['numFields']:m=bind('lam',prop,m)
            minors.append(m)
        c=b['ctors'][index]
        major=app(const(c['name'],levels),*params)
        if c['numFields']:major=app(major,proposition)
        reduced=app(const(b['recs'][0]['name'],[nl]+levels),*params,motive,*minors,major)
        r.append({'in':nn,'str':{'pre':0,'str':f'parameterIota{index}'}})
        r.append({'def':{'name':nn,'levelParams':[],'all':[nn],'type':reduced,'value':proposition,'hints':'opaque','safety':'safe'}})
        return r

if __name__=='__main__':unittest.main()
