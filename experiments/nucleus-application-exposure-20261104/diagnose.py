"""Bounded application/Pi traces from identical qualified source with diagnostics."""
import hashlib
import json
import os
from pathlib import Path,PurePosixPath
import shutil
import signal
import subprocess
import tarfile
import threading

ROOT=Path(__file__).resolve().parent
OUT=Path('/tmp/nucleus-application-exposure');OUT.mkdir(exist_ok=True)
PARENT=Path('/tmp/universe-qualified')
digest=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
q=json.loads((PARENT/'qualification.json').read_text())['candidate']
assert q['qualified']and q['binary_sha']=='adc2275242f93633bf143e61a0c80c946579d62a19c342bca3be3b7ee23d8f93'
assert digest(PARENT/'candidate/source.tar.gz')=='0a3c0657388b87c8ef34a79ba2bf45354cb15a296670722ca158ee685d85cb83'
assert digest(PARENT/'candidate/source-manifest.json')=='23b710e6143bbcdc94ea09714d1c4038eaf4b9b85006ab285e98cb07c8012618'
with tarfile.open(PARENT/'candidate/source.tar.gz')as a:a.extractall(OUT,filter='data')
kernel=OUT/'metatron-kernel'
for name,sha in json.loads((PARENT/'candidate/source-manifest.json').read_text()).items():
 p=PurePosixPath(name);assert not p.is_absolute()and '..'not in p.parts;assert digest(kernel/name)==sha,name
build_env=os.environ|{'CARGO_TARGET_DIR':str(OUT/'target')}
build=subprocess.run(['cargo','build','--release','--locked','--features','diagnostics','--manifest-path',str(kernel/'Cargo.toml')],capture_output=True,env=build_env,timeout=600)
(OUT/'build.log').write_bytes(build.stdout+build.stderr);assert build.returncode==0
binary=OUT/'diagnostic-nucleus';shutil.copyfile(OUT/'target/release/metatron-kernel',binary);binary.chmod(0o755)
subprocess.run(['zstd','-dq',str(PARENT/'next-frontier.ndjson.zst'),'-o',str(OUT/'int-ble-prefix.ndjson')],check=True)
manifest={x['case']:x for x in json.loads(Path('/tmp/current208/inputs-manifest.json').read_text())}
cases=[('int-ble',OUT/'int-ble-prefix.ndjson','5b7a6b7ad11f5683937e8258322d47f09a9daf6d254bd921e6d23b0d1ee3b494')]
for case in ['perf/grind-ring-5','perf/magma-list-pair-n7','perf/magma-string-n4']:
 row=manifest[case];assert row['expected']==0
 cases.append((case.replace('/','--'),Path('/tmp/current208/inputs')/row['relative_path'],row['sha256']))
env=q['configuration']|{'NUCLEUS_TRACE_DOWNSTREAM':'1','NUCLEUS_TRACE_APPLICATION_FUNCTION_TYPE':'1','NUCLEUS_TRACE_APP_DOMAIN_OBLIGATION':'1'}
records=[]
for label,source,sha in cases:
 assert digest(source)==sha
 stem=OUT/label;head=bytearray();tail=bytearray();counts=[0];limit=1024*1024
 def drain(pipe):
  while True:
   data=pipe.read(65536)
   if not data:break
   counts[0]+=len(data)
   if len(head)<limit:head.extend(data[:limit-len(head)])
   tail.extend(data)
   if len(tail)>limit:del tail[:-limit]
 with source.open('rb')as f,stem.with_suffix('.stdout').open('wb')as stdout:
  p=subprocess.Popen([str(binary)],stdin=f,stdout=stdout,stderr=subprocess.PIPE,env=env,start_new_session=True)
  thread=threading.Thread(target=drain,args=(p.stderr,));thread.start();timed_out=False
  try:p.wait(timeout=240)
  except subprocess.TimeoutExpired:timed_out=True;os.killpg(p.pid,signal.SIGKILL);p.wait()
  thread.join()
 stem.with_suffix('.head.stderr').write_bytes(head);stem.with_suffix('.tail.stderr').write_bytes(tail)
 lines=tail.decode(errors='replace').splitlines();terminal=[line for line in lines if line.startswith('NUCLEUS_DOWNSTREAM:')]
 records.append(dict(case=label,input_sha=sha,rc=p.returncode,timed_out=timed_out,stderr_bytes=counts[0],capture_limit_each=limit,terminal=terminal[-1]if terminal else None))
 report=dict(status='DIAGNOSTIC_ONLY',source_unchanged=True,parent_source_manifest='23b710e6143bbcdc94ea09714d1c4038eaf4b9b85006ab285e98cb07c8012618',parent_run=41747021024,parent_binary=q['binary_sha'],binary=digest(binary),build_features=['diagnostics'],configuration=env,records=records,no_rank_or_performance_claim=True)
 (OUT/'report.json').write_text(json.dumps(report,indent=2)+'\n');print('APPLICATION_DIAGNOSTIC',json.dumps(records[-1]),flush=True)
shutil.rmtree(OUT/'target',ignore_errors=True)
