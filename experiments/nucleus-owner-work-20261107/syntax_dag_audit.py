import json,collections,hashlib,argparse
from pathlib import Path
ap=argparse.ArgumentParser();ap.add_argument('input',type=Path);ap.add_argument('--output',type=Path);args=ap.parse_args();p=args.input;data=p.read_bytes();assert hashlib.sha256(data).hexdigest()=='78dfd772d8a1e6b91484434718af521885fec1386c7a841b70a12e0a7c2f56a3';nodes={};decls=[]
for line in data.splitlines():
 r=json.loads(line)
 if 'ie'in r:nodes[r['ie']]=r
 if set(r)&{'def','thm'}:decls.append(r)
def children(r):
 k=next(x for x in r if x!='ie');d=r[k]
 if k in ['lam','forallE']:return[d['type'],d['body']]
 if k=='app':return[d.get('fn',d.get('fun')),d['arg']]
 if k=='letE':return[d['type'],d['value'],d['body']]
 if k=='proj':return[d.get('struct',d.get('structure'))]
 return[]
size={}
for n in sorted(nodes):
 cs=children(nodes[n]);assert all(c<n for c in cs),'this audit requires topologically ordered acyclic syntax'
 size[n]=1+sum(size[c]for c in cs)
rows=[]
for owner,root in [('chain6_datF',7199),('chain9_datF',10707)]:
 weights=collections.Counter({root:1})
 for n in sorted(nodes,reverse=True):
  if weights[n]:
   for c in children(nodes[n]):weights[c]+=weights[n]
 row={'owner':owner,'root':root,'unique_syntax_nodes':len(weights),'expanded_syntax_visits':size[root],'expanded_to_unique_ratio':size[root]/len(weights),'most_revisited':weights.most_common(12)};rows.append(row)
report={'input_sha256':hashlib.sha256(data).hexdigest(),'boundary':'Exact static syntax DAG only; constants are leaves. No captured-environment expansion, paired-comparator execution, typing, or runtime cost claim.','rows':rows};out=args.output or p.with_suffix('.syntax-dag.json');out.write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
