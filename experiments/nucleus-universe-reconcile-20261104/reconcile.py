"""Reconcile a newly earned source boundary; reuse only an identical executable."""
import copy
import importlib.util
import json
from pathlib import Path,PurePosixPath
import re
import shutil
import subprocess
import tarfile

ROOT=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('universe_parent',ROOT.parent/'nucleus-universe-records-20261104/qualify.py')
U=importlib.util.module_from_spec(spec);spec.loader.exec_module(U)
Q,C,t=U.Q,U.C,U.Q.t
OUT=Path('/tmp/nucleus-universe-reconciled')
PRIOR=Path('/tmp/universe-prior')
BINARY='adc2275242f93633bf143e61a0c80c946579d62a19c342bca3be3b7ee23d8f93'
PATCH='f22826104beae6ac23bb3b5169fc38882f07b4109ce0f224332ed04dc8c8162e'

def main():
    OUT.mkdir(exist_ok=True)
    q=json.loads((PRIOR/'qualification.json').read_text())['candidate']
    baseline=json.loads(Path('/tmp/nonzero-qualified/qualification.json').read_text())['candidate']
    assert q['binary_sha']==BINARY and q['source_patch_sha']==PATCH
    assert t.digest(PRIOR/'candidate/nucleus')==BINARY and t.digest(PRIOR/'candidate/source.patch')==PATCH
    assert baseline['qualified']and baseline['binary_sha']==U.BASE_SHA
    assert q['configuration']==baseline['configuration']
    assert q['controls_unchanged']and q['extra_unchanged']and not q['verdict_changes']
    assert len(q['controls'])==61 and all(row['pass_']for row in q['controls'])
    assert len(q['green'])==3 and q['green'][0]['rc']==0
    inherited=[]
    for name,count in [('universe_gate.json',13),('carrier_gate.json',14),('ac_gate.json',9),('differential.json',12)]:
        d=json.loads((PRIOR/name).read_text())
        assert d['candidate_binary']==BINARY and d['reference_binary']==C.REF_SHA
        assert len(d['rows'])==count and all(row['pass_']for row in d['rows'])
        inherited.append(dict(file=name,sha256=t.digest(PRIOR/name),cases=count,authority_run=41744081899,artifact=13282929137))
        shutil.copyfile(PRIOR/name,OUT/name)
    arm=OUT/'candidate';arm.mkdir()
    sealed=Path('/tmp/immutable-prior/baseline')
    assert t.digest(sealed/'source.tar.gz')=='252a8b53c29194dafbd89acbc734f9615da6e9a69d4cb4fcd075e6eef407269b'
    assert t.digest(sealed/'source-manifest.json')=='a9b6d814bcd8114dc3659e47b8a1c2cf702a91331ca44ae1ace5b169e6d8e46a'
    with tarfile.open(sealed/'source.tar.gz')as archive:archive.extractall(arm,filter='data')
    kernel=arm/'metatron-kernel'
    for name,sha in json.loads((sealed/'source-manifest.json').read_text()).items():
        path=PurePosixPath(name);assert not path.is_absolute()and '..'not in path.parts
        assert t.digest(kernel/name)==sha,name
    patches=[ROOT.parent/'nucleus-universe-records-20261104/universe-record.patch',ROOT.parent/'nucleus-universe-records-20261104/imax-upper-bound.patch']
    # Bind cfg(test) source too: production binary equality alone is weaker.
    assert t.digest(sealed/'source.patch')=='787e7daf338d3ae72f7786ffd26548696cb96f1c15f9d92b305f5bb4a1cc746c'
    reconstructed_patch=(sealed/'source.patch').read_bytes()+b''.join(p.read_bytes()for p in patches)
    assert reconstructed_patch==(PRIOR/'candidate/source.patch').read_bytes()
    for patch in patches:
        result=t.run_group(['patch','--batch','--fuzz=0','-p1','-i',str(patch)],cwd=arm,capture_output=True,timeout=30)
        assert result.returncode==0,(patch,result.stdout,result.stderr)
    before={str(p.relative_to(kernel)):t.digest(p)for p in kernel.rglob('*')if p.is_file()}
    patch=ROOT/'test-reconciliation.patch'
    result=t.run_group(['patch','--batch','--fuzz=0','-p1','-i',str(patch)],cwd=arm,capture_output=True,timeout=30)
    assert result.returncode==0,(result.stdout,result.stderr)
    after={str(p.relative_to(kernel)):t.digest(p)for p in kernel.rglob('*')if p.is_file()}
    changed={name for name in before.keys()|after.keys()if before.get(name)!=after.get(name)}
    assert changed=={'tests/end_to_end.rs'},changed
    (arm/'source.patch').write_text((PRIOR/'candidate/source.patch').read_text()+patch.read_text())
    t.write_json(arm/'source-manifest.json',after)
    with tarfile.open(arm/'source.tar.gz','w:gz')as archive:
        for name in sorted(after):archive.add(kernel/name,arcname='metatron-kernel/'+name)
    binary,build_env=t.build(kernel,arm)
    assert binary is not None and t.digest(binary)==BINARY,'Test-only reconciliation must retain the exact previously checked executable'
    env=Q.R.N.runtime(True)
    assert{k:v for k,v in env.items()if k.startswith('NUCLEUS_')}==q['configuration']
    reference=Path('/tmp/k-reference/bundle/kernel');reference.chmod(0o755);assert t.digest(reference)==C.REF_SHA
    C.OUT=OUT
    manifest=json.loads((ROOT/'inputs/manifest.json').read_text())
    C.check_controls(binary,manifest,ROOT/'inputs',env,'renamed_record_gate.json','renamed-record-differential')
    prior_native=q['native'];assert prior_native['compiled']and all(v['complete']for v in prior_native['targets'].values())
    key='end_to_end|test'
    assert prior_native['targets'][key]['failures']==['g15_shared_representation_earns_no_fourth_family']
    native_env=build_env|env|{'NUCLEUS_FROZEN196':'/tmp/current208/inputs'}
    result=t.run_group(['cargo','test','--release','--locked','--manifest-path',str(kernel/'Cargo.toml'),'--test','end_to_end','--','--include-ignored','--test-threads=1'],env=native_env,capture_output=True,timeout=900)
    raw=(result.stdout+result.stderr).decode(errors='replace');(arm/'native-end_to_end-test.log').write_text(raw)
    counts=re.findall(t.SUMMARY,raw)
    assert t.native_target_valid(result.returncode,raw)and result.returncode==0 and len(counts)==1
    counts=list(map(int,counts[0]));assert counts==[86,0,0,0,0],counts
    native=copy.deepcopy(prior_native)
    native['targets'][key]=dict(rc=0,complete=True,failures=[],counts=counts)
    assert Q.R.N.Q.native_nonregression(native,baseline['native'])
    q=copy.deepcopy(q);q.update(status='WARRANTED_BOUNDED',qualified=True,native=native,native_nonregression=True,source_patch_sha=t.digest(arm/'source.patch'),reconciliation=dict(prior_run=41744081899,artifact=13282929137,production_binary_unchanged=True,prior_test_source_binding='exact sealed-source manifest and exact prior cumulative patch composition',prior_patch_sha=PATCH,changed_sources=sorted(changed),fresh_native_targets=[key],reused_native_targets=sorted(set(native['targets'])-{key}),reused_source_controls=inherited,fresh_source_controls=3,prior_failure='g15_shared_representation_earns_no_fourth_family',official_valid_renamed_source='72349b3f424b4370e6aed5b55d9ee8aa4a026d02c7f3a2e4c5875053948d9184'))
    shutil.copyfile(PRIOR/'candidate/verdicts.json',arm/'verdicts.json')
    t.write_json(OUT/'qualification.json',dict(candidate=q))
    print('RECONCILED_QUALIFICATION',json.dumps(dict(qualified=True,binary_sha=BINARY,source_patch_sha=q['source_patch_sha'],reused_native_targets=41,fresh_native_targets=1,reused_source_controls=48,fresh_source_controls=3)),flush=True)
    full_source=Path('/tmp/mathlib.ndjson');assert t.digest(full_source)==t.INPUT_SHA
    result=t.measure(binary,full_source,env|{'NUCLEUS_TRACE_DOWNSTREAM':'1'},OUT/'full',timeout=1800,perf=False)
    traces=[line for line in(OUT/'full/stderr').read_text(errors='replace').splitlines()if line.startswith('NUCLEUS_DOWNSTREAM:')]
    terminal=traces[-1]if traces else None;frontier=None
    if result['rc']==2 and terminal:
        match=re.search(r'NUCLEUS_DOWNSTREAM:name=(.*?):stage=',terminal)
        if match and not match.group(1).startswith('<'):
            frontier=Q.R.E.extract(full_source,OUT/'next-frontier.ndjson',match.group(1))
            subprocess.run(['zstd','-T0','-3',str(OUT/'next-frontier.ndjson')],check=True)
            (OUT/'next-frontier.ndjson').unlink()
    full=dict(status='WARRANTED_BOUNDED_COMPLETE_MATHLIB'if result['rc']==0 else 'WARRANTED_BOUNDED_FIRST_FRONTIER'if result['rc']==2 else 'BLOCKED_FULL_INPUT_FAILURE',qualified=True,complete_mathlib_accept=result['rc']==0,source_sha=t.INPUT_SHA,binary_sha=BINARY,result=result,terminal=terminal,next_frontier=frontier,no_official_arena_score=True)
    t.write_json(OUT/'full.json',full);print('RECONCILED_MATHLIB',json.dumps(full),flush=True)
    shutil.rmtree(arm/'target',ignore_errors=True)

if __name__=='__main__':main()
