"""Test reuse of actual capture aliases and bounded local replay exposure."""
import importlib.util
import json
from pathlib import Path,PurePosixPath
import re
import shutil
import tarfile

ROOT=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('universe_parent',ROOT.parent/'nucleus-universe-records-20261104/qualify.py')
U=importlib.util.module_from_spec(spec);spec.loader.exec_module(U)
t=U.Q.t
OUT=Path('/tmp/nucleus-replay-reuse');BASE=Path('/tmp/universe-qualified')
SHA='adc2275242f93633bf143e61a0c80c946579d62a19c342bca3be3b7ee23d8f93'

def materialize(label,patches):
    arm=OUT/label;arm.mkdir();kernel=arm/'metatron-kernel'
    with tarfile.open(BASE/'candidate/source.tar.gz')as archive:archive.extractall(arm,filter='data')
    for name,sha in json.loads((BASE/'candidate/source-manifest.json').read_text()).items():
        p=PurePosixPath(name);assert not p.is_absolute()and '..'not in p.parts;assert t.digest(kernel/name)==sha
    for patch in patches:
        result=t.run_group(['patch','--batch','--fuzz=0','-p1','-i',str(patch)],cwd=arm,capture_output=True,timeout=30)
        assert result.returncode==0,(patch,result.stdout,result.stderr)
    (arm/'source.patch').write_bytes((BASE/'candidate/source.patch').read_bytes()+b''.join(p.read_bytes()for p in patches))
    files=sorted(p for p in kernel.rglob('*')if p.is_file())
    t.write_json(arm/'source-manifest.json',{str(p.relative_to(kernel)):t.digest(p)for p in files})
    with tarfile.open(arm/'source.tar.gz','w:gz')as archive:
        for p in files:archive.add(p,arcname='metatron-kernel/'+str(p.relative_to(kernel)))
    return arm,kernel

def measure(binary,source,env,directory):
    result=t.measure(binary,source,env,directory,timeout=180,perf=False)
    lines=(directory/'stderr').read_text(errors='replace').splitlines()
    result['terminal']=next((line for line in reversed(lines)if line.startswith('NUCLEUS_DOWNSTREAM:')),None)
    return result

