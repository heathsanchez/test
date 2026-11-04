from pathlib import Path
import hashlib,json,os,subprocess,tarfile,zipfile,io,time
R=Path(__file__).resolve().parent;runtime=R/'runtime';runtime.mkdir(exist_ok=True)
with zipfile.ZipFile('/tmp/nucleus-offline-runtime.zip')as z:
 manifest=json.loads(z.read('runtime-manifest.json'))
 with tarfile.open(fileobj=io.BytesIO(z.read('rust-runtime.tar.gz')))as t:t.extractall(runtime,filter='data')
 for rel,sha in manifest['files'].items():assert hashlib.sha256((runtime/rel).read_bytes()).hexdigest()==sha,rel
source=R/'trace/metatron-kernel';target=R/'target';env=os.environ|dict(PATH=str(runtime/'toolchain/bin')+':'+os.environ['PATH'],RUSTC=str(runtime/'toolchain/bin/rustc'),RUSTDOC=str(runtime/'toolchain/bin/rustdoc'),CARGO_HOME=str(runtime/'cargo-home'),CARGO_TARGET_DIR=str(target),CARGO_BUILD_JOBS='1')
q=json.loads(Path('/tmp/nucleus-sealed-pair/B/qualification.json').read_text())['candidate'];runenv={k:v for k,v in os.environ.items()if not k.startswith('NUCLEUS_')}|q['configuration']|dict(NUCLEUS_TRACE_DOWNSTREAM='1')
input=Path('/tmp/nucleus-receiver-trials/goal/signature-diagnostic.ndjson');assert hashlib.sha256(input.read_bytes()).hexdigest()=='1022e5dc308231b91a2d8833a26006d1d082339785d61a09fc7427b30d8c0bdf'
oracle=R/'reference';oracle.mkdir(exist_ok=True)
with zipfile.ZipFile('/tmp/reference.zip')as z:
 binary=oracle/'kernel';binary.write_bytes(z.read('bundle/kernel'));binary.chmod(0o755)
assert hashlib.sha256(binary.read_bytes()).hexdigest()=='ae92c625e612fff1c90e329344d22e3c3c330383cb335ce28fd41435be3b3b94'
oracle_rows=[]
for kind,source_input in [('signature',input),('original',R/'original.ndjson')]:
 for mode,args in [('parse',['--parse-only']),('kernel',[])]:
  with(oracle/f'{kind}-{mode}.stdout').open('wb')as o,(oracle/f'{kind}-{mode}.stderr').open('wb')as e:r=subprocess.run([str(binary),*args,str(source_input)],stdout=o,stderr=e,timeout=900)
  oracle_rows.append(dict(input=kind,input_sha256=hashlib.sha256(source_input.read_bytes()).hexdigest(),mode=mode,rc=r.returncode));assert r.returncode==0
(oracle/'report.json').write_text(json.dumps(oracle_rows,indent=2))
rows=[]
for arm in ['parent-trace','skip-trace']:
 D=R/arm;D.mkdir(exist_ok=True)
 if arm=='skip-trace':
  p=source/'src/convert.rs';s=p.read_text();old='if exact_neutral_source_congruence(checker, left_structure, right_structure, &mut source_work) {';assert s.count(old)==1;s=s.replace(old,'let diagnostic_skip={ #[cfg(feature="diagnostics")] {crate::diagnostics::receiver_target_active()} #[cfg(not(feature="diagnostics"))] {false} };\n            if !diagnostic_skip && exact_neutral_source_congruence(checker, left_structure, right_structure, &mut source_work) {');p.write_text(s)
 (D/'source-manifest.json').write_text(json.dumps({str(p.relative_to(source)):hashlib.sha256(p.read_bytes()).hexdigest()for p in sorted(source.rglob('*'))if p.is_file()},indent=2))
 with(D/'build.stdout').open('wb')as o,(D/'build.stderr').open('wb')as e:r=subprocess.run(['cargo','build','--release','--locked','--offline','--manifest-path',str(source/'Cargo.toml'),'--features','diagnostics'],stdout=o,stderr=e,env=env,timeout=900)
 assert r.returncode==0,(D/'build.stderr').read_text()[-2000:]
 binary=target/'release/metatron-kernel'
 with input.open('rb')as i,(D/'stdout').open('wb')as o,(D/'stderr').open('wb')as e:r=subprocess.run([str(binary)],stdin=i,stdout=o,stderr=e,env=runenv,timeout=900)
 rows.append(dict(arm=arm,rc=r.returncode,binary_sha256=hashlib.sha256(binary.read_bytes()).hexdigest(),input_sha256=hashlib.sha256(input.read_bytes()).hexdigest(),terminal=(D/'stderr').read_text()[-300:],diagnostic_only=True,no_promotion=True));(R/'report.json').write_text(json.dumps(rows,indent=2));print(json.dumps(rows[-1]),flush=True)
