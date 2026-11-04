from pathlib import Path
import os,json,subprocess
R=Path(__file__).resolve().parent;W=R.parent.parent.resolve();q=json.loads((R.parent/'receipts/projected-function-eta/qualification.json').read_text())['candidate'];env=os.environ|q['configuration']|dict(NUCLEUS_FROZEN196='/tmp/current208/inputs',PATH=str(W/'rust-runtime/toolchain/bin')+':'+os.environ['PATH'],RUSTC=str(W/'rust-runtime/toolchain/bin/rustc'),RUSTDOC=str(W/'rust-runtime/toolchain/bin/rustdoc'),CARGO_HOME=str(W/'rust-runtime/cargo-home'),CARGO_TARGET_DIR=str(R/'target'))
manifest=R/'source/metatron-kernel/Cargo.toml'
for name,cmd in [('library-configured',['cargo','test','--release','--locked','--offline','--manifest-path',str(manifest),'--lib','--','--include-ignored']),('build-final',['cargo','build','--release','--locked','--offline','--manifest-path',str(manifest)])]:
 with(R/(name+'.log')).open('wb')as f:r=subprocess.run(cmd,env=env,stdout=f,stderr=subprocess.STDOUT)
 print(name,r.returncode,flush=True)
 if r.returncode:raise SystemExit(r.returncode)
subprocess.run(['python',str(R/'benchmark.py')],check=True)
