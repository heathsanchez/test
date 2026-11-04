"""Generated source controls are counterfactual; exact original input is checked separately."""
from pathlib import Path
import argparse,copy,json,hashlib

def generate(source,out):
 out.mkdir(parents=True,exist_ok=True);rows=[json.loads(x)for x in source.read_text().splitlines()];names={0:''};exprs={}
 for r in rows:
  if'in'in r:
   n=r.get('str',r.get('num'));names[r['in']]=names[n['pre']]+('.'if n['pre']else'')+str(n.get('str',n.get('i')))
  if'ie'in r:exprs[r['ie']]=r
 target=rows[-1];assert'thm'in target and names[target['thm']['name']]=='Multiset.singleton_add';base=[]
 for r in rows[:-1]:
  if'thm'in r:
   d=r['thm'];r={'axiom':dict(name=d['name'],levelParams=d['levelParams'],type=d['type'],isUnsafe=False)}
  base.append(r)
 manifest=[]
 def emit(case,extra,t,reference):
  f=out/(case+'.ndjson');f.write_text(''.join(json.dumps(r,separators=(',',':'))+'\n'for r in base+extra+[t]));manifest.append(dict(case=case,file=f.name,sha256=hashlib.sha256(f.read_bytes()).hexdigest(),expect_reference=reference,counterfactual_source_control=True))
 emit('authentic-dependent-prefix',[],target,0)
 fresh=max(exprs)+1;false=next(i for i,n in names.items()if n=='False');t=copy.deepcopy(target);t['thm']['type']=fresh
 emit('dependent-prefix-false-proof',[{'ie':fresh,'const':dict(name=false,us=[])}],t,1)
 def chain(root,key):
  stack=[]
  while key in exprs[root]:
   stack.append(exprs[root][key]);root=exprs[root][key]['body']
  return stack,root
 types,eqbody=chain(target['thm']['type'],'forallE');assert len(types)==3;eq=exprs[eqbody]['app'];rhs=eq['arg'];cons=exprs[rhs]['app'];extra=[];nextid=fresh
 def node(key,payload):
  nonlocal nextid
  raw=nextid;nextid+=1;extra.append({'ie':raw,key:payload});return raw
 def close(stack,key,body):
  for item in reversed(stack):body=node(key,dict(item,body=body))
  return body
 duplicate=node('app',dict(cons,arg=rhs));new_eq=node('app',dict(eq,arg=duplicate));new_ty=close(types,'forallE',new_eq);t=copy.deepcopy(target);t['thm']['type']=new_ty
 emit('dependent-prefix-trailing-data',extra,t,1)
 lambdas,proof=chain(target['thm']['value'],'lam');assert len(lambdas)==3;body=exprs[proof]['app'];fn=exprs[body['fn']]['app'];constant=exprs[fn['fn']]['const'];assert names[constant['name']]in('rfl','Eq.refl');extra=[];nextid=fresh
 bad_const=node('const',dict(constant,us=[0]));bad_fn=node('app',dict(fn,fn=bad_const));bad_body=node('app',dict(body,fn=bad_fn));bad_value=close(lambdas,'lam',bad_body);t=copy.deepcopy(target);t['thm']['value']=bad_value
 emit('dependent-prefix-wrong-universe',extra,t,1)
 (out/'manifest.json').write_text(json.dumps(manifest,indent=2));print(json.dumps(manifest),flush=True)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();generate(a.source,a.out)
