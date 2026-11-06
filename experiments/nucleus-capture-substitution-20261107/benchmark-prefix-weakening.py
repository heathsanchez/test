import pathlib,zipfile,json,hashlib,os,subprocess,time,statistics
r=pathlib.Path('recovered');dest=r/'prefix-benchmark';dest.mkdir(exist_ok=True)
for label,zpath,expected in [('parent','recovery-source.zip','d3e024777287f950d87bb20ba8bd02754b49a2660b52f88b96603fd89eb7883c'),('candidate',r/'prefix-weakening-ci.zip','49d7727f88b7c73f6b9959b872904b3c0de8e4372762f233d62ba533210f23f6')]:
 with zipfile.ZipFile(zpath)as z:(dest/label).write_bytes(z.read('candidate/metatron-kernel'))
 p=dest/label;p.chmod(0o755);assert hashlib.sha256(p.read_bytes()).hexdigest()==expected
flags=json.load(open(r/'evidence/flags.json'));assert len(flags)==24;assert not any('TRACE'in k for k in flags)
env={k:v for k,v in os.environ.items()if not k.startswith('NUCLEUS_')};env.update(flags)
data=(r/'original196/good/perf/fueled-chain.ndjson').read_bytes().splitlines(keepends=True);inp=dest/'chain6.ndjson';inp.write_bytes(b''.join(data[:8250]));h=hashlib.sha256(inp.read_bytes()).hexdigest();assert h=='16c9e3018e740505474ab8863017798241a5b6f07597520a0a0464aed7f6ee90'
rows=[]
for pair,order in [(-1,['parent','candidate']),(0,['parent','candidate']),(1,['candidate','parent']),(2,['parent','candidate'])]:
 for label in order:
  start=time.monotonic()
  with inp.open('rb')as f:p=subprocess.run([str((dest/label).resolve())],stdin=f,stdout=subprocess.PIPE,stderr=subprocess.PIPE,env=env,timeout=180)
  row={'pair':pair,'arm':label,'seconds':time.monotonic()-start,'rc':p.returncode,'stdout_bytes':len(p.stdout),'stderr_bytes':len(p.stderr)};assert p.returncode==0,row;rows.append(row);print(json.dumps(row),flush=True);(dest/'rows.json').write_text(json.dumps(rows,indent=2))
a=statistics.median(x['seconds']for x in rows if x['pair']>=0 and x['arm']=='parent');b=statistics.median(x['seconds']for x in rows if x['pair']>=0 and x['arm']=='candidate')
receipt={'status':'MATCHED_BOUNDED_TIMING','input_sha256':h,'parent_binary_sha256':hashlib.sha256((dest/'parent').read_bytes()).hexdigest(),'candidate_binary_sha256':hashlib.sha256((dest/'candidate').read_bytes()).hexdigest(),'flags':flags,'judgment_steps':262144,'rows':rows,'warmup_pair_excluded':-1,'parent_median_seconds':a,'candidate_median_seconds':b,'parent_over_candidate_median_ratio':a/b,'boundary':'Serial alternating matched original accepted chain6, three measured pairs after excluded warmups; local wall time only, no full-corpus runtime/completeness claim and no403 qualification.'};(dest/'receipt.json').write_text(json.dumps(receipt,indent=2));print(json.dumps({k:v for k,v in receipt.items()if k not in['flags','rows']}),flush=True)
