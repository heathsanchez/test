import argparse,json,hashlib
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--source',required=True);p.add_argument('--out',required=True);a=p.parse_args();source=Path(a.source).read_bytes();assert hashlib.sha256(source).hexdigest()=='d9d7b1fe7267a0806f65200abc64a9c7114fb8097a9da1f3687f2560a2568bb9';out=Path(a.out);out.mkdir(exist_ok=True,parents=True)
lines=source.splitlines(keepends=True);assert json.loads(lines[-1])['thm']['name']==11993;base=b''.join(lines[:-1]);manifest=[]
for label,name,expected,ty in [('constraint',6037,71533,27483),('coeffs',6039,107973,None),('false-constraint',6037,71533,27483)]:
 rows=[];counter=[108300]
 def expr(o):
  n=counter[0];counter[0]+=1;rows.append(dict(ie=n,**o));return n
 def const(n,ls=[]):return expr(dict(const=dict(name=n,us=ls)))
 def app(f,a):return expr(dict(app=dict(fn=f,arg=a)))
 def apps(f,*args):
  for a in args:f=app(f,a)
  return f
 if ty is None:ty=apps(const(63,[0]),27457)
 actual=apps(const(name),71533,107979)
 if label=='false-constraint':
  # Different upper bound: existing Int one vs both original Int zero bounds.
  expected=apps(const(3398),43283,apps(const(2647,[0]),27457,33400))
 goal=apps(1282,ty,actual,expected);proof=apps(2177,ty,expected)
 rows.insert(0,{'in':12001,'str':{'pre':0,'str':'NucleusClosedTidy'+label}});rows.append({'thm':{'all':[12001],'levelParams':[],'name':12001,'type':goal,'value':proof}})
 target=out/(label+'.ndjson');target.write_bytes(base+b''.join((json.dumps(x,separators=(',',':'))+'\n').encode()for x in rows));manifest.append(dict(case=label,file=target.name,sha256=hashlib.sha256(target.read_bytes()).hexdigest(),expected_rc=1 if label.startswith('false')else 0))
(out/'inputs.json').write_text(json.dumps(manifest,indent=2)+'\n')
