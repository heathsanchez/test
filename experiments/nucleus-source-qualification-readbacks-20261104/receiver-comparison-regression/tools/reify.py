from pathlib import Path
import json,hashlib,sys,subprocess,os
sys.setrecursionlimit(10000)
R=Path(__file__).resolve().parent;BASE=Path('/tmp/nucleus-receiver-trials/goal/signature-diagnostic.ndjson');raw=BASE.read_bytes();assert hashlib.sha256(raw).hexdigest()=='1022e5dc308231b91a2d8833a26006d1d082339785d61a09fc7427b30d8c0bdf'
records=[json.loads(x)for x in raw.splitlines()];expr={r['ie']:{k:v for k,v in r.items()if k!='ie'}for r in records if 'ie'in r};levels={r['il']:{k:v for k,v in r.items()if k!='il'}for r in records if 'il'in r};levels[0]={'zero':True};maxname=max(r.get('in',0)for r in records)
parent=[x for x,r in zip(raw.splitlines(True),records)if not('thm'in r and r['thm']['name']==26089)];assert len(parent)==len(records)-1
class Decline(Exception):pass
class Reifier:
 def __init__(self,snapshot):
  self.s=snapshot;self.frames={f['id']:f['bindings']for f in snapshot['frames']};self.add=[];self.next_expr=max(expr)+1;self.next_level=max(levels)+1;self.next_name=maxname+1;self.expr_intern={};self.level_intern={};self.params={};self.memo={};self.active=set();self.work=500000
 def tick(self):
  self.work-=1
  if self.work<0:raise Decline('reification-work-cap')
 def name(self,text):
  i=self.next_name;self.next_name+=1;self.add.append({'in':i,'str':{'pre':0,'str':text}});return i
 def e(self,node):
  k=json.dumps(node,sort_keys=True,separators=(',',':'))
  if k not in self.expr_intern:
   i=self.next_expr;self.next_expr+=1;self.expr_intern[k]=i;self.add.append({'ie':i,**node})
  return self.expr_intern[k]
 def l(self,node):
  if 'zero'in node:return 0
  k=json.dumps(node,sort_keys=True,separators=(',',':'))
  if k not in self.level_intern:
   i=self.next_level;self.next_level+=1;self.level_intern[k]=i;self.add.append({'il':i,**node})
  return self.level_intern[k]
 def actual_level(self,v):
  self.tick();tag=v[0]
  if tag=='zero':return 0
  if tag=='param':
   if v[1]not in self.params:self.params[v[1]]=self.name('NucleusSnapshotUniverse'+str(len(self.params)))
   return self.l({'param':self.params[v[1]]})
  if tag=='succ':return self.l({'succ':self.actual_level(v[1])})
  if tag in('max','imax'):return self.l({tag:[self.actual_level(v[1]),self.actual_level(v[2])]})
  raise Decline(('actual-level',v))
 def source_level(self,i,subst,active=()):
  self.tick()
  if i in active:raise Decline('source-level-cycle')
  r=levels[i];tag=next(iter(r));v=r[tag]
  if tag=='zero':return 0
  if tag=='param':
   if v not in subst:raise Decline(('missing-universe-substitution',i,v))
   return self.actual_level(subst[v])
  if tag=='succ':return self.l({'succ':self.source_level(v,subst,active+(i,))})
  if tag in('max','imax'):return self.l({tag:[self.source_level(c,subst,active+(i,))for c in v]})
  raise Decline(('source-level',r))
 def free(self,f,n,out,free_levels):
  if f not in free_levels:raise Decline(('escaped-free',f,n,out))
  index=n+out-1-free_levels[f]
  if index<0:raise Decline(('future-free',f,n,out))
  return self.e({'bvar':index})
 def closure(self,c,n,out,free_levels):return self.go(c['expr'],c['env'],tuple((a,json.dumps(b,separators=(',',':')))for a,b in c['levels']),0,n,out,tuple(sorted(free_levels.items())))
 def neutral(self,v,n,out,free_levels):
  h=v['head'];k=h['kind']
  if k=='free':head=self.free(h['id'],n,out,free_levels)
  elif k=='const':head=self.e({'const':{'name':h['name'],'us':[self.actual_level(x)for x in h['levels']]}})
  elif k=='proj':head=self.e({'proj':{'typeName':h['owner'],'idx':h['index'],'struct':self.neutral(h['receiver'],n,out,free_levels)}})
  else:raise Decline(('neutral-head',h))
  for c in v['spine']:head=self.e({'app':{'fn':head,'arg':self.closure(c,n,out,free_levels)}})
  return head
 def binding(self,b,n,out,free_levels):
  self.tick();k=b['kind']
  if k=='free':return self.free(b['id'],n,out,free_levels)
  if k=='closure':return self.closure(b['closure'],n,out,free_levels)
  if k=='neutral':return self.neutral(b['neutral'],n,out,free_levels)
  if k=='nat':return self.e({'natVal':str(sum(v*b['base']**i for i,v in enumerate(b['limbs'])))})
  raise Decline(('binding',b))
 def ty(self,t,n,out=0,free_levels=None):
  self.tick();free_levels=dict(enumerate(range(n)))if free_levels is None else free_levels;k=t['kind']
  if k=='term':return self.closure(t['closure'],n,out,free_levels)
  if k=='sort':return self.e({'sort':self.actual_level(t['level'])})
  if k=='pi':
   domain=self.ty(t['domain'],n,out,free_levels);extended=dict(free_levels);extended[t['binder']]=n+out;body=self.ty(t['body'],n,out+1,extended);return self.e({'forallE':{'name':0,'binderInfo':'default','type':domain,'body':body}})
  raise Decline(('typevalue',t))
 def go(self,i,env,substkey,intr,n,out,freekey):
  self.tick();key=(i,env,substkey,intr,n,out,freekey)
  if out>512:raise Decline('binder-depth-cap')
  if key in self.memo:return self.memo[key]
  if key in self.active:raise Decline('captured-source-cycle')
  self.active.add(key);r=expr[i];tag=next(iter(r));v=r[tag];subst={a:json.loads(b)for a,b in substkey};free_levels=dict(freekey)
  def child(j,binder=False):return self.go(j,env,substkey,intr+int(binder),n,out+int(binder),freekey)
  if tag=='bvar':
   if v<intr:result=self.e({'bvar':v})
   else:
    frame=self.frames.get(env)
    if frame is None or v-intr>=len(frame):raise Decline(('missing-frame-binding',env,v,intr))
    result=self.binding(frame[v-intr],n,out,free_levels)
  elif tag=='sort':result=self.e({'sort':self.source_level(v,subst)})
  elif tag=='const':result=self.e({'const':{'name':v['name'],'us':[self.source_level(x,subst)for x in v['us']]}})
  elif tag=='app':result=self.e({'app':{'fn':child(v['fn']),'arg':child(v['arg'])}})
  elif tag in('lam','forallE'):result=self.e({tag:{**v,'type':child(v['type']),'body':child(v['body'],True)}})
  elif tag=='letE':result=self.e({tag:{**v,'type':child(v['type']),'value':child(v['value']),'body':child(v['body'],True)}})
  elif tag=='proj':result=self.e({'proj':{**v,'struct':child(v['struct'])}})
  elif tag in('natVal','strVal'):result=self.e({tag:v})
  else:raise Decline(('expression',i,tag))
  self.active.remove(key);self.memo[key]=result;return result
 def build(self):
  name=self.name('NucleusReceiverSnapshot'+str(self.s['metadata']['slot']));n=len(self.s['context']);left=self.ty(self.s['left'],n);right=self.ty(self.s['right'],n);right_body=self.ty(self.s['right'],n,1)
  typ=self.e({'forallE':{'name':0,'binderInfo':'default','type':right,'body':right_body}});val=self.e({'lam':{'name':0,'binderInfo':'default','type':left,'body':self.e({'bvar':0})}})
  domains={}
  for i in reversed(range(n)):
   domain=self.ty(self.s['context'][i],i);domains[i]=domain;typ=self.e({'forallE':{'name':0,'binderInfo':'default','type':domain,'body':typ}});val=self.e({'lam':{'name':0,'binderInfo':'default','type':domain,'body':val}})
  self.summary=dict(left_type=left,right_type=right,domains=domains,context_len=n,universe_params=list(self.params.values()))
  self.add.append({'thm':{'name':name,'levelParams':list(self.params.values()),'type':typ,'value':val,'all':[name]}});return b''.join(parent)+b''.join((json.dumps(x,separators=(',',':'),ensure_ascii=False)+'\n').encode()for x in self.add)
results=[]
for p in sorted((R/'snapshots').glob('pair-*.json')):
 D=R/'reified'/p.stem;D.mkdir(parents=True,exist_ok=True);s=json.loads(p.read_text())
 try:
  reifier=Reifier(s);data=reifier.build();(D/'goal.ndjson').write_bytes(data)
  row=dict(status='REIFIED_NOT_YET_VERIFIED',snapshot_sha256=hashlib.sha256(p.read_bytes()).hexdigest(),input_sha256=hashlib.sha256(data).hexdigest(),input_bytes=len(data),context_len=len(s['context']),added_records=len(reifier.add),work_spent=500000-reifier.work,metadata=s['metadata'],reified_roots=reifier.summary,signature_environment_only=True,no_full_mathlib_or_rank_claim=True)
 except Exception as e:row=dict(status='DECLINED_REIFICATION',error=repr(e),metadata=s.get('metadata'),no_promotion=True)
 (D/'reification.json').write_text(json.dumps(row,indent=2));results.append(row);print(json.dumps(row),flush=True)
(R/'reification-report.json').write_text(json.dumps(results,indent=2))
