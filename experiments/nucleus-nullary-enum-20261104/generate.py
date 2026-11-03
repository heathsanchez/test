import copy,hashlib,json,pathlib
ROOT=pathlib.Path(__file__).resolve().parent
# Repository-owned minimal, exact checked Nat declaration for literal branches.
SEED=ROOT.parents[1]/'metatron-kernel/tests/fixtures/good-parameter-record.ndjson'
if not SEED.exists():SEED=ROOT.parent/'base-source/metatron-kernel/tests/fixtures/good-parameter-record.ndjson'
def generate(count):
 rows=[]
 for line in SEED.read_text().splitlines():
  r=json.loads(line);rows.append(r)
  if 'inductive'in r:break
 names={};words={0:''}
 for r in rows:
  if'in'in r:
   n=r.get('str')or r.get('num');word=words[n['pre']]+('.'if n['pre'] else'')+str(n.get('str',n.get('i')));words[r['in']]=word;names[word]=r['in']
 def name(word):
  if word not in names:
   pre,_,leaf=word.rpartition('.');parent=name(pre)if pre else 0;names[word]=max(words)+1;words[names[word]]=word;rows.append({'in':names[word],'str':{'pre':parent,'str':leaf}})
  return names[word]
 R=name('ReusableEnum');ctors=[name('ReusableEnum.tag'+str(i))for i in range(count)];rec=name('ReusableEnum.rec');u=name('u')
 ul=max(r['il']for r in rows if'il'in r)+1;rows.append({'il':ul,'param':u});next_expr=max(r['ie']for r in rows if'ie'in r)+1;memo={}
 def emit(obj):
  nonlocal next_expr
  key=json.dumps(obj,sort_keys=True)
  if key not in memo:memo[key]=next_expr;rows.append({'ie':next_expr,**obj});next_expr+=1
  return memo[key]
 def sort(l):return('sort',l)
 def var(n):return('var',n)
 def const(n,levels=()):return('const',n,list(levels))
 def app(fn,*args):
  for a in args:fn=('app',fn,a)
  return fn
 def bind(tag,ps,body):
  for n,ty in reversed(ps):body=(tag,n,ty,body)
  return body
 def compile(t,ctx=()):
  if t[0]=='sort':return emit({'sort':t[1]})
  if t[0]=='var':return emit({'bvar':ctx[::-1].index(t[1])})
  if t[0]=='const':return emit({'const':{'name':t[1],'us':t[2]}})
  if t[0]=='nat':return emit({'natVal':str(t[1])})
  if t[0]=='app':return emit({'app':{'fn':compile(t[1],ctx),'arg':compile(t[2],ctx)}})
  tag,n,ty,body=t;return emit({tag:{'name':name(n),'binderInfo':'default','type':compile(ty,ctx),'body':compile(body,ctx+(n,))}})
 carrier=const(R);ity=compile(sort(1));cty=compile(carrier)
 motive=('motive',bind('forallE',[('x',carrier)],sort(ul)))
 minors=[('case'+str(i),app(var('motive'),const(c)))for i,c in enumerate(ctors)]
 rty=compile(bind('forallE',[motive]+minors+[('major',carrier)],app(var('motive'),var('major'))))
 rhs=[compile(bind('lam',[motive]+minors,var(minors[i][0])))for i in range(count)]
 rows.append({'inductive':{'types':[{'name':R,'levelParams':[],'type':ity,'numParams':0,'numIndices':0,'numNested':0,'isRec':False,'isReflexive':False,'isUnsafe':False,'all':[R],'ctors':ctors}],'ctors':[{'name':c,'levelParams':[],'type':cty,'numParams':0,'numFields':0,'cidx':i,'induct':R,'isUnsafe':False}for i,c in enumerate(ctors)],'recs':[{'name':rec,'levelParams':[u],'type':rty,'numParams':0,'numIndices':0,'numMotives':1,'numMinors':count,'k':False,'isUnsafe':False,'all':[R],'rules':[{'ctor':c,'nfields':0,'rhs':rhs[i]}for i,c in enumerate(ctors)]}]}})
 if count==3:
  natural=const(names['Nat']);m=bind('lam',[('q',carrier)],natural)
  for i,c in enumerate(ctors):
   value=compile(app(const(rec,[1]),m,('nat',11),('nat',23),('nat',47),const(c)));ty=compile(natural);n=name('enumProbe'+str(i));rows.append({'def':{'name':n,'levelParams':[],'type':ty,'value':value,'all':[n],'hints':'abbrev','safety':'safe'}})
 return rows

