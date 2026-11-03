import json,pathlib
out=pathlib.Path(__file__).parent/'fixtures';out.mkdir(exist_ok=True)
def generate(p=2,f=2,dependent=False):
 rows=[{'meta':{'exporter':{'name':'lean4export','version':'3.1.0'},'format':{'version':'3.1.0'},'lean':{'version':'4.34.1','githash':'5045d0056413266e57c625dcd7c365b10e377c52'}}}]; names={}; exprs={}
 def name(s):
  if s not in names:
   pre,_,leaf=s.rpartition('.'); parent=name(pre) if pre else 0
   names[s]=len(names)+1;rows.append({'in':names[s],'str':{'pre':parent,'str':leaf}})
  return names[s]
 u=name('u');v=name('v');R=name('ReusableRecord');mk=name('ReusableRecord.mk');rec=name('ReusableRecord.rec')
 rows.extend([{'il':1,'param':u},{'il':2,'succ':1},{'il':3,'param':v}])
 def emit(obj):
  k=json.dumps(obj,sort_keys=True)
  if k not in exprs:
   exprs[k]=len(exprs);rows.append({'ie':exprs[k],**obj})
  return exprs[k]
 def sort(l):return ('sort',l)
 def var(n):return ('var',n)
 def const(n):return ('const',n)
 def app(fn,*args):
  for a in args:fn=('app',fn,a)
  return fn
 def bind(tag,ps,body):
  for n,t in reversed(ps):body=(tag,n,t,body)
  return body
 def compile(t,ctx=()):
  if t[0]=='sort':return emit({'sort':t[1]})
  if t[0]=='var':return emit({'bvar':ctx[::-1].index(t[1])})
  if t[0]=='const':return emit({'const':{'name':t[1],'us':[1]}})
  if t[0]=='app':return emit({'app':{'fn':compile(t[1],ctx),'arg':compile(t[2],ctx)}})
  tag,n,ty,body=t;return emit({tag:{'name':name(n),'binderInfo':'default','type':compile(ty,ctx),'body':compile(body,ctx+(n,))}})
 params=[('P'+str(i),sort(2)) for i in range(p)]
 if dependent:params[1]=('P1',bind('forallE',[('x',var('P0'))],sort(2)))
 fields=[('f'+str(i),app(var('P1'),var('f0')) if dependent and i==1 else var('P'+str(i%p))) for i in range(f)]
 applied=app(const(R),*[var(n) for n,_ in params]);constructed=app(const(mk),*[var(n) for n,_ in params+fields])
 motive=('motive',bind('forallE',[('major0',applied)],sort(3)))
 minor=('minor',bind('forallE',fields,app(var('motive'),constructed)))
 ity=compile(bind('forallE',params,sort(2)))
 cty=compile(bind('forallE',params+fields,applied))
 rty=compile(bind('forallE',params+[motive,minor,('major',applied)],app(var('motive'),var('major'))))
 rhs=compile(bind('lam',params+[motive,minor]+fields,app(var('minor'),*[var(n) for n,_ in fields])))
 rows.append({'inductive':{'types':[{'name':R,'levelParams':[u],'type':ity,'numParams':p,'numIndices':0,'numNested':0,'isRec':False,'isReflexive':False,'isUnsafe':False,'all':[R],'ctors':[mk]}],'ctors':[{'name':mk,'levelParams':[u],'type':cty,'numParams':p,'numFields':f,'cidx':0,'induct':R,'isUnsafe':False}],'recs':[{'name':rec,'levelParams':[v,u],'type':rty,'numParams':p,'numIndices':0,'numMotives':1,'numMinors':1,'k':False,'isUnsafe':False,'all':[R],'rules':[{'ctor':mk,'nfields':f,'rhs':rhs}]}]}})
 return rows
for label,p,f,d in [('two',2,3,False),('dependent',3,3,True),('boundary',64,64,False)]:
 (out/(label+'.ndjson')).write_text(''.join(json.dumps(x,separators=(',',':'))+'\n' for x in generate(p,f,d)))
