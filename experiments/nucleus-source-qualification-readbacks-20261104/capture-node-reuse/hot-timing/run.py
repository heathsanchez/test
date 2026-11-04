from pathlib import Path
import hashlib,json,os,resource,statistics,subprocess,sys,time
R=Path(__file__).resolve().parent;I=R/'input.ndjson'
SHA='8428d5d4282a608eb77e48ff62adace23212d9487ff9e86dc2e57af7c573d5f1'
EXPECTED={'A':'26244e47fb94c1ffa47a09531bc8fb9d8205bba176c459bcf31d431e9f4aea89','B':'1311e81c88d69ccd128e179c380f959de5039923873591b239a56a746e664cfd'}
config=json.loads((R/'B/qualification.json').read_text())['candidate']['configuration']
if len(sys.argv)>1:
 n=int(sys.argv[1]);arm=sys.argv[2];D=R/f'{n}-{arm}';D.mkdir(exist_ok=False);binary=R/arm/'candidate/nucleus';binary.chmod(0o755);assert hashlib.sha256(binary.read_bytes()).hexdigest()==EXPECTED[arm]
 before=I.stat();assert before.st_size==11654159
 env={k:v for k,v in os.environ.items()if not k.startswith('NUCLEUS_')}|config;start=time.monotonic()
 try:
  with I.open('rb')as i,(D/'stdout').open('wb')as o,(D/'stderr').open('wb')as e:p=subprocess.run([str(binary)],stdin=i,stdout=o,stderr=e,env=env,timeout=1800)
  rc=p.returncode
 except subprocess.TimeoutExpired:rc='TIMEOUT'
 elapsed=time.monotonic()-start;u=resource.getrusage(resource.RUSAGE_CHILDREN);after=I.stat();assert(before.st_size,before.st_mtime_ns,before.st_ino)==(after.st_size,after.st_mtime_ns,after.st_ino)
 lines=(D/'stderr').read_text(errors='replace').splitlines();terminal=[x for x in lines if x.startswith('NUCLEUS_DOWNSTREAM:')]
 row=dict(arm=arm,order=n,rc=rc,binary_sha256=EXPECTED[arm],input_sha256=SHA,input_bytes=before.st_size,configuration=config,wall=elapsed,user=u.ru_utime,system=u.ru_stime,cpu=u.ru_utime+u.ru_stime,rss_kib=u.ru_maxrss,terminal=terminal[-1:] or lines[-4:])
 (D/'report.json').write_text(json.dumps(row,indent=2));print(json.dumps(row),flush=True);sys.exit(0)
assert hashlib.sha256(I.read_bytes()).hexdigest()==SHA
rows=[]
for n,arm in enumerate('BAAB',1):
 subprocess.run([sys.executable,str(Path(__file__).resolve()),str(n),arm],check=True);row=json.loads((R/f'{n}-{arm}/report.json').read_text());rows.append(row)
 compatible=all(x['rc']==0 and x['terminal']==rows[0]['terminal']for x in rows)
 report=dict(status='RUNNING'if n<4 else'COMPLETE',rows=rows,compatible_prefix_acceptance=compatible,complete_mathlib_accept=False,no_rank_claim=True,not_source_qualified=True,candidate_only=True)
 if n==4 and compatible:
  a=[x['cpu']for x in rows if x['arm']=='A'];b=[x['cpu']for x in rows if x['arm']=='B'];report.update(median_cpu_ratio=statistics.median(b)/statistics.median(a),preset='every B CPU < every A CPU * 0.99',preset_passed=max(b)<min(a)*.99,median_rss_ratio=statistics.median(x['rss_kib']for x in rows if x['arm']=='B')/statistics.median(x['rss_kib']for x in rows if x['arm']=='A'))
 (R/'report.json').write_text(json.dumps(report,indent=2));assert compatible,'STOP: coverage boundary changed; no timing ratio'
