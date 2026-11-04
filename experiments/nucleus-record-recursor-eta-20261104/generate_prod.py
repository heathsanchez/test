"""Actual source product recursor eta differential controls."""
import argparse,json,hashlib
from pathlib import Path

def generate(source,out):
 out.mkdir(parents=True,exist_ok=True);base=[];names={0:''};me=-1;mn=0
 for raw in source.read_bytes().splitlines(keepends=True):
  x=json.loads(raw);base.append(raw)
  if'in'in x:
   n=x.get('str',x.get('num'));names[x['in']]=names[n['pre']]+('.'if n['pre']else'')+str(n.get('str',n.get('i')));mn=max(mn,x['in'])
  if'ie'in x:me=max(me,x['ie'])
  if'inductive'in x and any(names.get(t['name'])=='Prod'for t in x['inductive']['types']):break
 else:raise RuntimeError('actual product declaration absent')
 original=b''.join(base);ids={v:k for k,v in names.items()};rows=[]
 for label,kind,ref in [('authentic-product-recursor-eta','good',0),('product-recursor-wrong-field','field',1),('product-recursor-wrong-major','major',1),('product-recursor-wrong-universe','universe',1),('product-recursor-illtyped-minor','minor',1)]:
  records=[];next_id=me+1
  def expr(**v):
   nonlocal next_id
   i=next_id;next_id+=1;records.append(dict(ie=i,**v));return i
  def const(name,us=[]):return expr(const=dict(name=ids[name],us=us))
  def app(f,*args):
   for arg in args:f=expr(app=dict(fn=f,arg=arg))
   return f
  def bv(i):return expr(bvar=i)
  def lam(d,b):return expr(lam=dict(binderInfo='default',name=0,type=d,body=b))
  nat=const('Nat');product=app(const('Prod',[0,0]),nat,nat);motive=lam(product,nat)
  minor=lam(nat,lam(nat,nat if kind=='minor'else bv(1)));major=const('Nat.zero')if kind=='major'else bv(0)
  value=app(const('Prod.rec',[1,1,0]if kind=='universe'else[1,0,0]),nat,nat,motive,minor,major)
  wanted=expr(proj=dict(typeName=ids['Prod'],idx=1 if kind=='field'else 0,struct=bv(0)))
  typ=app(const('Eq',[1]),nat,value,wanted);proof=app(const('Eq.refl',[1]),nat,wanted)
  typ=expr(forallE=dict(binderInfo='default',name=0,type=product,body=typ));proof=lam(product,proof);name=mn+1
  records.append({'in':name,'str':dict(pre=0,str='NucleusProductRecursorEta_'+kind)});records.append({'thm':dict(name=name,levelParams=[],type=typ,value=proof,all=[name])})
  data=original+b''.join((json.dumps(x,separators=(',',':'))+'\n').encode()for x in records);p=out/(label+'.ndjson');p.write_bytes(data);rows.append(dict(case=label,file=p.name,sha256=hashlib.sha256(data).hexdigest(),expect_reference=ref))
 (out/'manifest.json').write_text(json.dumps(rows,indent=2));return rows
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();generate(a.source,a.out)
