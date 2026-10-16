import ast,base64,hashlib,importlib.util,json,pathlib,types,os
B=pathlib.Path('/workspace/qualification/native-authority-v41-screening-audit/metadata-preaudit')
R=pathlib.Path('/workspace/udm-v54'); C=B/'committed'; S=B/'source-binding'
s=importlib.util.spec_from_file_location('audit',B/'audit_index_v4.py');audit=importlib.util.module_from_spec(s);s.loader.exec_module(audit)
def h(raw): return hashlib.sha256(raw).hexdigest()
def load(f):return json.loads(f.read_text())
checks=[]
def check(name,value,detail=None): checks.append({'check':name,'pass':bool(value),'detail':detail})
def read(commit,name,label):
 record=B/('git-gate-'+label+'.json');d=S/'gate-files'/commit/name
 if record.exists():
  r=load(record);assert d.read_bytes()==base64.b64decode(r['stdout_base64'])
 else:
  r=audit.audit_git_read(R,['show',commit+':'+name]);d.parent.mkdir(parents=True,exist_ok=True);d.write_bytes(base64.b64decode(r['stdout_base64']));record.write_text(json.dumps(r,indent=2)+'\n')
 check('git_read_'+label,r['returncode']==0 and r['indexes_unchanged']);return d.read_bytes()
def expr(path,name,env):
 tree=ast.parse(path.read_text());nodes=[n for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id==name for t in n.targets)];assert len(nodes)==1
 # Only source-pinned container construction expressions are evaluated; no imports/module execution.
 expression=ast.Expression(nodes[0].value); allowed=(ast.Expression,ast.Call,ast.Attribute,ast.Name,ast.Load,ast.Constant,ast.Tuple,ast.List,ast.BinOp,ast.Add,ast.GeneratorExp,ast.comprehension,ast.Store,ast.Starred)
 assert all(isinstance(n,allowed) for n in ast.walk(expression)),name
 return eval(compile(expression,str(path),'eval'),dict({'__builtins__':{},'tuple':tuple,'dict':dict},**env))
