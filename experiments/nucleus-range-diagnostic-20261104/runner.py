import importlib.util,json,os,shutil,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('record_wave',ROOT.parent/'nucleus-parameter-telescope-20261104/runner.py');R=importlib.util.module_from_spec(spec);spec.loader.exec_module(R);t=R.t
out=Path('/tmp/range-diagnostic');out.mkdir(exist_ok=True)
k=R.materialize(out/'source',True);assert t.digest(out/'source/source.patch')=='8ad321253650a994511a9163b911af21f1dbfc08e1c347c07e71545ee4efab29'
binary,env=t.build(k,out/'source');assert binary and t.digest(binary)=='730f76f260437bcb01f567202a3af3765639582c94649988aaac6f36aa04e36d'
source=Path('/tmp/range-prefix.ndjson');assert t.digest(source)=='d9d7b1fe7267a0806f65200abc64a9c7114fb8097a9da1f3687f2560a2568bb9'
run=R.N.runtime(True);run['NUCLEUS_TRACE_DOWNSTREAM']='1'
with source.open('rb')as f:r=t.run_group([str(binary)],stdin=f,capture_output=True,env=run,timeout=180)
(out/'plain.stderr').write_bytes(r.stderr);assert r.returncode==2
built=t.run_group(['cargo','build','--release','--locked','--manifest-path',str(k/'Cargo.toml'),'--features','diagnostics'],env=env,capture_output=True,timeout=600);(out/'diagnostic-build.log').write_bytes(built.stdout+built.stderr);assert built.returncode==0
b=out/'source/target/release/metatron-kernel';assert b'METATRON_KERNEL_DIAGNOSTICS'in b.read_bytes(),'feature binary missing diagnostic marker'
trace=run|{'METATRON_KERNEL_DIAGNOSTICS':'1','NUCLEUS_TRACE_APPLICATION_FUNCTION_TYPE':'1','NUCLEUS_TRACE_DEPENDENCY_GAP':'1','NUCLEUS_TRACE_DEPENDENCY_VALUES':'1','NUCLEUS_TRACE_APP_DOMAIN_OBLIGATION':'1'}
with source.open('rb')as f,(out/'trace.stdout').open('wb')as stdout,(out/'trace.stderr').open('wb')as stderr:r=t.run_group([str(b)],stdin=f,stdout=stdout,stderr=stderr,env=trace,timeout=240)
lines=(out/'trace.stderr').read_text(errors='replace').splitlines();events=[x for x in lines if x.startswith('NUCLEUS_APPLICATION_FUNCTION_TYPE:')];gaps=[x for x in lines if x.startswith('NUCLEUS_DEPENDENCY_GAP:')];terminal=[x for x in lines if x.startswith('NUCLEUS_DOWNSTREAM:')]
summary=dict(source_sha=t.digest(source),source_patch_sha=t.digest(out/'source/source.patch'),production_binary=t.digest(binary),diagnostic_binary=t.digest(b),plain_rc=2,traced_rc=r.returncode,terminal=terminal[-1:]if terminal else[],application_events=len(events),last_application_events=events[-12:],first_conversion_gaps=gaps[:12],scope='Diagnostic on exact pre-let-bit-repair730f76 source; not a submission candidate or a proof of current repaired-stack closure')
t.write_json(out/'summary.json',summary);print(json.dumps(summary),flush=True);assert r.returncode==2 and terminal and 'pairwise_lt_range' in terminal[-1]
shutil.rmtree(out/'source/target',ignore_errors=True)
