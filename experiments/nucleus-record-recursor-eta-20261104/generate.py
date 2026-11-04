"""Source-certified nonrecursive record recursor eta controls."""
import argparse,json,hashlib
from pathlib import Path

def generate(source,out):
 out.mkdir(parents=True,exist_ok=True);base=source.read_bytes();records=[json.loads(x)for x in base.splitlines()];names={0:''};me=-1;mn=0
 for x in records:
  if'in'in x:
   n=x.get('str',x.get('num'));names[x['in']]=names[n['pre']]+('.'if n['pre']else'')+str(n.get('str',n.get('i')));mn=max(mn,x['in'])
  if'ie'in x:me=max(me,x['ie'])
 ids={v:k for k,v in names.items()};rows=[]
 for label,kind,ref in [('authentic-record-recursor-eta','good',0),('record-recursor-wrong-field','field',1),('record-recursor-wrong-major','major',1)]:
  tail=[];next_id=me+1
  def expr(**v):
   nonlocal next_id
   i=next_id;next_id+=1;tail.append(dict(ie=i,**v));return i
  def const(name,us=[]):return expr(const=dict(name=ids[name],us=us))
  def app(f,*args):
   for arg in args:f=expr(app=dict(fn=f,arg=arg))
   return f
  def bv(i):return expr(bvar=i)
  def lam(d,b):return expr(lam=dict(binderInfo='default',name=0,type=d,body=b))
  c=const('C');nat=const('Nat');motive=lam(c,nat);minor=lam(nat,lam(nat,bv(1)));major=const('Nat.zero')if kind=='major'else bv(0)
  value=app(const('C.rec',[3]),motive,minor,major);wanted=expr(proj=dict(typeName=ids['C'],idx=1 if kind=='field'else 0,struct=bv(0)))
  typ=app(const('Eq',[3]),nat,value,wanted);proof=app(const('Eq.refl',[3]),nat,wanted)
  typ=expr(forallE=dict(binderInfo='default',name=0,type=c,body=typ));proof=lam(c,proof);name=mn+1;tail.append({'in':name,'str':dict(pre=0,str='NucleusRecordRecEta_'+kind)});tail.append({'thm':dict(name=name,levelParams=[],type=typ,value=proof,all=[name])})
  suffix=b''.join((json.dumps(x,separators=(',',':'))+'\n').encode()for x in tail);data=base+suffix;(out/(label+'.ndjson')).write_bytes(data);(out/(label+'.suffix')).write_bytes(suffix)
  rows.append(dict(case=label,file=label+'.ndjson',sha256=hashlib.sha256(data).hexdigest(),expect_reference=ref))
 (out/'manifest.json').write_text(json.dumps(rows,indent=2));return rows
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();generate(a.source,a.out)
