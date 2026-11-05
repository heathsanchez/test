from pathlib import Path
import hashlib,json,os,resource,statistics,subprocess,sys,time
R=Path(__file__).resolve().parent;I=R/'hot.ndjson'
SHA='8428d5d4282a608eb77e48ff62adace23212d9487ff9e86dc2e57af7c573d5f1'
EXPECTED={'A': '2003c831c32a8249e8524349bc169f3e491e9c84fb71b5fc8db9bce2a8583d01', 'B': '7d2e15a8508df81fd6e7c8d7004951e16c8ac81e120c41317dfb085401379f1e', 'C': 'b8c3fe11076025d687f750f79221a9a15838195f0944814fef8bdee2099c7b59'}
config=json.loads((R/'configuration.json').read_text())
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
for proc in Path('/proc').iterdir():
 try:assert (proc/'comm').read_text().strip()not in ['rustc','cargo','metatron-kernel'],'No concurrent build/replay'
 except (OSError,ProcessLookupError):pass
for n,arm in enumerate('CBAABC',1):
 subprocess.run([sys.executable,str(Path(__file__).resolve()),str(n),arm],check=True);row=json.loads((R/f'{n}-{arm}/report.json').read_text());rows.append(row)
 compatible=all(x['rc']==0 and x['terminal']==[]for x in rows)
 report=dict(status='RUNNING'if n<6 else'COMPLETE',rows=rows,compatible_accepted_prefix=compatible,complete_mathlib_accept=False,no_rank_claim=True,candidate_qualified=False,accepted_original_prefix=True,order='CBAABC',source_stages=dict(A='sealed-default2003',B='immutable-root-universe-payload-runtime250',C='completed-typed-conversion-runtime253'))
 if n==6 and compatible:
  groups={arm:[x for x in rows if x['arm']==arm]for arm in 'ABC'};a=[x['cpu']for x in groups['A']];stats={}
  for arm,group in groups.items():
   cpus=[x['cpu']for x in group];stats[arm]=dict(median_cpu=statistics.median(cpus),median_cpu_ratio_to_default=statistics.median(cpus)/statistics.median(a),every_sample_beats_every_default_by_1percent=max(cpus)<min(a)*.99,median_rss_kib=statistics.median(x['rss_kib']for x in group))
  winner=min(stats,key=lambda arm:stats[arm]['median_cpu']);strict_dominance=all(max(x['cpu']for x in groups[winner])<min(x['cpu']for x in group)*.99 for arm,group in groups.items()if arm!=winner)
  report.update(statistics=stats,lowest_median_arm=winner,dominates_all_other_arms_by_1percent=strict_dominance,preset='Every winning CPU sample must beat every other-arm CPU sample by more than1percent')
 (R/'report.json').write_text(json.dumps(report,indent=2));assert compatible,'STOP: accepted-prefix verdict mismatch; no timing ratio'

h=hashlib.sha256();size=0
with I.open('rb')as f:
 while block:=f.read(8*1024*1024):h.update(block);size+=len(block)
assert h.hexdigest()==SHA and size==11654159
(R/'input-verification.json').write_text(json.dumps(dict(sha256=h.hexdigest(),bytes=size,after_all_samples=True),indent=2))
