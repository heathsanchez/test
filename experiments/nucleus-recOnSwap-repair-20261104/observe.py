#!/usr/bin/env python3
import json,os,subprocess,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'nucleus-reuse-20261104'))
import tournament as t
out=Path('/tmp/repair-observation');out.mkdir(exist_ok=True)
k=t.materialize(Path.cwd(),out/'source')
# Fast input representation; no typing rule changes.
p=k/'src/id.rs';p.write_text(t.hybrid_table(p.read_text()))
env=dict(os.environ,CARGO_TARGET_DIR=str(out/'target'))
r=t.run_group(['cargo','build','--release','--locked','--features','diagnostics','--manifest-path',str(k/'Cargo.toml')],env=env,capture_output=True,timeout=600)
(out/'build.log').write_bytes(r.stdout+r.stderr);assert r.returncode==0
binary=out/'target/release/metatron-kernel';env=t.run_env();env['NUCLEUS_TRACE_DOWNSTREAM']='1';env['NUCLEUS_TRACE_APPLICATION_FUNCTION_TYPE']='1'
source=Path('/tmp/recOnSwap-prefix.ndjson')
with source.open('rb') as f,(out/'stdout').open('wb') as stdout,(out/'stderr').open('wb') as stderr:
 r=t.run_group([str(binary)],stdin=f,stdout=stdout,stderr=stderr,env=env,timeout=600)
t.write_json(out/'summary.json',dict(base=t.BASE,rc=r.returncode,prefix_sha=t.digest(source),observation='NO_TYPING_CHANGES'))
print((out/'summary.json').read_text(),flush=True)