p='research/unified_consequence_runtime/'
q3=C/'qualify_native_frontier_v3.py';q4=C/'qualify_native_frontier_v4.py';q41=C/'qualify_native_frontier_v41.py';m4=S/(p+'qualify_environment_selection_v4.py');m41=S/(p+'qualify_environment_selection_v41.py')
m4gate=expr(m4,'SOURCE_GATE_FILES',{});evidence=expr(m41,'METADATA_EVIDENCE_FILES',{});m41gate=expr(m41,'SOURCE_GATE_FILES',{'previous':types.SimpleNamespace(SOURCE_GATE_FILES=m4gate),'METADATA_EVIDENCE_FILES':evidence})
q3gate=expr(q3,'ENVIRONMENT_GATE_FILES',{});q4gate=expr(q4,'ENVIRONMENT_GATE_FILES',{'_metadata_gate_files':m4gate,'_prior':types.SimpleNamespace(ENVIRONMENT_GATE_FILES=q3gate)});q41gate=expr(q41,'ENVIRONMENT_GATE_FILES',{'_metadata_gate_files':m41gate,'_carrier':types.SimpleNamespace(ENVIRONMENT_GATE_FILES=q4gate),'CATALOG_PATH':p+'archaeology/native-authority-v41/ENVIRONMENT_CATALOG.json'})
check('exact_qualified_source_gate_file_count',len(m41gate)==70,{'count':len(m41gate),'names':list(m41gate)});check('exact_prospective_environment_gate_file_count',len(q41gate)==83,{'count':len(q41gate),'names':list(q41gate)})
result_path=S/(p+'archaeology/native-authority-v41/CI_38954969411_RESULT.json');result=load(result_path);gate=load(C/'ENVIRONMENT_GATE.json');g=gate['environment_gate'];full='bd46699ea9933794a1c3fee161039c24a630bf4b';pre='a7d03cf43227fcdd40779e8a8aef8a2bb163f95d';qual='4c3f7e276567b4ea8df96c7a8797a889040dc0ac'
check('gate_identifiers_exact',g=={'artifact_id':12069448596,'artifact_sha256':'90dcaba5ecc47761890ad17a3761924863eb4b33ae4acf38f6aa1d870af455e0','qualification_result_sha256':'0ea3843c9b9d80c59a9102312813cf586216c1ce78d69dc9b47b400b2029de43','result_path':p+'archaeology/native-authority-v41/CI_38954969411_RESULT.json','run_id':38954969411,'source_commit':qual,'status':'ADMISSION_ONLY_QUALIFIED'})
check('qualified_result_exact_digest',h(result_path.read_bytes())==g['qualification_result_sha256'])
check('result_admission_only_and_unknown_claims',result['source_commit']==qual and result['status']=='ADMISSION_ONLY_QUALIFIED' and result['schema']=='UDM_NATIVE_ENVIRONMENT_QUALIFICATION_RESULT_V41' and result['first_task_gate']['status']=='PASS' and all(result['verdicts']['G'+str(i)]=='UNKNOWN' for i in range(2,7)))
archive=pathlib.Path('/workspace/qualification/native-authority-v41-38954969411.zip');check('qualification_archive_exact_digest',archive.is_file() and h(archive.read_bytes())==g['artifact_sha256'])
files=[]
for i,name in enumerate(q41gate):
 qualified=read(qual,name,f'{i:03d}-qualified');current=read(full,name,f'{i:03d}-pool');working=(R/name)
 row={'path':name,'qualified_sha256':h(qualified),'pool_committed_sha256':h(current),'working_sha256':h(working.read_bytes()) if working.is_file() else None,'freeze_sha256':result['freeze']['files'].get(name),'ordinary_working_file':working.is_file() and not working.is_symlink()}
 files.append(row);check('source_gate_binding_'+str(i),len({row['qualified_sha256'],row['pool_committed_sha256'],row['working_sha256'],row['freeze_sha256']})==1 and row['ordinary_working_file'],name)
prequery=load(C/'PREQUERY.json');execution=load(C/'PREQUERY_EXECUTION.json');pool=load(C/'FROZEN_POOL.json');curation=load(C/'METADATA_CURATION.json');protocol=load(C/'FRONTIER_PROTOCOL.json');authority=load(C/'SCREENING_AUTHORITY.json');universe=load(C/'DECLARED_UNIVERSE.json')
for key,f in [('code','curate_frontier.py'),('plan','PREQUERY.json'),('gate_descriptor','ENVIRONMENT_GATE.json')]:
 rec=execution[key];raw=(B/'prequery-committed'/f).read_bytes();check('execution_'+key+'_precommit',rec=={'path':p+'archaeology/native-authority-v41/'+f,'sha256':h(raw),'source_commit':pre} and raw==(C/f).read_bytes())
check('universe_precommit_unchanged',(B/'prequery-committed/DECLARED_UNIVERSE.json').read_bytes()==(C/'DECLARED_UNIVERSE.json').read_bytes())
check('prequery_universe_binding',prequery['qualification_and_universe']=={'environment_gate':g,'universe':{'path':p+'archaeology/native-authority-v41/DECLARED_UNIVERSE.json','sha256':h((C/'DECLARED_UNIVERSE.json').read_bytes())}})
check('prequery_execution_boundary',execution['source_commit']==pre and execution['state']=='PREQUERY_COMMITTED_BEFORE_QUERIES' and execution['target_query_count_before_receipt']==0 and execution['environment_gate']==g and execution['archive_sha256']==g['artifact_sha256'])
for key,f in [('pool','FROZEN_POOL.json'),('prequery','PREQUERY_EXECUTION.json')]:
 expected={'path':p+'archaeology/native-authority-v41/'+f,'sha256':h((C/f).read_bytes())};check('protocol_'+key+'_binding',protocol[key]==expected);check('authority_'+key+'_binding',authority[key]==expected)
