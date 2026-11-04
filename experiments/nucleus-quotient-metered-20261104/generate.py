"""Exact original source is a separate control; generated cases are counterfactual source controls."""
from pathlib import Path
import argparse,copy,json,hashlib

def generate(source,out):
 out.mkdir(parents=True,exist_ok=True);raw=[json.loads(x)for x in source.read_text().splitlines()];names={0:''};exprs={}
 for row in raw:
  if 'in'in row:
   x=row.get('str',row.get('num'));names[row['in']]=names[x['pre']]+('.'if x['pre']else'')+str(x.get('str',x.get('i')))
  if 'ie'in row:exprs[row['ie']]=row
 assert 'thm'in raw[-1] and names[raw[-1]['thm']['name']]=='Multiset.nodup_singleton'
 base=[]
 for row in raw[:-1]:
  if 'thm'in row:
   d=row['thm'];row={'axiom':dict(name=d['name'],levelParams=d['levelParams'],type=d['type'],isUnsafe=False)}
  base.append(row)
 target=raw[-1];fresh=max(exprs)+1;manifest=[]
 def emit(case,rows,expect):
  f=out/(case+'.ndjson');f.write_text(''.join(json.dumps(x,separators=(',',':'))+'\n'for x in rows));manifest.append(dict(case=case,file=f.name,sha256=hashlib.sha256(f.read_bytes()).hexdigest(),expect_reference=expect,counterfactual_source_control=True))
 emit('authentic-quotient-projection',base+[target],0)
 false=next(i for i,n in names.items()if n=='False');t=copy.deepcopy(target);t['thm']['type']=fresh
 emit('quotient-projection-false-proof',base+[{'ie':fresh,'const':{'name':false,'us':[]}},t],1)
 lam=exprs[target['thm']['value']]['lam'];app=exprs[lam['body']]['app'];fn=exprs[app['fn']]['const'];assert len(fn['us'])==1
 t=copy.deepcopy(target);t['thm']['value']=fresh+2
 nodes=[{'ie':fresh,'const':dict(fn,us=[0])},{'ie':fresh+1,'app':dict(app,fn=fresh)},{'ie':fresh+2,'lam':dict(lam,body=fresh+1)}]
 emit('quotient-projection-wrong-universe',base+nodes+[t],1)
 nodes=[{'ie':fresh,'bvar':1},{'ie':fresh+1,'app':dict(app,arg=fresh)},{'ie':fresh+2,'lam':dict(lam,body=fresh+1)}]
 emit('quotient-projection-unbound-source',base+nodes+[t],1)
 (out/'manifest.json').write_text(json.dumps(manifest,indent=2));print(json.dumps(manifest),flush=True)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();generate(a.source,a.out)
