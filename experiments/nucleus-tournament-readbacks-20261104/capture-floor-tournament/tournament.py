from pathlib import Path
import shutil,subprocess,os,json,hashlib,time
r=Path('/workspace/scratch/38cabe96376f');base=r/'nucleus-tournaments/capture-composition-tournament/quarter';o=r/'nucleus-tournaments/capture-floor-tournament';o.mkdir(exist_ok=True);tool=r/'rust-runtime/toolchain/bin';e={k:v for k,v in os.environ.items()if not k.startswith('NUCLEUS_')};e.update(json.loads((r/'nucleus-tournaments/receipts/stack-qualified/qualification.json').read_text())['candidate']['configuration']);e.update(PATH=str(tool)+':'+e['PATH'],RUSTC=str(tool/'rustc'),RUSTDOC=str(tool/'rustdoc'),CARGO_HOME=str(r/'rust-runtime/cargo-home'),CARGO_TARGET_DIR=str(o/'shared-target'),NUCLEUS_FROZEN196='/tmp/current208/inputs',NUCLEUS_TRACE_DOWNSTREAM='1')
report=[]
for minimum in [80,96,112]:
 a=o/str(minimum);a.mkdir();s=a/'source/metatron-kernel';shutil.copytree(base/'source/metatron-kernel',s,ignore=shutil.ignore_patterns('target'));p=s/'src/convert.rs';x=p.read_text();assert x.count('let allowance = (remaining / 4).min(1024);')==1;x=x.replace('let allowance = (remaining / 4).min(1024);',f'let allowance = (remaining / 4).max(remaining.min({minimum})).min(1024);');p.write_text(x);results={}
 for stage,args in [('unit',['test','--lib','capture_','--','--include-ignored','--test-threads=1']),('native-capture',['test','--test','captured_source_equivalence','--','--include-ignored','--test-threads=1']),('build',['build'])]:
  with(a/(stage+'.stdout')).open('wb')as out,(a/(stage+'.stderr')).open('wb')as err:q=subprocess.run(['cargo',args[0],'--release','--locked','--offline','--manifest-path',str(s/'Cargo.toml'),*args[1:]],env=e,stdout=out,stderr=err)
  results[stage]=q.returncode;print(minimum,stage,q.returncode,flush=True)
  if q.returncode:break
 if len(results)==3 and all(v==0 for v in results.values()):
  b=a/'nucleus';shutil.copyfile(o/'shared-target/release/metatron-kernel',b);b.chmod(0o755);results['binary_sha']=hashlib.sha256(b.read_bytes()).hexdigest();source=r/'nucleus-tournaments/source-projection-eta/next/next-frontier.ndjson';start=time.monotonic()
  with source.open('rb')as inp,(a/'original.stdout').open('wb')as out,(a/'original.stderr').open('wb')as err:q=subprocess.run([str(b)],env=e,stdin=inp,stdout=out,stderr=err,timeout=180)
  results['original']=dict(rc=q.returncode,wall=time.monotonic()-start,input_sha=hashlib.sha256(source.read_bytes()).hexdigest(),stderr=(a/'original.stderr').read_text()[-2000:]);print(minimum,'original',json.dumps(results['original']),flush=True)
 report.append(dict(minimum=minimum,results=results));(o/'report.json').write_text(json.dumps(report,indent=2))
