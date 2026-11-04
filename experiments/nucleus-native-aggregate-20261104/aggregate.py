"""Compile native integration modules once; run each in an isolated process.

Library, binary and rustdoc targets remain separate checks. A named baseline
comparison is optional and never substitutes for source/oracle qualification.
"""
from pathlib import Path
import argparse,hashlib,json,os,re,shutil,subprocess,time
PATTERN=re.compile(r'^test (\S+)(?: - should panic)? \.\.\. (ok|FAILED|ignored)',re.M)
def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def write(path,value):path.write_text(json.dumps(value,indent=2)+'\n')
def outcomes(text):return dict(PATTERN.findall(text))
def compile_modules(kernel,out,env):
 out.mkdir(parents=True,exist_ok=True);source=out/'source';shutil.copytree(kernel,source,ignore=shutil.ignore_patterns('target'),dirs_exist_ok=False)
 files=sorted(p for p in source.rglob('*')if p.is_file());manifest={str(p.relative_to(source)):digest(p)for p in files};write(out/'source-manifest.json',manifest)
 modules=sorted(p for p in(source/'tests').glob('*.rs'));assert modules
 target='nucleus_native_aggregate';generated=source/'tests'/(target+'.rs');assert not generated.exists()
 generated.write_text('\n'.join('#[path="'+p.name+'"]\nmod '+p.stem+';'for p in modules)+'\n')
 build_env=env|dict(CARGO_TARGET_DIR=str((out/'target').resolve()),CARGO_TERM_COLOR='never');start=time.monotonic()
 with(out/'build.stdout').open('wb')as stdout,(out/'build.stderr').open('wb')as stderr:
  result=subprocess.run(['cargo','test','--release','--locked','--offline','--manifest-path',str(source/'Cargo.toml'),'--test',target,'--no-run','--message-format=json'],env=build_env,stdout=stdout,stderr=stderr)
 report=dict(rc=result.returncode,wall=time.monotonic()-start,source_manifest_sha=digest(out/'source-manifest.json'),generated_source_sha=digest(generated),modules=[p.stem for p in modules],configuration={k:v for k,v in env.items()if k.startswith('NUCLEUS_')})
 write(out/'build.json',report);assert result.returncode==0,'aggregate build failed; inspect build.stderr'
 records=[json.loads(x)for x in(out/'build.stdout').read_text().splitlines()]
 binary=next(Path(x['executable'])for x in records if x.get('reason')=='compiler-artifact'and x.get('executable')and x['target']['name']==target)
 report.update(binary_sha=digest(binary),binary=str(binary));write(out/'build.json',report);return binary,report

def run_modules(binary,build,out,env,baseline=None,mode='exact'):
 assert digest(binary)==build['binary_sha'];logs=out/'modules';logs.mkdir(exist_ok=True)
 listing=subprocess.run([str(binary),'--list'],env=env,capture_output=True,text=True,check=True).stdout
 names=[line[:-6]for line in listing.splitlines()if line.endswith(': test')];assert len(names)==len(set(names));rows=[];start=time.monotonic()
 for module in build['modules']:
  selected={x[len(module)+2:]for x in names if x.startswith(module+'::')}
  with(logs/(module+'.stdout')).open('wb')as stdout,(logs/(module+'.stderr')).open('wb')as stderr:
   result=subprocess.run([str(binary),module+'::','--include-ignored','--test-threads=1'],env=env,stdout=stdout,stderr=stderr,timeout=240)
  raw=outcomes((logs/(module+'.stdout')).read_text());assert all(x.startswith(module+'::')for x in raw),'cross-module filter collision'
  actual={x[len(module)+2:]:v for x,v in raw.items()};assert set(actual)==selected,'missing or unrecognized named test results'
  assert 'ignored'not in actual.values(),'include-ignored did not exercise every selected test'
  assert result.returncode==(101 if 'FAILED'in actual.values()else 0),'crash or inconsistent test result'
  expected=None;pass_=True
  if baseline is not None:
   expected=outcomes((baseline/'candidate'/('native-'+module+'-test.log')).read_text())
   if mode=='exact':pass_=actual==expected
   else:pass_=set(expected)<=set(actual)and all(actual[k]==v or(v=='FAILED'and actual[k]=='ok')for k,v in expected.items())and all(v=='ok'for k,v in actual.items()if k not in expected)
  row=dict(module=module,rc=result.returncode,complete=True,tests=actual,expected=expected,baseline_comparison=pass_);rows.append(row)
  write(out/'results.json',dict(status='COMPLETE_NAMED_INTEGRATION_TESTS'if len(rows)==len(build['modules'])and all(x['baseline_comparison']for x in rows)else'CANDIDATE',module_count=len(build['modules']),named_test_count=len(names),completed_modules=len(rows),binary_sha=build['binary_sha'],source_manifest_sha=build['source_manifest_sha'],baseline_mode=mode,configuration=build['configuration'],separate_module_processes=True,wall=time.monotonic()-start,modules=rows))
  assert pass_,module+' differs from named baseline'
 return rows

def main():
 p=argparse.ArgumentParser();p.add_argument('--kernel',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--baseline',type=Path);p.add_argument('--mode',choices=['exact','nonregression'],default='exact');a=p.parse_args();env=dict(os.environ)
 binary,build=compile_modules(a.kernel.resolve(),a.out.resolve(),env);rows=run_modules(binary,build,a.out.resolve(),env,a.baseline,a.mode);print(json.dumps(dict(modules=len(rows),tests=sum(len(x['tests'])for x in rows),build_seconds=build['wall'])),flush=True)
if __name__=='__main__':main()
