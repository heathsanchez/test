import os,pathlib,subprocess,zipfile,tarfile,json,hashlib,gzip,time,re
P=pathlib.Path;root=P.cwd();out=root/'reports';out.mkdir(exist_ok=True)
def sha(p):return hashlib.sha256(P(p).read_bytes()).hexdigest()
def artifact(repo,id,label,digest):
 p=root/(label+'.zip')
 with p.open('wb')as f:subprocess.run(['gh','api',f'repos/{repo}/actions/artifacts/{id}/zip'],stdout=f,check=True)
 assert sha(p)==digest
 with zipfile.ZipFile(p)as z:assert z.testzip()is None;z.extractall(root/label)
artifact('heathsanchez/test',13555074038,'base','42bfe782d0499049dc89512212e2f76170c4fbc1a233dcf7a8a77e886ec66840')
with tarfile.open('base/candidate/source.tar.gz')as t:t.extractall(root,filter='data')
source=root/'metatron-kernel'
flags=json.loads(P('base/reports/receipt.json').read_text())['flags'];assert len(flags)==24
env={k:v for k,v in os.environ.items()if not k.startswith('NUCLEUS_')};env.update(flags);env.update(RUST_MIN_STACK='16777216',CARGO_BUILD_JOBS='2')
import shutil
exp = root / 'experiments/nucleus-chain9-budget-20261107'
shutil.copy2(exp / 'budget-probe.rs', source / 'src/bin/budget-probe.rs')
with (out / 'build.log').open('w') as log:
 subprocess.run(['cargo','build','--locked','--release','--features','diagnostics',
                 '--bin','budget-probe'],cwd=source,env=env,stdout=log,stderr=subprocess.STDOUT,check=True)
artifact('leanprover/lean-kernel-arena',11272848230,'original','f6cd590db7f6fb92b8d1b3ca87231d4b0f521f085d73f93abd005f5caaff86d2')
with tarfile.open('original/lean-arena-tests.tar.gz')as t:t.extractall(root/'original196',filter='data')
data=P('original196/good/perf/fueled-chain.ndjson').read_bytes().splitlines(keepends=True);P('chain9.ndjson').write_bytes(b''.join(data[:11792]))
assert sha('chain9.ndjson')=='78dfd772d8a1e6b91484434718af521885fec1386c7a841b70a12e0a7c2f56a3'

binary = source / 'target/release/budget-probe'
rows = []
for steps in (262144, 524288, 1048576):
 label = str(steps)
 e = {**env, 'NUCLEUS_TRACE_DOWNSTREAM':'1','NUCLEUS_TRACE_APPLICATION_FUNCTION_TYPE':'1',
      'NUCLEUS_TRACE_LAMBDA_TRIAL_WORK':'1'}
 t = time.monotonic()
 try:
  with P('chain9.ndjson').open('rb') as inp:
   result = subprocess.run([str(binary),label],stdin=inp,env=e,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=180)
  rc, stdout, stderr = result.returncode, result.stdout, result.stderr
 except subprocess.TimeoutExpired as error:
  rc, stdout, stderr = None, error.stdout or b'', error.stderr or b''
 (out/(label+'.stderr')).write_bytes(stderr)
 (out/(label+'.stdout')).write_bytes(stdout)
 lines=stderr.decode().splitlines()
 rows.append({'steps':steps,'rc':rc,'seconds':time.monotonic()-t,
              'first_failure':next((l for l in lines if l.startswith('NUCLEUS_DOWNSTREAM:')),None),
              'owner_work':next((l for l in lines if l.startswith('lambda-trial-work expression=ExprId(10707)')),None)})
 (out/'rows.json').write_text(json.dumps(rows,indent=2))
 if rc == 0:
  break
assert rows[0]['rc']==2 and 'chain9_datF' in (rows[0]['first_failure'] or '')
(out/'receipt.json').write_text(json.dumps({'source_artifact':13555074038,'binary_sha256':sha(binary),
 'input_sha256':sha('chain9.ndjson'),'flags':flags,'rows':rows,
 'boundary':'Diagnostic allowance ladder through the native entry point. Added trace flags are common to all runs. Raised allowance is outside standard qualification.'},indent=2))
