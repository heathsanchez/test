from pathlib import Path
import argparse,copy,json,hashlib,shutil

def generate(source,out):
 out.mkdir(parents=True,exist_ok=True);rows=[json.loads(s)for s in source.read_text().splitlines()];names={0:''};exprs={}
 for r in rows:
  if'in'in r:
   n=r.get('str',r.get('num'));names[r['in']]=names[n['pre']]+('.'if n['pre']else'')+str(n.get('str',n.get('i')))
  if'ie'in r:exprs[r['ie']]=r
 target=rows[-1];assert'thm'in target and names[target['thm']['name']]=='Multiset.coe_foldr_swap';base=[]
 for r in rows[:-1]:
  if'thm'in r:
   d=r['thm'];r={'axiom':dict(name=d['name'],levelParams=d['levelParams'],type=d['type'],isUnsafe=False)}
  base.append(r)
 manifest=[]
 def emit(case,extra,t,reference):
  p=out/(case+'.ndjson');p.write_text(''.join(json.dumps(r,separators=(',',':'))+'\n'for r in base+extra+[t]));manifest.append(dict(case=case,file=p.name,sha256=hashlib.sha256(p.read_bytes()).hexdigest(),expect_reference=reference,counterfactual_source_control=True))
 emit('quotient-result-authentic',[],target,0)
 fresh=max(exprs)+1;false=next(n for n,v in names.items()if v=='False');t=copy.deepcopy(target);t['thm']['type']=fresh
 emit('quotient-result-false-proof',[{'ie':fresh,'const':dict(name=false,us=[])}],t,1)
 t=copy.deepcopy(target);t['thm']['value']=fresh
 emit('quotient-result-unbound-source',[{'ie':fresh,'bvar':0}],t,1)
 def chain(root,tag):
  stack=[]
  while tag in exprs[root]:stack.append(exprs[root][tag]);root=exprs[root][tag]['body']
  return stack,root
 extra=[];nextid=fresh
 def node(tag,data):
  nonlocal nextid
  i=nextid;nextid+=1;extra.append(dict(ie=i,**{tag:data}));return i
 def close(stack,tag,body):
  for data in reversed(stack):body=node(tag,dict(data,body=body))
  return body
 telescope,body=chain(target['thm']['type'],'forallE');assert len(telescope)==6
 app=exprs[body]['app'];b=next(i for i,r in exprs.items()if r.get('bvar')==1)
 ty=close(telescope,'forallE',node('app',dict(app,arg=b)));t=copy.deepcopy(target);t['thm']['type']=ty
 emit('quotient-result-changed-data',extra,t,1)
 lambdas,body=chain(target['thm']['value'],'lam');assert len(lambdas)==6;args=[]
 while'app'in exprs[body]:args.append(exprs[body]['app']['arg']);body=exprs[body]['app']['fn']
 c=exprs[body]['const'];assert names[c['name']]=='Eq.trans'and len(c['us'])==1;extra=[];nextid=fresh
 body=node('const',dict(c,us=[0]))
 for arg in reversed(args):body=node('app',dict(fn=body,arg=arg))
 value=close(lambdas,'lam',body);t=copy.deepcopy(target);t['thm']['value']=value
 emit('quotient-result-wrong-universe',extra,t,1)
 p=out/'original-coe-foldr-swap.ndjson';shutil.copyfile(source,p);sha=hashlib.sha256(p.read_bytes()).hexdigest();assert sha=='13ea49b22c1d367dbe44a6301a4d4c71dd623e40afa8ab4b8e5728e5f1659d26'
 manifest.append(dict(case='authentic-original-coe-foldr-swap',file=p.name,sha256=sha,expect_reference=0))
 (out/'manifest.json').write_text(json.dumps(manifest,indent=2));print(json.dumps(manifest),flush=True)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();generate(a.source,a.out)
