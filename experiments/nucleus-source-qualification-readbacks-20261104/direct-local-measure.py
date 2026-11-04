import os,json,subprocess,time,hashlib
from pathlib import Path
R=Path('/workspace/scratch/38cabe96376f/nucleus-tournaments')
O=R/'canonical-parser/direct-stack-screen';O.mkdir(exist_ok=True)
baseline=R/'receipts/universe-qualified/candidate/nucleus'
candidate=R/'receipts/canonical-parser/qualified-winner/candidate/nucleus'
env={k:v for k,v in os.environ.items()if not k.startswith('NUCLEUS_')}
env.update(json.loads((R/'receipts/stack-qualified/qualification.json').read_text())['candidate']['configuration']);env['NUCLEUS_TRACE_DOWNSTREAM']='1'
rows=[]
for i,order in enumerate([('baseline','candidate'),('candidate','baseline'),('baseline','candidate')]):
 pair={}
 for label in order:
  b=baseline if label=='baseline'else candidate;b.chmod(0o755)
  out=O/f'{i}-{label}';start=time.monotonic()
  with open('/tmp/nucleus-mathlib-22c5de8346940895/mathlib.ndjson','rb')as inp,open(str(out)+'.stdout','wb')as stdout,open(str(out)+'.stderr','wb')as stderr:
   p=subprocess.Popen([str(b)],stdin=inp,stdout=stdout,stderr=stderr,env=env,start_new_session=True)
   pid,status,usage=os.wait4(p.pid,0);p.returncode=os.waitstatus_to_exitcode(status)
  terminal=[x for x in Path(str(out)+'.stderr').read_text().splitlines()if x.startswith('NUCLEUS_DOWNSTREAM:')]
  row=dict(rc=p.returncode,user=usage.ru_utime,system=usage.ru_stime,rss=usage.ru_maxrss,wall=time.monotonic()-start,terminal=terminal[-1]if terminal else None,binary_sha=hashlib.sha256(b.read_bytes()).hexdigest())
  pair[label]=row;print(i,label,json.dumps(row),flush=True)
 assert pair['baseline']['rc']==pair['candidate']['rc']==2 and pair['baseline']['terminal']==pair['candidate']['terminal']
 pair['ratio']=(pair['candidate']['user']+pair['candidate']['system'])/(pair['baseline']['user']+pair['baseline']['system']);rows.append(pair);(O/'pairs.json').write_text(json.dumps(rows,indent=2))
