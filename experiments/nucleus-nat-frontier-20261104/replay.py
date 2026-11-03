#!/usr/bin/env python3
"""Replay unpromoted Nat-frontier trials on the qualified independent stack.

Run from a complete checkout containing the pinned base commit. A completed
harness run with checker rc=2 is UNKNOWN, not a successful proof check.
"""
import argparse,importlib.util,json,os,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parent
SPEC=importlib.util.spec_from_file_location('quotient_wave',ROOT.parent/'nucleus-quotient-reuse-20261104/runner.py')
Q=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(Q)

def main():
 p=argparse.ArgumentParser();p.add_argument('variant',choices=['baseline','function-domain','captured-subtraction','predecessor','stack']);p.add_argument('--out',required=True);p.add_argument('--unit',action='store_true');p.add_argument('--demand',action='store_true');a=p.parse_args();out=Path(a.out).resolve();out.mkdir(parents=True,exist_ok=True);os.chdir(ROOT.parents[1])
 k=Q.materialize(out,True)
 patches={'baseline':[],'function-domain':['function-domain.patch'],'captured-subtraction':['captured-subtraction.patch'],'predecessor':['complete-replay.patch'],'stack':['complete-replay.patch','function-domain.patch']}[a.variant]
 for name in patches:
  r=Q.t.run_group(['patch','--batch','--fuzz=0','-p1','-i',str(ROOT/name)],cwd=out,capture_output=True,timeout=30);(out/(name+'.log')).write_bytes(r.stdout+r.stderr);assert r.returncode==0
  with(out/'source.patch').open('a')as f:f.write((ROOT/name).read_text())
 if a.unit:
  tests='captured_native_tests.rs'if a.variant in('predecessor','stack')else'captured_native_tests_initial.rs'
  with(k/'src/machine.rs').open('a')as f:f.write((ROOT/tests).read_text())
 source=out/'source-prefix.ndjson';subprocess.run(['zstd','-d','-f',str(ROOT/'fixtures/nat-prefix.ndjson.zst'),'-o',str(source)],check=True,capture_output=True);assert Q.t.digest(source)=='7767e7f90b3e24b30ecb5324f1117d6858b5f40653b31011ad1948eed747e8ea'
 binary,env=Q.t.build(k,out);assert binary is not None;runtime=Q.t.run_env();runtime['NUCLEUS_TRACE_DOWNSTREAM']='1'
 if a.variant in('function-domain','stack'):runtime['NUCLEUS_EXPERIMENTAL_FUNCTION_DOMAIN_RETRY']='1'
 if a.demand:runtime['NUCLEUS_EXPERIMENTAL_DEMAND_MAJOR']='1'
 with source.open('rb')as f:r=Q.t.run_group([str(binary)],stdin=f,env=runtime,capture_output=True,timeout=120)
 (out/'stdout').write_bytes(r.stdout);(out/'stderr').write_bytes(r.stderr)
 report=dict(variant=a.variant,rc=r.returncode,source_patch_sha=Q.t.digest(out/'source.patch'),binary_sha=Q.t.digest(binary),input_sha=Q.t.digest(source),configuration={k:v for k,v in runtime.items()if k.startswith('NUCLEUS_')},state='ACCEPT'if r.returncode==0 else'UNKNOWN'if r.returncode==2 else'REJECT_OR_ERROR')
 if a.unit:
  env.update(runtime);unit=Q.t.run_group(['cargo','test','--release','--locked','--manifest-path',str(k/'Cargo.toml'),'--lib','captured_native_subtraction_tests'],env=env,capture_output=True,timeout=600);(out/'unit.log').write_bytes(unit.stdout+unit.stderr);report['unit_rc']=unit.returncode
 Q.t.write_json(out/'replay.json',report);print(json.dumps(report),flush=True)
if __name__=='__main__':main()
