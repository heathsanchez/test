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
if __name__=='__main__':unittest.main()
