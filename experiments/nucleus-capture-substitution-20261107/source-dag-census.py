import json,collections,pathlib,hashlib
p=pathlib.Path('recovered/original196/good/perf/fueled-chain.ndjson');e={}
for line in p.open():
 r=json.loads(line)
 if'ie'in r:e[r['ie']]={k:v for k,v in r.items()if k!='ie'}
tags=collections.Counter(next(iter(x))for x in e.values());assert set(tags)<={'bvar','sort','const','app','lam','forallE','letE','proj','natVal','strVal'},tags
def children(r):
 k=next(iter(r));v=r[k]
 if k=='app':return[(v['fn'],False),(v['arg'],False)]
 if k in ('lam','forallE'):return[(v['type'],False),(v['body'],True)]
 if k=='letE':return[(v['type'],False),(v['value'],False),(v['body'],True)]
 if k=='proj':return[(v['struct'],False)]
 return[]
support={};size={}
for i in sorted(e):
 r=e[i];k=next(iter(r));v=r[k];s=set([v])if k=='bvar'else set();n=1
 for c,b in children(r):
  n+=size[c];s|={j-1 for j in support[c]if j>0}if b else support[c]
 support[i]=s;size[i]=n
rows=[]
for name,root in [('chain6',7199),('chain9',10707),('chain12',16167)]:
 use=collections.Counter({root:1});seen=set();pending=[root]
 while pending:
  i=pending.pop()
  if i in seen:continue
  seen.add(i);pending.extend(c for c,_ in children(e[i]))
 for i in sorted(seen,reverse=True):
  for c,_ in children(e[i]):use[c]+=use[i]
 closed=[{'expr':i,'syntactic_occurrences':use[i],'expanded_nodes':size[i],'tag':next(iter(e[i]))}for i in seen if not support[i]and next(iter(e[i]))in('lam','forallE','letE')]
 closed.sort(key=lambda x:x['syntactic_occurrences']*x['expanded_nodes'],reverse=True)
 row={'name':name,'unique_nodes':len(seen),'expanded_source_nodes':size[root],'closed_non_spine_candidates':closed[:12]};rows.append(row);print(json.dumps(row))
pathlib.Path('recovered/source-dag-census.json').write_text(json.dumps({'input_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'diagnostic_only':True,'scope':'literal source AST sharing; constants not unfolded; no claim of type equality or dynamic execution count','source_tags':tags,'rows':rows},indent=2))
