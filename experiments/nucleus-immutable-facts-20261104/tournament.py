"""Screen immutable-fact reuse, then fully qualify and pair the winning arm."""
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path, PurePosixPath
import shutil
import subprocess
import tarfile
import threading
from concurrent.futures import ThreadPoolExecutor

ROOT=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('carrier_qualification',ROOT.parent/'nucleus-nonzero-carrier-20261104/qualify.py')
I=importlib.util.module_from_spec(spec)
spec.loader.exec_module(I)
C,Q=I.C,I.Q
OUT=Path('/tmp/nucleus-immutable-tournament')
BASE_SHA='013e742dc3bf541301235b6e6d37615b62c9800b923b7c9506b254cffdbfe61e'
W=Path('/tmp/nonzero-qualified')

def materialize(directory,patches):
    directory.mkdir(parents=True,exist_ok=True)
    sealed=Path('/tmp/envfork-red')
    assert Q.t.digest(sealed/'qualified-source.tar.gz')=='71cf6f028111109cc6361cf44b1d91a3e5f26a098e0c9737c20b3ff3325d4c9d'
    with tarfile.open(sealed/'qualified-source.tar.gz')as archive:archive.extractall(directory,filter='data')
    kernel=directory/'metatron-kernel'
    for name,sha in json.loads((sealed/'source-manifest.json').read_text()).items():
        path=PurePosixPath(name)
        assert not path.is_absolute()and '..'not in path.parts
        assert Q.t.digest(kernel/name)==sha,name
    for patch in[ROOT.parent/'nucleus-nonzero-carrier-20261104/nonzero-carrier.patch',*patches]:
        result=Q.t.run_group(['patch','--batch','--fuzz=0','-p1','-i',str(patch)],cwd=directory,capture_output=True,timeout=30)
        with(directory/'patch.log').open('ab')as stream:stream.write(result.stdout+result.stderr)
        assert result.returncode==0,(patch,result.stdout,result.stderr)
    source=(W/'candidate/source.patch').read_text()+''.join(p.read_text()for p in patches)
    (directory/'source.patch').write_text(source)
    return kernel

def seal_source(kernel,arm):
    files=sorted(p for p in kernel.rglob('*')if p.is_file()and 'target'not in p.relative_to(kernel).parts)
    Q.t.write_json(arm/'source-manifest.json',{str(p.relative_to(kernel)):Q.t.digest(p)for p in files})
    with tarfile.open(arm/'source.tar.gz','w:gz',dereference=True)as archive:
        for p in files:archive.add(p,arcname='metatron-kernel/'+str(p.relative_to(kernel)))

def boundary(result,directory):
    lines=(directory/'stderr').read_text(errors='replace').splitlines()
    terminal=next((line for line in reversed(lines)if line.startswith('NUCLEUS_DOWNSTREAM:')),None)
    return result['rc'],terminal