def write(path,rows):path.write_text(''.join(json.dumps(r,separators=(',',':'))+'\n'for r in rows))
if __name__=='__main__':
 out=ROOT/'fixtures';out.mkdir(exist_ok=True)
 for count in [3,16,17]:write(out/('enum'+str(count)+'.ndjson'),generate(count))
 rows=generate(3);b=next(r['inductive']for r in rows if'inductive'in r and len(r['inductive']['ctors'])==3);ns={r['ie']:r for r in rows if'ie'in r}
 for label,change in [('wrong-branch',lambda b,n:None),('wrong-index',lambda b,n:b['ctors'][1].update(cidx=0)),('wrong-constructor-result',lambda b,n:b['ctors'][0].update(type=b['types'][0]['type'])),('wrong-field-count',lambda b,n:b['ctors'][0].update(numFields=1)),('wrong-k',lambda b,n:b['recs'][0].update(k=True))]:
  r=copy.deepcopy(rows);block=next(x['inductive']for x in r if'inductive'in x and len(x['inductive']['ctors'])==3);nodes={x['ie']:x for x in r if'ie'in x};change(block,nodes)
  if label=='wrong-branch':
   root=block['recs'][0]['rules'][0]['rhs']
   for _ in range(3):root=nodes[root]['lam']['body']
   # Final lambda returns case1 rather than case0; all annotations unchanged.
   nodes[root]['lam']['body']=next(x['ie']for x in r if x.get('bvar')==1)
  write(out/(label+'.ndjson'),r)
 for label,attribute in [('motive-v','v'),('motive-hierarchical','x.u')]:
  r=copy.deepcopy(rows);block=next(x['inductive']for x in r if'inductive'in x and len(x['inductive']['ctors'])==3);uid=block['recs'][0]['levelParams'][0]
  # This universe is shared with the Nat recursor, so give the enum its own
  # new structured name and substitute only enum-owned universe expressions.
  name_id=max(x['in']for x in r if'in'in x)+1
  if '.'in attribute:
   parent=name_id;name_id+=1;r.insert(1,{'in':parent,'str':{'pre':0,'str':'x'}});r.insert(2,{'in':name_id,'str':{'pre':parent,'str':'u'}})
  else:r.insert(1,{'in':name_id,'str':{'pre':0,'str':attribute}})
  block['recs'][0]['levelParams']=[name_id]
  enum_level=max(x['il']for x in r if'il'in x);next(x for x in r if x.get('il')==enum_level)['param']=name_id
  write(out/(label+'.ndjson'),r)
 # Change a rule annotation while retaining a complete, parseable expression DAG.
 r=copy.deepcopy(rows);block=next(x['inductive']for x in r if'inductive'in x and len(x['inductive']['ctors'])==3);nodes={x['ie']:x for x in r if'ie'in x};root=block['recs'][0]['rules'][0]['rhs'];nodes[root]['lam']['type']=block['types'][0]['type'];write(out/'wrong-rule-annotation.ndjson',r)
 print(json.dumps({p.name:hashlib.sha256(p.read_bytes()).hexdigest()for p in out.glob('*.ndjson')},indent=2))
if __name__=='__main__':
 for label,depth,dag in [('deep-rule-annotation',600,False),('dag-rule-annotation',20,True)]:
  r=generate(3);block=next(x['inductive']for x in r if'inductive'in x and len(x['inductive']['ctors'])==3);nodes={x['ie']:x for x in r if'ie'in x};original=nodes[block['recs'][0]['rules'][0]['rhs']]['lam']['type'];node=original;nid=max(nodes)+1
  for _ in range(depth):
   x={'ie':nid,'app':{'fn':node,'arg':node}}if dag else {'ie':nid,'forallE':{'name':1,'binderInfo':'default','type':block['ctors'][0]['type'],'body':node}}
   r.append(x);nodes[nid]=x;node=nid;nid+=1
  nodes[block['recs'][0]['rules'][0]['rhs']]['lam']['type']=node
  # Topological expression emission keeps parse errors separate from guards.
  seen=set();ordered=[]
  def visit(i):
   if i in seen:return
   seen.add(i);x=nodes[i]
   if'app'in x:children=[x['app']['fn'],x['app']['arg']]
   elif'lam'in x or'forallE'in x:
    b=x.get('lam',x.get('forallE'));children=[b['type'],b['body']]
   else:children=[]
   for child in children:visit(child)
   ordered.append(x)
  for i in nodes:visit(i)
  r=[x for x in r if'ie'not in x and'inductive'not in x and'def'not in x]+ordered+[x for x in r if'inductive'in x or'def'in x];write(out/(label+'.ndjson'),r)
