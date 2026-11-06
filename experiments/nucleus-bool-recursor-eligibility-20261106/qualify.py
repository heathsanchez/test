import concurrent.futures,hashlib,json,os,pathlib,subprocess,time
root=pathlib.Path('.')
reports=root/'reports';reports.mkdir(exist_ok=True)
flags=json.load(open('flags.json'))
binary=root/'candidate/nucleus-diagnostic'
binary_sha=hashlib.sha256(binary.read_bytes()).hexdigest()
def run(item):
 corpus,path,steps=item
 name=str(path.relative_to(corpus));safe=f'{corpus}-{steps}-{name}'.replace('/','_')
 start=time.monotonic()
 with path.open('rb')as inp,(reports/(safe+'.stderr')).open('wb')as err:
  try:rc=subprocess.run([str(binary.resolve()),str(steps)],stdin=inp,stdout=subprocess.DEVNULL,stderr=err,env={**os.environ,**flags,'NUCLEUS_TRACE_DOWNSTREAM':'1'},timeout=180).returncode
  except subprocess.TimeoutExpired:rc=124
 return {'corpus':str(corpus),'case':name,'steps':steps,'expected':0 if name.startswith('good/')else 1,'rc':rc,'seconds':time.monotonic()-start,'input_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'binary_sha256':binary_sha}
jobs=[]
for name,count in [('original196',196),('arena207',207)]:
 corpus=root/name;paths=sorted(corpus.rglob('*.ndjson'));assert len(paths)==count
 jobs += [(corpus,p,262144)for p in paths]
jobs += [(root/'arena207',p,16777216)for p in sorted((root/'arena207/bad').rglob('*.ndjson'))]
jobs += [(root/'arena207',p,16777216)for p in sorted((root/'arena207/good/perf').glob('*.ndjson'))if p.stem in {'fueled-chain','grind-ring-5','magma-list-deep-n21','magma-list-deep-n36','magma-list-pair-n21','magma-list-pair-n7'}]
rows=[]
with concurrent.futures.ThreadPoolExecutor(max_workers=3)as pool,(reports/'verdicts.jsonl').open('w')as out:
 for row in pool.map(run,jobs):
  rows.append(row);out.write(json.dumps(row)+'\n');out.flush()
  if row['rc']!=row['expected']:print(json.dumps(row),flush=True)
wrong=[r for r in rows if r['rc']not in (r['expected'],2,124)]
summary={'rows':len(rows),'wrong':len(wrong),'standard_unresolved':sum(r['steps']==262144 and r['rc']!=r['expected']for r in rows),'large_budget_invalid_accept':sum(r['steps']==16777216 and r['expected']==1 and r['rc']==0 for r in rows),'binary_sha256':binary_sha}
(reports/'summary.json').write_text(json.dumps(summary,indent=2));print(json.dumps(summary),flush=True)
assert not wrong,'Wrong verdict or process error: '+repr(wrong)
