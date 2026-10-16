import pathlib,json,hashlib,re,ast,types,base64
B=pathlib.Path('/workspace/qualification/native-authority-v41-screening-audit/metadata-preaudit');S=B/'source-binding';R=B.parent/'committed-source/research/unified_consequence_runtime';P=json.loads((B/'committed/PREQUERY.json').read_text());checks=[]
def check(n,p,d=None):checks.append({'check':n,'pass':bool(p),'detail':d})
def h(raw):return hashlib.sha256(raw).hexdigest()
def expr(path,name,env):
 n=next(n for n in ast.parse(path.read_text()).body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id==name for t in n.targets));return eval(compile(ast.Expression(n.value),str(path),'eval'),dict({'__builtins__':{}},**env))
p='research/unified_consequence_runtime/'
hist=expr(S/p/'archaeology/native-frontier-v2/curate_metadata.py','HISTORICAL_METADATA',{})
hist=tuple('archaeology/native-authority-v4/HISTORICAL_REPOSITORIES.json' if n=='archaeology/programme-closure/REPOSITORIES.json' else n for n in hist)
e3=expr(S/p/'archaeology/native-environment-v3/curate_frontier.py','EXTRA_HISTORY',{})
e4=expr(S/p/'archaeology/native-authority-v4/curate_frontier.py','EXTRA_HISTORY',{'_original':types.SimpleNamespace(EXTRA_HISTORY=e3)})
e41=expr(B/'committed/curate_frontier.py','EXTRA_HISTORY',{'_carrier':types.SimpleNamespace(EXTRA_HISTORY=e4)})
paths=(*hist,*e41);check('exact_original_plus_versioned_history_inventory',[x['path'] for x in P['historical_metadata_inputs']]==list(paths),{'count':len(paths)})
def strings(v,k=''):
 if isinstance(v,dict):
  for key,val in v.items():yield from strings(val,key)
 elif isinstance(v,list):
  for val in v:yield from strings(val,k)
 elif isinstance(v,str):yield k,v
evidence={};rows=[]
for row in P['historical_metadata_inputs']:
 path=R/row['path']
 if not path.exists():check('missing_record:'+row['path'],row=={'path':row['path'],'status':'MISSING'});rows.append(row);continue
 check('historical_bytes:'+row['path'],h(path.read_bytes())==row['sha256'])
 repos=set()
 for key,value in strings(json.loads(path.read_text())):
  repos.update(match.removesuffix('.git') for match in re.findall(r'(?:https?://)?(?:www\.)?github\.com/([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)',value))
  if ('repo' in key.lower() or key.lower() in {'repository_order','repositories'}) and re.fullmatch(r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+',value):repos.add(value.removesuffix('.git'))
 check('historical_repo_extract:'+row['path'],sorted(repos)==row['repositories'])
 for repo in repos:evidence.setdefault(repo.lower(),[]).append(row['path'])
 rows.append({'path':row['path'],'sha256':row['sha256'],'repositories':sorted(repos)})
evidence.setdefault('go-chi/chi',[]).append('capability_index.json#jpl-observation-quotient-native-chi-servemux')
check('exact_exclusion_evidence',dict(sorted(evidence.items()))==P['historically_touched_repository_exclusions'])
check('all_nine_declared_repositories_disjoint',set(P['repository_universe_fixed_before_github_queries']).isdisjoint(evidence))
prepaths=base64.b64decode(json.loads((B/'git-tree-prequery.json').read_text())['stdout_base64']).decode().splitlines();prefix=p+'archaeology/native-authority-v41/'
check('prequery_commit_without_query_or_screening_records',all(prefix+n not in prepaths for n in ['PREQUERY_EXECUTION.json','METADATA_CURATION.json','FROZEN_POOL.json','SCREENING_AUTHORITY.json','FRONTIER_PROTOCOL.json','SCREENING_ENVELOPES.json','SCREENING_METER.json']))
out={'schema':'UDM_V41_BOUNDED_HISTORICAL_EXCLUSION_AUDIT','status':'PASS' if all(x['pass'] for x in checks) else 'UNKNOWN','check_count':len(checks),'checks':checks,'failures':[x for x in checks if not x['pass']],'history_input_count':len(rows),'reconstructed_exclusion_count':len(evidence),'limitations':['This reconstructs the original bounded accessible metadata scan, not all prior human/model exposure or unlogged external access.','Missing input records remain explicit; source pinning and local ancestry do not independently timestamp network access.']};(B/'HISTORY_EXCLUSION_AUDIT.json').write_text(json.dumps(out,indent=2)+'\n');print({k:v for k,v in out.items() if k not in ['checks','limitations']})
