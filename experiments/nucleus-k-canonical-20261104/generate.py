import argparse,json,copy,hashlib
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--record',action='store_true');p.add_argument('--max1',action='store_true');p.add_argument('--closed',action='store_true');p.add_argument('--source',required=True);p.add_argument('--out',required=True);a=p.parse_args();data=Path(a.source).read_bytes();assert hashlib.sha256(data).hexdigest()==('e7daddaf05fa799dc248bb3f10a502fd5ab5569561a4502d9f48de63256f3113'if a.max1 else 'e08afe0a4ce9c0cd64308ee6eef52d0952316784d72175c843846762e2eb4d0b'if a.record else '282a7cf85e897f1e246fc25bc0cf6a6b69afdce72856f2fb500299504b8488ef');rows=[json.loads(l)for l in data.splitlines()];
if a.closed:
 index=next(i for i,r in enumerate(rows)if 'inductive'in r and r['inductive']['types'][0]['name']==435)
 rows=rows[:index+1];data=b''.join(data.splitlines(keepends=True)[:index+1])
original=rows[-1]['inductive'];assert original['types'][0]['name']==(12926 if a.max1 else 12862 if a.record else 435 if a.closed else 12829)
N={r['in']:r for r in rows if'in'in r};L={r['il']:r for r in rows if'il'in r};E={r['ie']:r for r in rows if'ie'in r};out=Path(a.out);out.mkdir(parents=True,exist_ok=True);manifest=[]
def fullname(n):
 if n==0:return ''
 r=N[n];v=r.get('str',r.get('num'));return (fullname(v['pre'])+'.'+str(v.get('str',v.get('num')))).strip('.')
print('ORIGINAL',[(i,fullname(i))for i in original['recs'][0]['levelParams']])
cases=[('closed-original',None,None),('closed-fresh-w',None,'w')]if a.closed else [('original',None,None),('fresh-w',None,'w'),('fresh-u3',None,'u_3'),('hierarchical',None,'probe.u'),('owner-wx',['w','x'],'u'),('owner-u-v',['u','v'],'u_1')]
if a.record or a.max1:cases=[('original',None,None),('fresh-w',None,'w'),('fresh-u3',None,'u_3'),('hierarchical',None,'probe.u'),('owner-v',['v'],'u')]
for label,owners,motive in cases:
 extra=[];names={fullname(i):i for i in N};ni=[max(N)+1];li=[max(L)+1];ei=[max(E)+1]
 def name(s):
  if s in names:return names[s]
  parent,_,leaf=s.rpartition('.');pre=name(parent)if parent else 0;n=ni[0];ni[0]+=1;names[s]=n;extra.append({'in':n,'str':{'pre':pre,'str':leaf}});return n
 b=copy.deepcopy(original);oldowners=b['types'][0]['levelParams'];oldm=b['recs'][0]['levelParams'][0];mapping={}
 if owners:
  newowners=[name(x)for x in owners];mapping.update(zip(oldowners,newowners))
  b['types'][0]['levelParams']=newowners;b['ctors'][0]['levelParams']=newowners
 else:newowners=oldowners
 if motive:mapping[oldm]=name(motive)
 b['recs'][0]['levelParams']=[mapping.get(oldm,oldm),*newowners];lc={};ec={}
 def level(i):
  if i==0:return 0
  if i in lc:return lc[i]
  before=L[i];r=copy.deepcopy(before)
  if 'param'in r:r['param']=mapping.get(r['param'],r['param'])
  for k in ['succ']:
   if k in r:r[k]=level(r[k])
  for k in ['max','imax']:
   if k in r:r[k]=[level(x)for x in r[k]]
  if r==before:lc[i]=i;return i
  n=li[0];li[0]+=1;r['il']=n;extra.append(r);lc[i]=n;return n
 def expr(i):
  if i in ec:return ec[i]
  before=E[i];r=copy.deepcopy(before)
  if 'sort'in r:r['sort']=level(r['sort'])
  if 'const'in r:r['const']['us']=[level(x)for x in r['const']['us']]
  if 'app'in r:
   for k in ['fn','arg']:r['app'][k]=expr(r['app'][k])
  for tag in ['lam','forallE','letE']:
   if tag in r:
    for k in ['type','body']+(['value']if tag=='letE'else[]):r[tag][k]=expr(r[tag][k])
  if'proj'in r:r['proj']['struct']=expr(r['proj']['struct'])
  if r==before:ec[i]=i;return i
  n=ei[0];ei[0]+=1;r['ie']=n;extra.append(r);ec[i]=n;return n
 for t in b['types']+b['ctors']+b['recs']:t['type']=expr(t['type'])
 for rec in b['recs']:
  for rule in rec['rules']:rule['rhs']=expr(rule['rhs'])
 result=b''.join(data.splitlines(keepends=True)[:-1])+b''.join((json.dumps(x,separators=(',',':'))+'\n').encode()for x in extra+[{'inductive':b}]);target=out/(label+'.ndjson');target.write_bytes(result);manifest.append(dict(case=label,file=target.name,sha256=hashlib.sha256(result).hexdigest(),expect_reference=0 if label in ['original','closed-original','owner-v','owner-wx','owner-u-v']else 1))
for label,change in ([] if a.closed else [
 ('forged-k-on'if a.record or a.max1 else 'forged-k-off',lambda b:b['recs'][0].__setitem__('k',a.record or a.max1)),
 ('forged-extra-field',lambda b:b['ctors'][0].__setitem__('numFields',1)),
 ('forged-recursor-level',lambda b:b['recs'][0]['levelParams'].__setitem__(1,326)),
 ('forged-rule-count',lambda b:b['recs'][0]['rules'][0].__setitem__('nfields',1))]):
 b=copy.deepcopy(original);change(b)
 result=b''.join(data.splitlines(keepends=True)[:-1])+(json.dumps({'inductive':b},separators=(',',':'))+'\n').encode()
 target=out/(label+'.ndjson');target.write_bytes(result)
 manifest.append(dict(case=label,file=target.name,sha256=hashlib.sha256(result).hexdigest(),expect_reference=1))
(out/'inputs.json').write_text(json.dumps(manifest,indent=2)+'\n')
