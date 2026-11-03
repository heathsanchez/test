import copy,json,pathlib
from generate import generate
out=pathlib.Path(__file__).parent/'controls';out.mkdir(exist_ok=True)
def save(label,rows):
 (out/(label+'.ndjson')).write_text(''.join(json.dumps(r,separators=(',',':'))+'\n' for r in rows))
def nodes(rows):return {r['ie']:r for r in rows if 'ie'in r}
def telescope(ns,root,tag,n):
 a=[]
 for _ in range(n):a.append(ns[root][tag]);root=ns[root][tag]['body']
 return a
base=generate(3,3,True)
for label,change in [('field-too-large',lambda r,n,b,c,a:c[3].update(type=next(x['ie']for x in r if x.get('sort')==2))),('ctor-parameter-domain',lambda r,n,b,c,a:c[1].update(type=c[0]['type'])),('rhs-parameter-annotation',lambda r,n,b,c,a:a[1].update(type=c[0]['type'])),('rhs-motive-annotation',lambda r,n,b,c,a:a[3].update(type=c[0]['type'])),('rhs-minor-annotation',lambda r,n,b,c,a:a[4].update(type=c[0]['type'])),('rhs-field-shift',lambda r,n,b,c,a:a[6].update(type=c[4]['type'])),('wrong-parameter-count',lambda r,n,b,c,a:b['ctors'][0].update(numParams=2)),('colliding-motive-universe',lambda r,n,b,c,a:b['recs'][0].update(levelParams=[b['types'][0]['levelParams'][0]]*2))]:
 rows=copy.deepcopy(base);ns=nodes(rows);b=rows[-1]['inductive'];c=telescope(ns,b['ctors'][0]['type'],'forallE',6);a=telescope(ns,b['recs'][0]['rules'][0]['rhs'],'lam',8);change(rows,ns,b,c,a);save(label,rows)
# Exact source self-reference hidden in a field's function domain.
rows=copy.deepcopy(base);ns=nodes(rows);b=rows[-1]['inductive'];c=telescope(ns,b['ctors'][0]['type'],'forallE',6)
root=max(ns)+1;const=root;rows.insert(-1,{'ie':const,'const':{'name':b['types'][0]['name'],'us':[1]}})
# Supply the complete three-parameter application in its constructor context.
for index in [2,1,0]:
 bv=root+1;root+=2;rows.insert(-1,{'ie':bv,'bvar':index});rows.insert(-1,{'ie':root,'app':{'fn':const,'arg':bv}});const=root
root+=1;rows.insert(-1,{'ie':root,'forallE':{'name':1,'binderInfo':'default','type':const,'body':c[3]['type']}});c[3]['type']=root;save('recursive-function-domain',rows)
# Exercise the overlapping legacy four-parameter/three-field selector before
# its recursive walkers can run. Expanded work is counted without DAG memoing.
for label,depth,dag in [('excessive-depth',600,False),('expanded-dag',20,True)]:
 rows=generate(4,3,False);ns=nodes(rows);b=rows[-1]['inductive'];c=telescope(ns,b['ctors'][0]['type'],'forallE',7);node=c[4]['type'];next_id=max(ns)+1
 for i in range(depth):
  if dag:new={'ie':next_id,'app':{'fn':node,'arg':node}}
  else:new={'ie':next_id,'forallE':{'name':1,'binderInfo':'default','type':node,'body':node}}
  rows.insert(-1,new);node=next_id;next_id+=1
 c[4]['type']=node;save(label,rows)
