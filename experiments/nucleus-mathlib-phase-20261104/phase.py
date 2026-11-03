#!/usr/bin/env python3
"""Full-input parse/resolve/check observation; never a speed qualification."""
import json,os,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'nucleus-reuse-20261104'))
import tournament as t
arm=sys.argv[1];out=Path('/tmp/phase-evidence');out.mkdir(exist_ok=True)
k=t.materialize(Path.cwd(),out/'source',table=arm in ('dense','dense-facts'),facts=arm in ('facts','dense-facts'))
example=k/'examples/phase_observer.rs';example.parent.mkdir(exist_ok=True)
example.write_text('''
use std::io::{self,BufReader};
use std::time::Instant;
use metatron_kernel::{parser,checker};
fn main(){
 let now=Instant::now();
 let parsed=match parser::parse(BufReader::new(io::stdin().lock())){Ok(x)=>x,Err(e)=>{eprintln!("PARSE_ERROR {e}");std::process::exit(3)}};
 eprintln!("PHASE_PARSE_SECONDS {}",now.elapsed().as_secs_f64());
 let t=Instant::now();
 let export=match parsed.resolve(){Ok(x)=>x,Err(e)=>{eprintln!("RESOLVE_ERROR {e}");std::process::exit(3)}};
 eprintln!("PHASE_RESOLVE_SECONDS {}",t.elapsed().as_secs_f64());
 let t=Instant::now();let verdict=checker::check_export(export,checker::Limits::default());
 eprintln!("PHASE_CHECK_SECONDS {}",t.elapsed().as_secs_f64());
 std::process::exit(verdict.exit_code());
}
''')
import subprocess
env=dict(os.environ);env['CARGO_TARGET_DIR']=str(out/'target')
r=t.run_group(['cargo','build','--release','--locked','--manifest-path',str(k/'Cargo.toml'),'--example','phase_observer'],env=env,capture_output=True,timeout=600)
(out/'build.log').write_bytes(r.stdout+r.stderr);assert r.returncode==0
source=Path('/tmp/mathlib.ndjson');assert t.digest(source)==t.INPUT_SHA
runenv=t.run_env();runenv['NUCLEUS_TRACE_DOWNSTREAM']='1'
binary=out/'target/release/examples/phase_observer'
result=t.measure(binary,source,runenv,out/'full-input',timeout=1800,perf=t.probe_perf(out))
t.write_json(out/'summary.json',dict(arm=arm,base=t.BASE,patch_sha=t.digest(out/'source/source.patch'),input_sha=t.INPUT_SHA,result=result,qualification='DIAGNOSTIC_ONLY_NOT_A_SPEED_WIN'))
print(json.dumps(result),flush=True)