def main():
    OUT.mkdir(exist_ok=True)
    q=json.loads((BASE/'qualification.json').read_text())['candidate'];assert q['qualified']and q['binary_sha']==SHA
    assert t.digest(BASE/'candidate/source.tar.gz')=='0a3c0657388b87c8ef34a79ba2bf45354cb15a296670722ca158ee685d85cb83'
    assert t.digest(BASE/'candidate/source-manifest.json')=='23b710e6143bbcdc94ea09714d1c4038eaf4b9b85006ab285e98cb07c8012618'
    env=U.Q.R.N.runtime(True);assert{k:v for k,v in env.items()if k.startswith('NUCLEUS_')}==q['configuration']
    traced=env|{'NUCLEUS_TRACE_DOWNSTREAM':'1'}
    source=OUT/'int-ble-prefix.ndjson'
    t.run_group(['zstd','-dq',str(BASE/'next-frontier.ndjson.zst'),'-o',str(source)],capture_output=True,timeout=30)
    assert t.digest(source)=='5b7a6b7ad11f5683937e8258322d47f09a9daf6d254bd921e6d23b0d1ee3b494'
    original=BASE/'candidate/nucleus';assert t.digest(original)==SHA;original.chmod(0o755)
    red=measure(original,source,traced,OUT/'red-prefix');assert red['rc']==2 and "Int.ble'_eq_true"in(red['terminal']or'')
    arm,kernel=materialize('red-alias-tests',[ROOT/'alias-tests.patch'])
    prior=Path('/tmp/replay-prior/red-alias-tests')
    assert json.loads((prior/'source-manifest.json').read_text())==json.loads((arm/'source-manifest.json').read_text())
    assert (prior/'source.patch').read_bytes()==(arm/'source.patch').read_bytes()
    raw=(prior/'tests.log').read_text();(arm/'tests.log').write_text(raw)
    expected={'machine::replay_source_alias_guards::actual_alias_bindings_reuse_one_completed_source_computation','machine::replay_source_alias_guards::alias_keys_retain_the_bound_universe_map_and_separate_other_instances'}
    assert set(t.failures(raw))==expected and t.native_target_valid(101,raw)
    t.write_json(OUT/'reused_assertion_red.json',dict(status='REUSED_EXACT_NATIVE_TEST_SOURCE',run=41751479444,artifact=13285953057,artifact_sha='d860e8e3c4c251a3bce3743c45cda6c8619aa8518c2275e403b7bbcaaac2aec4',source_patch_sha=t.digest(arm/'source.patch'),source_manifest_sha=t.digest(arm/'source-manifest.json'),test_failures=sorted(expected),source_files_identical=True))
    manifest={x['case']:x for x in json.loads(Path('/tmp/current208/inputs-manifest.json').read_text())}
    results=[]
    for name,patches in [('alias-keys',[ROOT/'alias-key-with-tests.patch']),('alias-plus-exposure',[ROOT/'alias-key-with-tests.patch',ROOT/'local-cap.patch'])]:
        arm,kernel=materialize(name,patches)
        try:
            binary,build_env=t.build(kernel,arm);assert binary is not None,'Compile failure'
            test=t.run_group(['cargo','test','--release','--locked','--manifest-path',str(kernel/'Cargo.toml'),'--lib','--','--include-ignored','--test-threads=1'],env=build_env|env|{'NUCLEUS_FROZEN196':'/tmp/current208/inputs'},capture_output=True,timeout=600)
            raw=(test.stdout+test.stderr).decode(errors='replace');(arm/'library.log').write_text(raw)
            assert test.returncode==0 and t.native_target_valid(test.returncode,raw)and '0 failed; 0 ignored;'in raw,'Complete library gate failed'
            checks=[]
            for case in json.loads((ROOT.parent/'nucleus-universe-reconcile-20261104/inputs/manifest.json').read_text()):
                p=ROOT.parent/'nucleus-universe-reconcile-20261104/inputs'/case['file'];assert t.digest(p)==case['sha256']
                result=measure(binary,p,traced,arm/case['case'])
                assert result['rc']==0 if case['expect_reference']==0 else result['rc']in(1,2)
                checks.append(dict(case=case['case'],expected=case['expect_reference'],result=result))
            prefix=measure(binary,source,traced,arm/'int-ble')
            assert prefix['rc']in(0,2),'Valid prefix must never REJECT or error'
            for case in ['perf/grind-ring-5','perf/magma-list-pair-n7','perf/magma-string-n4','bugs/eta-ctor-alias']:
                row=manifest[case];p=Path('/tmp/current208/inputs')/row['relative_path'];assert t.digest(p)==row['sha256']
                result=measure(binary,p,traced,arm/case.replace('/','--'))
                assert result['rc']in(row['expected'],2),'Incorrect or execution-error screen result'
                checks.append(dict(case=case,expected=row['expected'],result=result))
            gained=[x['case']for x in checks if x['case'].startswith(('perf/','bugs/'))and x['result']['rc']==x['expected']]
            result=dict(arm=name,status='CANDIDATE_COVERAGE_GAIN'if prefix['rc']==0 or gained else'NO_COVERAGE_GAIN',newly_decisive=gained,binary_sha=t.digest(binary),source_patch_sha=t.digest(arm/'source.patch'),prefix=prefix,checks=checks,library_summary=re.findall(t.SUMMARY,raw),no_full_qualification_or_speed_claim=True)
        except AssertionError as error:result=dict(arm=name,status='REJECTED_AT_SCREEN',reason=str(error))
        results.append(result);t.write_json(OUT/'results.json',results);print('REPLAY_REUSE_SCREEN',json.dumps(result),flush=True)
        shutil.rmtree(arm/'target',ignore_errors=True)
    t.write_json(OUT/'final.json',dict(status='SCREEN_ONLY',results=results,require_full_51_source_42_native_61_control_209_outcome_qualification=True))

if __name__=='__main__':main()
