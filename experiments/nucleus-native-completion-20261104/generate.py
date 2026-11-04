"""Source controls for registered-native completion; no desired-value reduction rule."""
import argparse,json,hashlib
from pathlib import Path

def generate(source,out):
 out.mkdir(parents=True,exist_ok=True)
 lines=source.read_bytes().splitlines(keepends=True);names={0:''};core=[];maximum_expr=-1;maximum_name=0
 for raw in lines:
  core.append(raw);row=json.loads(raw)
  if 'in'in row:
   n=row.get('str',row.get('num'));names[row['in']]=names[n['pre']]+('.'if n['pre']else'')+str(n.get('str',n.get('i')));maximum_name=max(maximum_name,row['in'])
  if 'ie'in row:maximum_expr=max(maximum_expr,row['ie'])
  if 'def'in row and names.get(row['def']['name'])=='Nat.sub':break
 else:raise RuntimeError('Nat.sub source declaration absent')
 ids={v:k for k,v in names.items()};base=b''.join(core);rows=[]
 def emit(label,data,ref):
  path=out/(label+'.ndjson');path.write_bytes(data);rows.append(dict(case=label,file=path.name,sha256=hashlib.sha256(data).hexdigest(),expect_reference=ref))
 emit('authentic-int-ble',source.read_bytes(),0)
 for label,kind,reference in [('authentic-native-ground','good',0),('native-wrong-numeral','number',1),('native-wrong-boolean','boolean',1),('native-symbolic-predecessor','symbolic',1)]:
  records=[];next_id=maximum_expr+1
  def expr(**value):
   nonlocal next_id
   i=next_id;next_id+=1;records.append(dict(ie=i,**value));return i
  def const(name):return expr(const=dict(name=ids[name],us=[]))
  def app(fun,*args):
   for arg in args:fun=expr(app=dict(fn=fun,arg=arg))
   return fun
  def lam(domain,body):return expr(lam=dict(binderInfo='default',name=0,type=domain,body=body))
  nat=const('Nat');zero=expr(natVal='0');one=expr(natVal='1');succ_zero=app(const('Nat.succ'),const('Nat.zero'))
  sub=app(const('Nat.sub'),one,succ_zero);motive=lam(nat,nat);step=lam(nat,lam(nat,expr(bvar=1)))
  recursor=expr(const=dict(name=ids['Nat.rec'],us=[1]));value=app(recursor,motive,sub,step,zero)
  eq=expr(const=dict(name=ids['Eq'],us=[1]));refl=expr(const=dict(name=ids['Eq.refl'],us=[1]))
  if kind=='symbolic':
   variable=expr(bvar=0);term=app(const('Nat.pred'),variable);ty=expr(forallE=dict(binderInfo='default',name=0,type=nat,body=app(eq,nat,term,zero)));proof=lam(nat,app(refl,nat,zero))
  elif kind=='boolean':
   boolean=const('Bool');term=app(const('Nat.beq'),value,zero);wrong=const('Bool.false');ty=app(eq,boolean,term,wrong);proof=app(refl,boolean,wrong)
  else:
   wanted=one if kind=='number'else zero;ty=app(eq,nat,value,wanted);proof=app(refl,nat,wanted)
  name=maximum_name+1;records.append({'in':name,'str':{'pre':0,'str':'NucleusNativeCompletion_'+kind}})
  assert 'NucleusNativeCompletion_'+kind not in ids
  records.append({'thm':dict(name=name,levelParams=[],type=ty,value=proof,all=[name])})
  data=base+b''.join((json.dumps(x,sort_keys=True,separators=(',',':'))+'\n').encode()for x in records)
  emit(label,data,reference)
 (out/'manifest.json').write_text(json.dumps(rows,indent=2)+'\n');return rows
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--source',required=True,type=Path);p.add_argument('--out',required=True,type=Path);a=p.parse_args();generate(a.source,a.out)
