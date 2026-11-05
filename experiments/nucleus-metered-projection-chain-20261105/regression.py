from pathlib import Path
import os,json,subprocess,hashlib,time,resource
R=Path(__file__).resolve().parent;runtime=Path('/tmp/nucleus-frontier-investigation/runtime');target=R/'target';env={k:v for k,v in os.environ.items()if not k.startswith('NUCLEUS_')}|dict(PATH=str(runtime/'toolchain/bin')+':'+os.environ['PATH'],RUSTC=str(runtime/'toolchain/bin/rustc'),RUSTDOC=str(runtime/'toolchain/bin/rustdoc'),CARGO_HOME=str(runtime/'cargo-home'),CARGO_TARGET_DIR=str(target),CARGO_BUILD_JOBS='1');config=json.loads(Path('/tmp/nucleus-sealed-pair/B/qualification.json').read_text())['candidate']['configuration'];env|=config
with(R/'build.stdout').open('wb')as o,(R/'build.stderr').open('wb')as e:r=subprocess.run(['cargo','build','--release','--locked','--offline','--manifest-path',str(R/'source/Cargo.toml')],env=env,stdout=o,stderr=e,timeout=900)
assert r.returncode==0,(R/'build.stderr').read_text()[-2000:]
binary=R/'nucleus';binary.write_bytes((target/'release/metatron-kernel').read_bytes());binary.chmod(0o755);rows=[]
for kind,p in [('hot',Path('/tmp/nucleus-parametric-hot-pair/hot.ndjson')),('compact',Path('/tmp/nucleus-receiver-snapshot-probe/compact/data/goal.ndjson')),('proof2',Path('/tmp/nucleus-proof2-frontier/next-frontier.ndjson'))]:
 D=R/kind;D.mkdir(exist_ok=True);start=time.monotonic()
 with p.open('rb')as i,(D/'stdout').open('wb')as o,(D/'stderr').open('wb')as e:r=subprocess.run([str(binary)],stdin=i,stdout=o,stderr=e,env=env,timeout=900)
 row=dict(input=kind,input_sha256=hashlib.sha256(p.read_bytes()).hexdigest(),rc=r.returncode,wall=time.monotonic()-start,terminal=(D/'stderr').read_text()[-1000:]);rows.append(row);print(json.dumps(row),flush=True)
 (R/'report.json').write_text(json.dumps(dict(status='COMPLETE'if len(rows)==3 else'RUNNING',candidate_only=True,no_promotion=True,no_speed_claim=True,binary_sha256=hashlib.sha256(binary.read_bytes()).hexdigest(),configuration=config,rows=rows),indent=2));assert r.returncode in(0,2),'REJECT or crash blocks candidate'
 assert kind=='proof2' or r.returncode==0,'STOP: accepted-prefix regression'
