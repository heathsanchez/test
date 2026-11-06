"""Matched observation-only probes. Neither arm can reuse shadow metadata."""
import hashlib,json,pathlib,os,subprocess,time
flags=json.load(open('flags.json'));out=pathlib.Path('reports/probe');out.mkdir(parents=True,exist_ok=True)
expected={'magma-list-pair-n7':'abce636f6a7dd529c0dc6bbad8e7c8e2eaecfdda0d04c191d7f868e3a4468d35','fueled-chain':'e5ca34489fc7b8ee13b1e7f09f76247ab7b01dd1a752a13cc8b796c569e1401a'}
rows=[]
for name,sha in expected.items():
 source=pathlib.Path('original196/good/perf')/(name+'.ndjson');assert hashlib.sha256(source.read_bytes()).hexdigest()==sha
 for arm in ['off','on']:
  env={**os.environ,**flags,'NUCLEUS_TRACE_DOWNSTREAM':'1'};env.pop('NUCLEUS_DIAGNOSTIC_SHARED_TYPING',None)
  if arm=='on':env['NUCLEUS_DIAGNOSTIC_SHARED_TYPING']='1'
  start=time.monotonic()
  with source.open('rb')as inp,(out/(name+'-'+arm+'.stderr')).open('wb')as err:
   r=subprocess.run(['candidate/metatron-kernel'],stdin=inp,stderr=err,stdout=subprocess.PIPE,env=env,timeout=300)
  summaries=[];trace=[]
  for line in (out/(name+'-'+arm+'.stderr')).read_text(errors='replace').splitlines():
   if line.startswith('NUCLEUS_SHARED_TYPING_SHADOW:'):summaries.append(json.loads(line.split(':',1)[1]))
   if line.startswith('NUCLEUS_DOWNSTREAM:'):trace.append(line)
  keys=['exact_source_queries','completed_ordinary_matches','pending_ordinary_matches','completed_match_exact_unresolved','pending_match_exact_unresolved','untracked_due_capacity']
  row={'case':name,'input_sha256':sha,'arm':arm,'rc':r.returncode,'stdout_sha256':hashlib.sha256(r.stdout).hexdigest(),'first_failure_trace':trace,'seconds':time.monotonic()-start,'checker_reports':len(summaries),'diagnostic_only':True,'acceptance_authority':False,'counts':{k:sum(x[k]for x in summaries)for k in keys}}
  rows.append(row);print(json.dumps(row),flush=True)
 a,b=rows[-2:];assert a['rc']==b['rc']==2;assert a['stdout_sha256']==b['stdout_sha256'];assert a['first_failure_trace']==b['first_failure_trace'] and a['first_failure_trace'];assert b['counts']['exact_source_queries']>0
(out/'results.json').write_text(json.dumps(rows,indent=2))
