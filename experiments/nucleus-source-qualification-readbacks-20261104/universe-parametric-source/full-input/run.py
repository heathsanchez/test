from pathlib import Path
import hashlib,json,os,resource,statistics,subprocess,sys,time
R=Path(__file__).resolve().parent;I=Path('/tmp/nucleus-original-input/mathlib.ndjson')
SHA='22c5de83469408950005589a3bc5ef5157c65549b5a802f85d567c29151306a6'
EXPECTED={'A':'26244e47fb94c1ffa47a09531bc8fb9d8205bba176c459bcf31d431e9f4aea89','B':'82ebbce2278e54f82667e4d12793034acdf72f329b989e4605cf65473c9de715'}
config=json.loads((R/'B/qualification.json').read_text())['candidate']['configuration']|{'NUCLEUS_TRACE_DOWNSTREAM':'1'}
if len(sys.argv)>1:
 n=int(sys.argv[1]);arm=sys.argv[2];D=R/f'{n}-{arm}';D.mkdir(exist_ok=False);binary=R/arm/'candidate/nucleus';binary.chmod(0o755);assert hashlib.sha256(binary.read_bytes()).hexdigest()==EXPECTED[arm]
 before=I.stat();assert before.st_size==6184415052
 env={k:v for k,v in os.environ.items()if not k.startswith('NUCLEUS_')}|config;start=time.monotonic()
 try:
  with I.open('rb')as i,(D/'stdout').open('wb')as o,(D/'stderr').open('wb')as e:p=subprocess.run([str(binary)],stdin=i,stdout=o,stderr=e,env=env,timeout=1800)
  rc=p.returncode
 except subprocess.TimeoutExpired:rc='TIMEOUT'
 elapsed=time.monotonic()-start;u=resource.getrusage(resource.RUSAGE_CHILDREN);after=I.stat();assert(before.st_size,before.st_mtime_ns,before.st_ino)==(after.st_size,after.st_mtime_ns,after.st_ino)
 lines=(D/'stderr').read_text(errors='replace').splitlines();terminal=[x for x in lines if x.startswith('NUCLEUS_DOWNSTREAM:')]
 row=dict(arm=arm,order=n,rc=rc,binary_sha256=EXPECTED[arm],input_sha256=SHA,input_bytes=before.st_size,configuration=config,wall=elapsed,user=u.ru_utime,system=u.ru_stime,cpu=u.ru_utime+u.ru_stime,rss_kib=u.ru_maxrss,terminal=terminal[-1:] or lines[-4:])
 (D/'report.json').write_text(json.dumps(row,indent=2));print(json.dumps(row),flush=True);sys.exit(0)
assert json.loads(Path('/tmp/nucleus-original-input/restoration.json').read_text())['source_sha256']==SHA
assert json.loads((R/'A/qualification.json').read_text())['candidate']['configuration']==json.loads((R/'B/qualification.json').read_text())['candidate']['configuration']
rows=[]
for n,arm in enumerate('BAAB',1):
 subprocess.run([sys.executable,str(Path(__file__).resolve()),str(n),arm],check=True);row=json.loads((R/f'{n}-{arm}/report.json').read_text());rows.append(row)
 compatible=all(x['rc']==2 and x['terminal']==rows[0]['terminal']for x in rows)
 report=dict(status='RUNNING'if n<4 else'COMPLETE',rows=rows,compatible_first_frontier=compatible,complete_mathlib_accept=False,no_rank_claim=True)
 if n==4 and compatible:
  a=[x['cpu']for x in rows if x['arm']=='A'];b=[x['cpu']for x in rows if x['arm']=='B'];report.update(median_cpu_ratio=statistics.median(b)/statistics.median(a),preset='every B CPU < every A CPU * 0.99',preset_passed=max(b)<min(a)*.99,median_rss_ratio=statistics.median(x['rss_kib']for x in rows if x['arm']=='B')/statistics.median(x['rss_kib']for x in rows if x['arm']=='A'))
 (R/'report.json').write_text(json.dumps(report,indent=2));assert compatible,'STOP: coverage boundary changed; no timing ratio'

h=hashlib.sha256();size=0
with I.open('rb')as f:
 while block:=f.read(8*1024*1024):h.update(block);size+=len(block)
assert h.hexdigest()==SHA and size==6184415052
(R/'input-verification.json').write_text(json.dumps(dict(sha256=h.hexdigest(),bytes=size,after_all_samples=True),indent=2))