def main():
    OUT.mkdir(exist_ok=True)
    baseline=json.loads((W/'qualification.json').read_text())['candidate']
    baseline_full=json.loads((W/'full.json').read_text())
    assert baseline['qualified']and baseline['binary_sha']==BASE_SHA
    env=Q.R.N.runtime(True)
    assert{k:v for k,v in env.items()if k.startswith('NUCLEUS_')}==baseline['configuration']
    traced=env|{'NUCLEUS_TRACE_DOWNSTREAM':'1'}
    original=W/'candidate/nucleus'
    assert Q.t.digest(original)==BASE_SHA
    original.chmod(0o755)
    kernel=materialize(OUT/'baseline',[])
    rebuilt,build_env=Q.t.build(kernel,OUT/'baseline')
    assert rebuilt is not None and Q.t.digest(rebuilt)==BASE_SHA,'Exact source reconstruction must reproduce the qualified executable'
    seal_source(kernel,OUT/'baseline')
    expected=(baseline_full['result']['rc'],baseline_full['terminal'])
    assert expected[0]in(0,2)
    source=Path('/tmp/mathlib.ndjson')
    assert Q.t.digest(source)==baseline_full['source_sha']==Q.t.INPUT_SHA
    rows=json.loads((W/'candidate/verdicts.json').read_text())
    manifest={x['case']:x for x in json.loads(Path('/tmp/current208/inputs-manifest.json').read_text())}
    selected=[row for row in rows if row['rc']in(0,1)or row['case']=='bugs/eta-ctor-alias']
    assert len(selected)==201
    arms={
        'run-flags':[ROOT/'run-flags.patch'],
        'level-digest':[ROOT/'cached-levels.patch'],
        'flags-plus-levels':[ROOT/'run-flags.patch',ROOT/'cached-levels.patch'],
        'environment-forks':[ROOT.parent/'nucleus-environment-forks-20261104/forked-constants.patch'],
    }
    candidates={}
    screens=[]
    for index,(label,patches)in enumerate(arms.items()):
        arm=OUT/label
        try:
            kernel=materialize(arm,patches)
            binary,build_env=Q.t.build(kernel,arm)
            assert binary is not None,'Compile failure is not a performance result'
            seal_source(kernel,arm)
            native=Q.t.run_group(['cargo','test','--release','--locked','--manifest-path',str(kernel/'Cargo.toml'),'--lib','--','--include-ignored','--test-threads=1'],env=build_env|env,capture_output=True,timeout=600)
            (arm/'lib.stdout').write_bytes(native.stdout)
            (arm/'lib.stderr').write_bytes(native.stderr)
            assert native.returncode==0 and b'0 failed; 0 ignored;'in native.stdout,'Library invariants must pass'
            def one(old):
                item=manifest[old['case']]
                assert item['sha256']==old['sha256']and item['expected']==old['expected']
                path=Path('/tmp/current208/inputs')/item['relative_path']
                assert Q.t.digest(path)==old['sha256']
                with path.open('rb')as stream:r=Q.t.run_group([str(binary)],stdin=stream,capture_output=True,env=env,timeout=240)
                return dict(case=old['case'],source_sha=old['sha256'],baseline_rc=old['rc'],candidate_rc=r.returncode,pass_=r.returncode==old['rc'])
            with ThreadPoolExecutor(max_workers=2)as pool:checks=list(pool.map(one,selected))
            Q.t.write_json(arm/'screen-verdicts.json',checks)
            assert all(x['pass_']for x in checks),'Screen corpus changed'
            measured={}
            for name,executable in([('baseline',original),('candidate',binary)]if index%2==0 else[('candidate',binary),('baseline',original)]):
                target=arm/('screen-'+name)
                result=Q.t.measure(executable,source,traced,target,timeout=1800,perf=False)
                assert boundary(result,target)==expected,'The measured verification boundary changed'
                measured[name]=result
            ratio=(measured['candidate']['user']+measured['candidate']['system'])/(measured['baseline']['user']+measured['baseline']['system'])
            screen=dict(arm=label,status='SCREEN_ONLY',binary_sha=Q.t.digest(binary),source_patch_sha=Q.t.digest(arm/'source.patch'),decisive_corpus=201,excluded_baseline_unknowns=7,ratio=ratio,result=measured)
            candidates[label]=(kernel,binary,build_env,arm)
        except AssertionError as error:
            screen=dict(arm=label,status='REJECTED_AT_SCREEN',reason=str(error))
        screens.append(screen)
        Q.t.write_json(OUT/'screens.json',screens)
        print('IMMUTABLE_FACT_SCREEN',json.dumps(screen),flush=True)
    eligible=[x for x in screens if x['status']=='SCREEN_ONLY'and x['ratio']<0.97]
    if not eligible:
        Q.t.write_json(OUT/'final.json',dict(status='NO_ARM_QUALIFIED_FOR_PROMOTION',screens=screens,no_official_rank_claim=True))
        for _,_,_,arm in candidates.values():shutil.rmtree(arm/'target',ignore_errors=True)
        return
    winner=min(eligible,key=lambda x:x['ratio'])['arm']
    selected_candidate=candidates[winner]
    C.OUT=OUT/'qualified-winner'
    C.OUT.mkdir(exist_ok=True)
    original_builder=Q.source_qualified_candidate
    original_capture=C.captured
    cache={row['sha256']:(row,W/'carrier-differential'/row['case'])for row in json.loads((W/'carrier_gate.json').read_text())['rows']}
    assert len(cache)==14
    reuse=[]
    lock=threading.Lock()
    def capture(command,target,**kwargs):
        if Path(command[0]).resolve()==Path('/tmp/k-reference/bundle/kernel'):
            assert Q.t.digest(Path(command[0]))==C.REF_SHA
            sha=Q.t.digest(Path(command[-1]))
            if sha in cache:
                row,directory=cache[sha]
                stage='parse'if '--parse-only'in command else 'reference'
                target.parent.mkdir(parents=True,exist_ok=True)
                for suffix in('.stdout','.stderr'):shutil.copyfile(directory/(stage+suffix),target.with_suffix(suffix))
                rc=row['reference_parse_rc']if stage=='parse'else row['reference_rc']
                with lock:
                    reuse.append(dict(source_sha=sha,stage=stage,rc=rc,authority_run=41733591868,artifact=13276734778,reference_binary=C.REF_SHA))
                    Q.t.write_json(C.OUT/'reused_parent_oracles.json',reuse)
                return rc
        return original_capture(command,target,**kwargs)
    Q.source_qualified_candidate=lambda unused:selected_candidate
    C.captured=capture
    try:
        I.main()
    finally:
        Q.source_qualified_candidate=original_builder
        C.captured=original_capture
    q=json.loads((C.OUT/'qualification.json').read_text())['candidate']
    assert q['qualified']and Q.R.N.Q.native_nonregression(q['native'],baseline['native'])
    full=json.loads((C.OUT/'full.json').read_text())
    assert(full['result']['rc'],full['terminal'])==expected
    pairs=[]
    for index,order in enumerate([('baseline','candidate'),('candidate','baseline'),('baseline','candidate')]):
        measured={}
        for name in order:
            target=OUT/'paired'/str(index)/name
            result=Q.t.measure(original if name=='baseline'else selected_candidate[1],source,traced,target,timeout=1800,perf=False)
            assert boundary(result,target)==expected
            measured[name]=result
        ratio=(measured['candidate']['user']+measured['candidate']['system'])/(measured['baseline']['user']+measured['baseline']['system'])
        pairs.append(dict(index=index,order=order,ratio=ratio,results=measured))
        Q.t.write_json(OUT/'pairs.json',pairs)
    geomean=math.exp(sum(math.log(x['ratio'])for x in pairs)/3)
    passed=geomean<0.95 and all(x['ratio']<1 for x in pairs)
    Q.t.write_json(OUT/'final.json',dict(status='WARRANTED_BOUNDED_PARTIAL_SPEEDUP'if passed else 'REJECTED_AS_SUFFICIENT_SPEEDUP',winner=winner,qualified=True,binary_sha=q['binary_sha'],source_patch_sha=q['source_patch_sha'],baseline_binary=BASE_SHA,geomean_total_cpu_ratio=geomean,pairs=pairs,boundary=expected,input_sha=Q.t.INPUT_SHA,complete_mathlib_accept=expected[0]==0,no_official_rank_claim=True))
    for _,_,_,arm in candidates.values():shutil.rmtree(arm/'target',ignore_errors=True)

if __name__=='__main__':
    main()
