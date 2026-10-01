import copy,json,os,pathlib,subprocess,unittest
from slice_no_confusion import slice_prefix

OBLIGATIONS=[('perf/magma-list-deep-n21','GetElem?'),('perf/magma-list-deep-n36','GetElem?'),('perf/fueled-chain','Functor')]
class RecordTelescopes(unittest.TestCase):
    def rows(self,name,target):
        return list(map(json.loads,slice_prefix(pathlib.Path(os.environ.get('NUCLEUS_CORPUS','/tmp/current'))/'good'/(name+'.ndjson'),target).splitlines()))
    def run_rows(self,r):
        p=subprocess.run([os.environ['NUCLEUS_SUM_BINARY']],input=''.join(json.dumps(x)+'\n'for x in r),text=True,capture_output=True,timeout=60)
        self.assertIn(p.returncode,(0,1,2),p.stderr)
        return p.returncode
    def test_real_record_prefixes_close(self):
        for n,t in OBLIGATIONS:
            with self.subTest(target=t,source=n):self.assertEqual(self.run_rows(self.rows(n,t)),0)
    def test_successor_dependency_prefixes_close(self):
        for t in ['Applicative','Monad']:
            with self.subTest(target=t):self.assertEqual(self.run_rows(self.rows('perf/fueled-chain',t)),0)
    def test_renamed_records_close(self):
        for n,t in OBLIGATIONS[::2]:
            r=self.rows(n,t);b=[x['inductive']for x in r if 'inductive'in x][-1]
            next(x for x in r if x.get('in')==b['types'][0]['name'])['str']['str']='RenamedRecord'
            self.assertEqual(self.run_rows(r),0)
    def test_each_rule_annotation_is_checked(self):
        for n,t in OBLIGATIONS[::2]:
            base=self.rows(n,t);b=[x['inductive']for x in base if 'inductive'in x][-1];e={x['ie']:x for x in base if 'ie'in x}
            at=b['recs'][0]['rules'][0]['rhs']
            while 'lam'in e[at]:
                r=copy.deepcopy(base);next(x for x in r if x.get('ie')==at)['lam']['type']=b['types'][0]['type']
                self.assertNotEqual(self.run_rows(r),0)
                at=e[at]['lam']['body']
    def test_metadata_remains_checked(self):
        for n,t in OBLIGATIONS[::2]:
            base=self.rows(n,t)
            for kind,key,value in [('types','isRec',True),('types','numIndices',1),('types','numNested',1),('types','isReflexive',True),('types','isUnsafe',True),('ctors','cidx',1),('recs','numMinors',2),('recs','numMotives',2),('recs','k',True)]:
                r=copy.deepcopy(base);b=[x['inductive']for x in r if 'inductive'in x][-1];b[kind][0][key]=value
                self.assertNotEqual(self.run_rows(r),0)
    def witness_rows(self,name,target,projection=None):
        r=self.rows(name,target);b=[x['inductive']for x in r if 'inductive'in x][-1]
        c=b['ctors'][0];i=b['types'][0];e={x['ie']:x for x in r if 'ie'in x}
        ne=max(e)+1;nn=max(x.get('in',0)for x in r)+1;nl=max(x.get('il',0)for x in r)+1
        def expr(kind,v):
            nonlocal ne
            k=ne;ne+=1;row={'ie':k,kind:v};r.append(row);e[k]=row;return k
        def const(n,us):return expr('const',{'name':n,'us':us})
        def app(fn,*args):
            for arg in args:fn=expr('app',{'fn':fn,'arg':arg})
            return fn
        def bind(kind,ty,body):return expr(kind,{'name':0,'type':ty,'body':body,'binderInfo':'default'})
        def shift(k,amount,cutoff=0):
            x=e[k]
            if 'bvar'in x:return expr('bvar',x['bvar']+amount if x['bvar']>=cutoff else x['bvar'])
            for kind in ['lam','forallE']:
                if kind in x:return bind(kind,shift(x[kind]['type'],amount,cutoff),shift(x[kind]['body'],amount,cutoff+1))
            if 'app'in x:return app(shift(x['app']['fn'],amount,cutoff),shift(x['app']['arg'],amount,cutoff))
            if 'proj'in x:
                z=dict(x['proj']);z['struct']=shift(z['struct'],amount,cutoff);return expr('proj',z)
            if 'letE'in x:raise AssertionError('fixture requires let shifting')
            return k
        domains=[];at=c['type']
        for _ in range(c['numParams']+c['numFields']):domains.append(e[at]['forallE']['type']);at=e[at]['forallE']['body']
        p=c['numParams'];f=c['numFields'];n=p+f
        us=[]
        for u in i['levelParams']:
            r.append({'il':nl,'param':u});us.append(nl);nl+=1
        one=nl;r.append({'il':nl,'succ':0});nl+=1
        two=nl;r.append({'il':nl,'succ':one})
        args=[expr('bvar',n-1-k)for k in range(n)]
        major=app(const(c['name'],us),*args)
        if projection is not None:
            ty=shift(domains[p+projection],f-projection)
            value=expr('proj',{'typeName':i['name'],'idx':projection,'struct':major})
        else:
            prop=expr('sort',0);typ=expr('sort',one)
            sum_ty=app(const(i['name'],us),*args[:p])
            motive=bind('lam',sum_ty,typ)
            minor=prop
            for k in reversed(range(f)):
                minor=bind('lam',shift(domains[p+k],f,k),minor)
            ty=app(const(b['recs'][0]['name'],[two]+us),*args[:p],motive,minor,major)
            v0=expr('bvar',0);v1=expr('bvar',1)
            value=bind('forallE',prop,bind('forallE',v0,v1))
        for domain in reversed(domains):
            ty=bind('forallE',domain,ty);value=bind('lam',domain,value)
        r.append({'in':nn,'str':{'pre':0,'str':'recordRuntimeWitness'}})
        r.append({'def':{'name':nn,'levelParams':i['levelParams'],'all':[nn],'type':ty,'value':value,'hints':'opaque','safety':'safe'}})
        return r
    def test_runtime_iota_and_projections(self):
        for n,t in OBLIGATIONS[::2]+[('perf/fueled-chain','Applicative')]:
            f=[x['inductive']for x in self.rows(n,t)if 'inductive'in x][-1]['ctors'][0]['numFields']
            for projection in [None]+list(range(f)):
                with self.subTest(target=t,projection=projection):self.assertEqual(self.run_rows(self.witness_rows(n,t,projection)),0)

if __name__=='__main__':unittest.main()
