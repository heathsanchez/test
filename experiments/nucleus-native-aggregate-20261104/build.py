"""Compile the unchanged integration modules once; retain process isolation per module."""
from pathlib import Path
import os,json,tarfile,subprocess,hashlib,time
R=Path('/workspace/scratch/38cabe96376f');A=R/'nucleus-tournaments/native-aggregate';P=R/'nucleus-tournaments/receipts/neutral-proof';S=A/'source';S.mkdir(exist_ok=True)
assert hashlib.sha256((P/'candidate/source.tar.gz').read_bytes()).hexdigest()=='754c245046b5e1c33d884247cbb50ad2f235d154c0c733a94c98f54208198fed'
with tarfile.open(P/'candidate/source.tar.gz')as archive:archive.extractall(S,filter='data')
k=S/'metatron-kernel';manifest=json.loads((P/'candidate/source-manifest.json').read_text())
for path,digest in manifest.items():assert hashlib.sha256((k/path).read_bytes()).hexdigest()==digest,path
sources=sorted(p for p in(k/'tests').glob('*.rs'))
aggregate='\n'.join('#[path="'+p.name+'"]\nmod '+p.stem+';'for p in sources)+'\n';(k/'tests/native_aggregate.rs').write_text(aggregate)
q=json.loads((P/'qualification.json').read_text())['candidate'];tool=R/'rust-runtime/toolchain/bin';env={x:y for x,y in os.environ.items()if not x.startswith('NUCLEUS_')};env.update(q['configuration']);env.update(PATH=str(tool)+':'+env['PATH'],RUSTC=str(tool/'rustc'),RUSTDOC=str(tool/'rustdoc'),CARGO_HOME=str(R/'rust-runtime/cargo-home'),CARGO_TARGET_DIR=str(A/'target'),NUCLEUS_FROZEN196='/tmp/current208/inputs')
start=time.monotonic()
with(A/'build.stdout').open('wb')as out,(A/'build.stderr').open('wb')as err:r=subprocess.run(['cargo','test','--release','--locked','--offline','--manifest-path',str(k/'Cargo.toml'),'--test','native_aggregate','--no-run','--message-format=json'],env=env,stdout=out,stderr=err)
report=dict(rc=r.returncode,wall=time.monotonic()-start,source_parent=q['binary_sha'],module_count=len(sources),source_manifest_sha=hashlib.sha256((P/'candidate/source-manifest.json').read_bytes()).hexdigest());print(json.dumps(report),flush=True)
(A/'build.json').write_text(json.dumps(report,indent=2))
if r.returncode:raise SystemExit(r.returncode)
records=[json.loads(x)for x in(A/'build.stdout').read_text().splitlines()];binary=next(Path(x['executable'])for x in records if x.get('reason')=='compiler-artifact'and x.get('executable')and x['target']['name']=='native_aggregate')
(A/'binary.json').write_text(json.dumps(dict(path=str(binary),sha256=hashlib.sha256(binary.read_bytes()).hexdigest(),modules=[p.stem for p in sources]),indent=2))
