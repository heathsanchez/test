from pathlib import Path
import os,json,subprocess,hashlib,time,resource
R=Path(__file__).resolve().parent;D=R/'full';D.mkdir(exist_ok=True);p=Path('/tmp/nucleus-original-input/mathlib.ndjson');binary=R/'nucleus';expected='22c5de83469408950005589a3bc5ef5157c65549b5a802f85d567c29151306a6';config=json.loads((R/'report.json').read_text())['configuration'];assert p.stat().st_size==6184415052
for proc in Path('/proc').iterdir():
 try:assert (proc/'comm').read_text().strip()not in ['rustc','cargo','metatron-kernel'],'No concurrent build or replay'
 except (OSError,ProcessLookupError):pass
h=hashlib.sha256()
with p.open('rb')as f:
 for b in iter(lambda:f.read(1048576),b''):h.update(b)
assert h.hexdigest()==expected
report=dict(status='RUNNING',binary_sha256=hashlib.sha256(binary.read_bytes()).hexdigest(),runtime_source_label='runtime237',input_sha256=expected,input_bytes=p.stat().st_size,configuration=config,no_promotion=True,no_speed_claim=True,no_rank_claim=True,complete_mathlib_accept=False);(D/'report.json').write_text(json.dumps(report,indent=2));env={k:v for k,v in os.environ.items()if not k.startswith('NUCLEUS_')}|config;start=time.monotonic()
with p.open('rb')as i,(D/'stdout').open('wb')as o,(D/'stderr').open('wb')as e:r=subprocess.run([str(binary)],stdin=i,stdout=o,stderr=e,env=env,timeout=3600)
u=resource.getrusage(resource.RUSAGE_CHILDREN);report.update(status='COMPLETE',rc=r.returncode,wall=time.monotonic()-start,cpu=u.ru_utime+u.ru_stime,max_rss_kib=u.ru_maxrss,complete_mathlib_accept=r.returncode==0,stdout_tail=(D/'stdout').read_text()[-3000:],stderr_tail=(D/'stderr').read_text()[-3000:]);(D/'report.json').write_text(json.dumps(report,indent=2));print(json.dumps(report),flush=True)
