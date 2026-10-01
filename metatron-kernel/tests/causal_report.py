from contract_paths import Contract,plan
REGISTRY=[
 Contract('sum-telescope-derivation@candidate',{'observed.nonrecursive-sum','observed.route-miss'},{'admitted'},False),
 # Current qualified code contracts: premises are deliberately stronger than shape.
 Contract('iff-singleton@0659',{'validated.iff-function-fields','validated.singleton-recursor'},{'admitted'},True),
 Contract('closed-record3@0659',{'validated.closed-three-data-fields','validated.record-recursor'},{'admitted'},True),
 Contract('proof-type-conversion@13d5',{'validated.both-prop','validated.bounded-type-conversion'},{'conversion'},True),
]
def classify(block,events):
 if any(e.get('truncated') for e in events):
  return {'status':'UNRESOLVED_INCOMPLETE_TRACE','contracts':[],'candidates':[]}
 seeds=set()
 ts=block.get('types',[])
 if len(ts)==1 and len(block.get('ctors',[]))>1:
  t=ts[0]
  if all(t.get(k)==0 for k in ('numIndices','numNested')) and all(t.get(k) is False for k in ('isRec','isReflexive','isUnsafe')):
   seeds.add('observed.nonrecursive-sum')
 if any(e.get('kind')=='admission-route-miss' for e in events):
  seeds.add('observed.route-miss')
 result=plan(REGISTRY,seeds,'admitted' if block else 'conversion')
 result['seeds']=sorted(seeds)
 return result


def report(root,frontier):
 import hashlib,json,pathlib,re
 rows=[]
 for row in frontier:
  source=pathlib.Path(root)/('good' if row['expected']==0 else 'bad')/(row['test']+'.ndjson')
  digest=hashlib.sha256(source.read_bytes()).hexdigest()
  downstream=[s for s in row['trace'].splitlines() if s.startswith('NUCLEUS_DOWNSTREAM:')]
  assert downstream, row['test']
  terminal=downstream[-1]
  name=terminal.split('name=',1)[1].split(':stage=',1)[0]
  names={0:''};block={};declaration=None
  for line in source.open():
   r=json.loads(line)
   if 'in' in r:
    v=r.get('str',r.get('num'));names[r['in']]=names[v['pre']]+('.' if v['pre'] else '')+str(v.get('str',v.get('i')))
   if 'inductive' in r and any(names.get(t['name'])==name for t in r['inductive']['types']):
    block=r['inductive'];declaration=r;break
   if any(k in r and names.get(r[k].get('name'))==name for k in ('def','thm','axiom','opaque')):
    declaration=r;break
  events=[json.loads(s.split(':',1)[1]) for s in row['trace'].splitlines() if s.startswith('NUCLEUS_CAUSAL:')]
  boundaries=[e for e in events if e['kind']=='boundary']
  if boundaries:
   scope=boundaries[-1]['scope'];events=[e for e in events if e['scope']==scope]
   outcome=classify(block,events)
  else:
   outcome={'status':'UNRESOLVED_MISSING_BOUNDARY','contracts':[],'candidates':[]}
  rows.append(dict(test=row['test'],expected=row['expected'],verdict=row['candidate'],object_id=digest+':'+name,input_sha256=digest,terminal=terminal,declaration=declaration,events=events,plan=outcome,
   causal_limit='Failed comparisons in the terminal declaration are observed, not a proven minimal causal chain. No observed shape is a validated premise.'))
 from collections import Counter
 return {'schema':'nucleus-causal-contracts-v1','base_sha':'0659bc671a4ef536ed4a096deacd0c61b1ca927e',
  'boundary':'Diagnostic paths only; no semantic authority or full-file gains',
  'counts':dict(Counter(r['plan']['status'] for r in rows)),
  'candidate_paths':dict(Counter(r['plan'].get('path_id') for r in rows if r['plan']['status']=='CANDIDATE_PATH')),'rows':rows}

if __name__=='__main__':
 import json,pathlib,sys
 result=report(sys.argv[1],json.loads(pathlib.Path(sys.argv[2]).read_text()))
 pathlib.Path(sys.argv[3]).write_text(json.dumps(result,indent=2)+'\n')
 print(json.dumps({k:v for k,v in result.items() if k!='rows'}))
 assert len(result['rows'])==24
