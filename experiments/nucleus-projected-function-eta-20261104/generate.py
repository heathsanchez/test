from pathlib import Path
import argparse,json,hashlib,shutil
from generate_prefix import generate as generate_prefix

def generate(source,foldlm,foldrm,out):
 generate_prefix(source,out)
 manifest=json.loads((out/'manifest.json').read_text())
 d=out
 meta=json.loads(source.open().readline())
 rows=[meta,{'il':1,'succ':0},{'ie':0,'sort':1}]
 for i,n in enumerate(('A','B','f','g','x'),1):rows.append({'in':i,'str':{'pre':0,'str':n}})
 rows += [{'ie':1,'const':{'name':1,'us':[]}},{'ie':2,'const':{'name':2,'us':[]}},{'ie':3,'const':{'name':3,'us':[]}},{'ie':4,'bvar':0},{'ie':5,'forallE':{'name':5,'type':1,'body':1,'binderInfo':'default'}},{'ie':6,'app':{'fn':3,'arg':4}}]
 for n,t in ((1,0),(2,0),(3,5)):rows.append({'axiom':{'name':n,'levelParams':[],'type':t,'isUnsafe':False}})
 cases=[]
 for label,domain in [('authentic',1),('wrong-lambda-domain',2)]:
  x=rows+[{'ie':7,'lam':{'name':5,'type':domain,'body':6,'binderInfo':'default'}},{'def':{'name':4,'levelParams':[],'type':5,'value':7,'hints':'opaque','safety':'safe','all':[4]}}]
  p=d/(label+'.ndjson');p.write_text(''.join(json.dumps(x,separators=(',',':'))+'\n' for x in x));cases.append((label,p))
 for label,path in cases:
  manifest.append(dict(case='eta-function-'+label,file=path.name,sha256=hashlib.sha256(path.read_bytes()).hexdigest(),expect_reference=0 if label=='authentic' else 1,counterfactual_source_control=True))
 dest=out/'original-foldlm-cons.ndjson';shutil.copyfile(foldlm,dest)
 assert hashlib.sha256(dest.read_bytes()).hexdigest()=='7a5a71599fb8240c88553967ae3d3146d1d26d176ef3cd2388608c25c4a2da29'
 manifest.append(dict(case='authentic-original-foldlm-cons',file=dest.name,sha256=hashlib.sha256(dest.read_bytes()).hexdigest(),expect_reference=0))
 dest=out/'original-foldrm-cons.ndjson';shutil.copyfile(foldrm,dest)
 assert hashlib.sha256(dest.read_bytes()).hexdigest()=='8fbfa485711e12b989548753fb35fd077e7bb71c9a7b5d53a91e3c4db93d87d4'
 manifest.append(dict(case='authentic-original-foldrm-cons',file=dest.name,sha256=hashlib.sha256(dest.read_bytes()).hexdigest(),expect_reference=0))
 (out/'manifest.json').write_text(json.dumps(manifest,indent=2))

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--foldlm',type=Path,required=True);p.add_argument('--foldrm',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();generate(a.source,a.foldlm,a.foldrm,a.out)