check('pool_curation_binding',pool['metadata_curation_sha256']==h((C/'METADATA_CURATION.json').read_bytes()) and pool['pool']==curation['pool'])
check('metadata_execution_binding',pool['prequery_execution_sha256']==curation['prequery_execution_sha256']==h((C/'PREQUERY_EXECUTION.json').read_bytes()) and curation['prequery_plan_sha256']==h((C/'PREQUERY.json').read_bytes()))
check('authority_exact',authority['schema']=='UDM_NATIVE_CLI_AUTHORITY_V3' and authority['operation']=='screen' and authority['repo']==str(R) and authority['output_root']=='/workspace/qualification/native-authority-v41-screening-sealed' and authority['environment_gate']==g)
check('prepared_protocol_unchanged_policy',protocol['state']=='PREPARED_NOT_FROZEN' and protocol['screening'] is None and protocol['metadata_sha256'] is None and protocol['requested_roles']==2 and protocol['search_budget']==8 and protocol['candidate_cap_per_file']==64 and protocol['acquisition_native_calls']==512 and protocol['training_unique_calls']==128 and protocol['training_seconds']==3600 and protocol['per_search_seconds']==3600 and protocol['collection_seconds']==60 and protocol['execution_seconds']==600 and protocol['future_native_reserve']==64)
for tag,parent in [('bd46699e',pre),('a7d03cf4',qual)]:
 obj=load(B/('git-commit-'+tag+'.json'));raw=base64.b64decode(obj['stdout_base64']);check('direct_commit_parent_'+tag,b'parent '+parent.encode()+b'\n' in raw)
for f,expected in [('qualify_native_frontier_v3.py','d40d188be3565ed5127e06b033dd9cbf8fa32d60977d27ec47b5ae6698189418'),('qualify_native_frontier_v4.py','37cbd2de7d69350d2208afbb4d8fb6bdf8c417bf53cac842ea3e466d566518cc')]:check('controller_pin_'+f,h((C/f).read_bytes())==expected)
for f,expected in [('archaeology/native-authority-v4/curate_frontier.py','bfd0f38de30b12021090eb9592aebc79c60317c1bccdbcac3487da15f0e1b413'),('archaeology/native-environment-v3/curate_frontier.py','44455d61c8144261e2db2ce2a6de8b6b2671d9ca504353e03bb9dcd487fa3c14'),('archaeology/native-frontier-v2/curate_metadata.py','b2885099eb904395cb297ba17a0c3f1270975061b24d46ac5742a07804b8e251'),('archaeology/native-authority-v4/prepare_records.py','f9f1ad136596354256ac1f0d5e6ff6006551856daa73d9d0508da9b3bd4916b8')]:check('curator_and_assembler_pin_'+f,h((S/p/f).read_bytes())==expected)
out={'schema':'UDM_V41_METADATA_LINEAGE_PREAUDIT','status':'PASS_LOCAL_METADATA_LINEAGE' if all(c['pass'] for c in checks) else 'UNKNOWN_METADATA_LINEAGE','source_commit':full,'prequery_commit':pre,'qualified_source_commit':qual,'source_gate_files':files,'checks':checks,'limitations':['Git object and retained-receipt checks establish exact local ancestry and bytes, not an independently timestamped proof of first network access.','No global filesystem/network/process access log was available; no claim of global absence of other access.','Original code inspected statically; no curator/native CLI was executed by this audit.']}
(B/'LINEAGE_PREAUDIT.json').write_text(json.dumps(out,indent=2)+'\n'); print(json.dumps({'status':out['status'],'checks':len(checks),'failures':[c for c in checks if not c['pass']],'source_gate_file_count':len(q41gate)}))
