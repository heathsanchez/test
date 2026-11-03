import argparse,json,hashlib
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--source',required=True);p.add_argument('--out',required=True);a=p.parse_args();source=Path(a.source).read_bytes();assert hashlib.sha256(source).hexdigest()=='d9d7b1fe7267a0806f65200abc64a9c7114fb8097a9da1f3687f2560a2568bb9';out=Path(a.out);out.mkdir(exist_ok=True,parents=True)
lines=source.splitlines(keepends=True);assert json.loads(lines[-1])['thm']['name']==11993;base=b''.join(lines[:-1]);manifest=[]
for label,name in [('constraint',6037),('coeffs',6039),('false-constraint',6037)]:
 rows=[];counter=[108300]
 def expr(o):
  n=counter[0];counter[0]+=1;rows.append(dict(ie=n,**o));return n
 def const(n,ls=[]):return expr(dict(const=dict(name=n,us=ls)))
 def app(f,a):return expr(dict(app=dict(fn=f,arg=a)))
 def apps(f,*args):
  for a in args:f=app(f,a)
  return f
 xs_type=apps(const(63,[0]),27457);ty=xs_type if label=='coeffs'else 27483
 expected=107973 if label=='coeffs'else 12
 if label=='false-constraint':expected=apps(const(3398),43283,apps(const(2647,[0]),27457,33400))
 actual=apps(const(name),12,5)
 goal=apps(1282,ty,actual,expected);proof=apps(2177,ty,expected)
 for type_,value_ in [(xs_type,107979),(27483,71533)]:
  goal=expr({'letE':{'name':0,'type':type_,'value':value_,'body':goal,'nondep':False}});proof=expr({'letE':{'name':0,'type':type_,'value':value_,'body':proof,'nondep':False}})
 for _ in range(8):
  goal=expr({'forallE':{'type':1,'body':goal,'name':0,'binderInfo':'default'}});proof=expr({'lam':{'type':1,'body':proof,'name':0,'binderInfo':'default'}})
 rows.insert(0,{'in':12001,'str':{'pre':0,'str':'NucleusCapturedTidy'+label}});rows.append({'thm':{'all':[12001],'levelParams':[],'name':12001,'type':goal,'value':proof}})
 target=out/(label+'.ndjson');target.write_bytes(base+b''.join((json.dumps(x,separators=(',',':'))+'\n').encode()for x in rows));manifest.append(dict(case=label,file=target.name,sha256=hashlib.sha256(target.read_bytes()).hexdigest(),expected_reference_rc=1 if label.startswith('false')else 0))
(out/'inputs.json').write_text(json.dumps(manifest,indent=2)+'\n')
