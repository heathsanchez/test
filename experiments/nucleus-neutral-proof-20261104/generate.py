"""Checked distinct-neutral proof controls derived from the actual source declaration prefix."""
import argparse,json,hashlib
from pathlib import Path

def generate(source,out):
 out.mkdir(parents=True,exist_ok=True);names={0:''};base=[];me=-1;mn=0
 for raw in source.read_bytes().splitlines(keepends=True):
  row=json.loads(raw);base.append(raw)
  if 'in'in row:
   n=row.get('str',row.get('num'));names[row['in']]=names[n['pre']]+('.'if n['pre']else'')+str(n.get('str',n.get('i')));mn=max(mn,row['in'])
  if 'ie'in row:me=max(me,row['ie'])
  if any(names.get(row.get(k,{}).get('name'))=='Not'for k in ['def','opaque','thm']):break
 else:raise RuntimeError('actual Not declaration not found')
 ids={v:k for k,v in names.items()};rows=[];original=b''.join(base)
 for label,kind,ref in [('authentic-neutral-proof','good',0),('neutral-wrong-proposition','prop',1),('neutral-data-identity','data',1),('neutral-wrong-proof-argument','arg',1),('neutral-invalid-universe','levels',1)]:
  records=[];next_id=me+1
  def expr(**value):
   nonlocal next_id
   i=next_id;next_id+=1;records.append(dict(ie=i,**value));return i
  def const(name,us=[]):return expr(const=dict(name=ids[name],us=us))
  def app(fun,*args):
   for arg in args:fun=expr(app=dict(fn=fun,arg=arg))
   return fun
  def bv(i):return expr(bvar=i)
  def pi(d,b):return expr(forallE=dict(binderInfo='default',name=0,type=d,body=b))
  def lam(d,b):return expr(lam=dict(binderInfo='default',name=0,type=d,body=b))
  prop=expr(sort=0);notc=const('Not');nat=const('Nat')
  def neg(i):return app(notc,bv(i))
  ax=mn+1;ax2=mn+2;th=mn+3
  for name,text in [(ax,'NucleusNeutralAxiom_'+kind),(ax2,'NucleusNeutralSecond_'+kind),(th,'NucleusNeutralProof_'+kind)]:records.append({'in':name,'str':{'pre':0,'str':text}})
  axtype=pi(prop,pi(neg(0),pi(neg(1),pi(neg(2),nat if kind=='data'else neg(3)))))
  records.append({'axiom':dict(name=ax,levelParams=[],type=axtype,isUnsafe=False)})
  term=app(expr(const=dict(name=ax,us=[1]if kind=='levels'else[])),bv(18),bv(18)if kind=='arg'else bv(17),bv(16),bv(15))
  records.append({'axiom':dict(name=ax2,levelParams=[],type=pi(prop,nat if kind=='data'else bv(0)if kind=='prop'else neg(0)),isUnsafe=False)})
  local=app(expr(const=dict(name=ax2,us=[])),bv(18));carrier=nat if kind=='data'else neg(18)
  eq=app(const('Eq',[1]if kind=='data'else[0]),carrier,term,local)
  proof=app(const('Eq.refl',[1]if kind=='data'else[0]),carrier,local)
  ty=eq;value=proof
  for index in range(18,0,-1):
   domain=neg(index-1)
   ty=pi(domain,ty);value=lam(domain,value)
  ty=pi(prop,ty);value=lam(prop,value)
  records.append({'thm':dict(name=th,levelParams=[],type=ty,value=value,all=[th])})
  data=original+b''.join((json.dumps(x,sort_keys=True,separators=(',',':'))+'\n').encode()for x in records)
  p=out/(label+'.ndjson');p.write_bytes(data);rows.append(dict(case=label,file=p.name,sha256=hashlib.sha256(data).hexdigest(),expect_reference=ref))
 (out/'manifest.json').write_text(json.dumps(rows,indent=2)+'\n');return rows
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();generate(a.source,a.out)
