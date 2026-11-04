"""Source eta controls for the positively checked nonrecursive parameter-record scope."""
import argparse,json,hashlib,copy
from pathlib import Path

def generate(source,out):
 out.mkdir(parents=True,exist_ok=True);core=[];names={0:''};expressions={};me=-1;mn=0;block=None
 for raw in source.read_bytes().splitlines(keepends=True):
  x=json.loads(raw);core.append(x)
  if'in'in x:
   n=x.get('str',x.get('num'));names[x['in']]=names[n['pre']]+('.'if n['pre']else'')+str(n.get('str',n.get('i')));mn=max(mn,x['in'])
  if'ie'in x:expressions[x['ie']]=x;me=max(me,x['ie'])
  if'inductive'in x and any(names.get(t['name'])=='RingHom'for t in x['inductive']['types']):block=x['inductive'];break
 if block is None:raise RuntimeError('actual RingHom declaration absent')
 owner=block['types'][0];ctor=block['ctors'][0];p=owner['numParams'];fields=ctor['numFields'];node=owner['type'];domains=[]
 for _ in range(p):domains.append(expressions[node]['forallE']['type']);node=expressions[node]['forallE']['body']
 carrier=expressions[node]['sort'];node=ctor['type']
 for _ in range(p+fields):node=expressions[node]['forallE']['body']
 while'app'in expressions[node]:node=expressions[node]['app']['fn']
 us=expressions[node]['const']['us'];ids={v:k for k,v in names.items()};rows=[]
 for label,kind,ref in [('authentic-parameter-record-eta','good',0),('parameter-record-wrong-receiver','receiver',1),('parameter-record-forged-nonrecursive-field','recursive',1),('parameter-record-prop-collapse','prop',1)]:
  base=copy.deepcopy(core);tail=[];next_id=me+1
  def expr(**v):
   nonlocal next_id
   i=next_id;next_id+=1;tail.append(dict(ie=i,**v));return i
  def bv(i):return expr(bvar=i)
  def const(name,levels=[]):return expr(const=dict(name=name,us=levels))
  def app(f,*args):
   for a in args:f=expr(app=dict(fn=f,arg=a))
   return f
  def product(depth):return app(const(owner['name'],us),*(bv(depth-1-i)for i in range(p)))
  if kind=='recursive':
   recursive_type=product(p);node=ctor['type']
   for _ in range(p):node=expressions[node]['forallE']['body']
   target=next(x for x in base if x.get('ie')==node);target['forallE']['type']=recursive_type
   # Preserve the forged isRec=false bit: the owner-occurrence certificate
   # itself must prevent this field from earning nonrecursive eta metadata.
   assert base[-1]['inductive']['types'][0]['isRec']is False
  elif kind=='prop':
   zero=expr(sort=0);node=owner['type']
   for _ in range(p-1):node=expressions[node]['forallE']['body']
   next(x for x in base if x.get('ie')==node)['forallE']['body']=zero
  # Insert fresh expression nodes before the declaration that uses a forged
  # carrier/field. IDs are globally fresh even though their rows precede it.
  if kind in ['recursive','prop']:
   base=base[:-1]+tail+[base[-1]];tail=[]
  data_type=product(p);depth=p+1
  if kind=='receiver':depth+=1
  actual_type=product(depth);f=bv(1 if kind=='receiver'else 0);receiver=bv(0)
  arguments=[bv(depth-1-i)for i in range(p)]
  arguments +=[expr(proj=dict(typeName=owner['name'],idx=i,struct=receiver))for i in range(fields)]
  rebuilt=app(const(ctor['name'],us),*arguments)
  typ=app(const(ids['Eq'],[carrier]),actual_type,f,rebuilt);proof=app(const(ids['Eq.refl'],[carrier]),actual_type,f)
  def pi(d,b):return expr(forallE=dict(binderInfo='default',name=0,type=d,body=b))
  def lam(d,b):return expr(lam=dict(binderInfo='default',name=0,type=d,body=b))
  if kind=='receiver':
   second_type=product(p+1);typ=pi(second_type,typ);proof=lam(second_type,proof)
  typ=pi(data_type,typ);proof=lam(data_type,proof)
  for domain in reversed(domains):typ=pi(domain,typ);proof=lam(domain,proof)
  name=mn+1;tail.append({'in':name,'str':dict(pre=0,str='NucleusParameterRecordEta_'+kind)});tail.append({'thm':dict(name=name,levelParams=owner['levelParams'],type=typ,value=proof,all=[name])})
  data=b''.join((json.dumps(x,separators=(',',':'))+'\n').encode()for x in base+tail);path=out/(label+'.ndjson');path.write_bytes(data);rows.append(dict(case=label,file=path.name,sha256=hashlib.sha256(data).hexdigest(),expect_reference=ref))
 (out/'manifest.json').write_text(json.dumps(rows,indent=2));return rows
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();generate(a.source,a.out)
