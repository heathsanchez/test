from pathlib import Path
import json,os,subprocess,time,re,hashlib,resource
R=Path(__file__).resolve().parent;source=Path('/tmp/nucleus-original-input/mathlib.ndjson');restored=json.loads(Path('/tmp/nucleus-original-input/restoration.json').read_text());assert restored['source_sha256']=='22c5de83469408950005589a3bc5ef5157c65549b5a802f85d567c29151306a6'and source.stat().st_size==6184415052
binary=R/'target/release/metatron-kernel';assert hashlib.sha256(binary.read_bytes()).hexdigest()=='430228200b2b97e2e86e2fd213835c29c9f8b88c1f4b1453ce1d849c994366af';q=json.loads((R.parent/'receipts/quotient-result-projection/qualification.json').read_text())['candidate'];env={k:v for k,v in os.environ.items()if not k.startswith('NUCLEUS_')}|q['configuration']|dict(NUCLEUS_TRACE_DOWNSTREAM='1');D=R/'full-original';D.mkdir(exist_ok=True);start=time.monotonic();before=source.stat()
usage_before=resource.getrusage(resource.RUSAGE_CHILDREN)
with source.open('rb')as i,(D/'stdout').open('wb')as o,(D/'stderr').open('wb')as e:r=subprocess.run([str(binary)],stdin=i,stdout=o,stderr=e,env=env,timeout=1800)
usage_after=resource.getrusage(resource.RUSAGE_CHILDREN)
after=source.stat();assert(before.st_size,before.st_mtime_ns)==(after.st_size,after.st_mtime_ns)
metrics=dict(wall=time.monotonic()-start,user=usage_after.ru_utime-usage_before.ru_utime,system=usage_after.ru_stime-usage_before.ru_stime,rss_kb=usage_after.ru_maxrss)
report=dict(status='COMPLETE_ORIGINAL_INPUT_REPLAY',rc=r.returncode,wall_observed=time.monotonic()-start,source_sha256=restored['source_sha256'],source_bytes=before.st_size,binary_sha256=hashlib.sha256(binary.read_bytes()).hexdigest(),configuration=q['configuration']|dict(NUCLEUS_TRACE_DOWNSTREAM='1'),metrics=metrics,terminal=(D/'stderr').read_text()[-3000:],complete_mathlib_accept=r.returncode==0,no_rank_claim=True)
(D/'report.json').write_text(json.dumps(report,indent=2));print(json.dumps(report),flush=True)
assert r.returncode in(0,2),'Original full input may not reject/crash/timeout'
