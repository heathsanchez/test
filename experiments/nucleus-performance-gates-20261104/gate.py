"""Qualify composition of independently earned source and immutable-fact changes."""
import importlib.util
import json
import math
from pathlib import Path,PurePosixPath
import shutil
import tarfile
import threading

ROOT=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('universe_parent',ROOT.parent/'nucleus-universe-records-20261104/qualify.py')
U=importlib.util.module_from_spec(spec);spec.loader.exec_module(U)
C,Q,t=U.C,U.Q,U.Q.t
OUT=Path('/tmp/nucleus-qualified-stack')
BASE=Path('/tmp/universe-qualified')

def qualify_and_pair(selected,baseline_directory,output):
    BASE=Path(baseline_directory);OUT=Path(output);OUT.mkdir(parents=True,exist_ok=True)
    kernel,binary,build_env,arm=selected
    baseline=json.loads((BASE/'qualification.json').read_text())['candidate']
    assert baseline['qualified']and t.digest(BASE/'candidate/nucleus')==baseline['binary_sha']
    assert len(baseline['native']['targets'])==42 and len(baseline['controls'])==61
    env=Q.R.N.runtime(True)
    assert{k:v for k,v in env.items()if k.startswith('NUCLEUS_')}==baseline['configuration']
    cache={}
    for file,directory,root in [('universe_gate.json','universe-differential',Path('/tmp/universe-prior')),('renamed_record_gate.json','renamed-record-differential',BASE)]:
        data=json.loads((root/file).read_text());assert data['reference_binary']==C.REF_SHA
        for row in data['rows']:
            assert row['pass_'];cache[row['sha256']]=(row,root/directory/row['case'],41744081899 if file=='universe_gate.json'else 41747021024)
    assert len(cache)==16
    original_capture=C.captured;original_builder=Q.source_qualified_candidate;original_gate=U.new_gate
    reused=[];lock=threading.Lock()
    def captured(command,target,**kwargs):
        if Path(command[0]).resolve()==Path('/tmp/k-reference/bundle/kernel'):
            assert t.digest(Path(command[0]))==C.REF_SHA
            sha=t.digest(Path(command[-1]))
            if sha in cache:
                row,directory,authority=cache[sha];stage='parse'if '--parse-only'in command else'reference'
                target.parent.mkdir(parents=True,exist_ok=True)
                for suffix in ['.stdout','.stderr']:shutil.copyfile(directory/(stage+suffix),target.with_suffix(suffix))
                rc=row['reference_parse_rc']if stage=='parse'else row['reference_rc']
                with lock:
                    reused.append(dict(source_sha=sha,stage=stage,rc=rc,authority_run=authority))
                    t.write_json(OUT/'reused_universe_oracles.json',reused)
                return rc
        return original_capture(command,target,**kwargs)
    def gate(binary,env):
        C.check_controls(binary,json.loads((ROOT.parent/'nucleus-universe-reconcile-20261104/inputs/manifest.json').read_text()),ROOT.parent/'nucleus-universe-reconcile-20261104/inputs',env,'renamed_record_gate.json','renamed-record-differential')
        original_gate(binary,env)
    C.OUT=OUT;C.captured=captured;Q.source_qualified_candidate=lambda unused:(kernel,binary,build_env,arm);U.new_gate=gate
    try:U.main()
    finally:C.captured=original_capture;Q.source_qualified_candidate=original_builder;U.new_gate=original_gate
    q=json.loads((OUT/'qualification.json').read_text())['candidate']
    assert q['qualified']and Q.R.N.Q.native_nonregression(q['native'],baseline['native'])
    full=json.loads((OUT/'full.json').read_text());base_full=json.loads((BASE/'full.json').read_text())
    expected=(base_full['result']['rc'],base_full['terminal']);assert(full['result']['rc'],full['terminal'])==expected
    original=BASE/'candidate/nucleus';assert t.digest(original)==baseline['binary_sha'];original.chmod(0o755)
    source=Path('/tmp/mathlib.ndjson');assert t.digest(source)==t.INPUT_SHA
    paired=[]
    for index,order in enumerate([('baseline','candidate'),('candidate','baseline'),('baseline','candidate')]):
        measured={}
        for label in order:
            directory=OUT/'paired'/str(index)/label
            result=t.measure(original if label=='baseline'else binary,source,env|{'NUCLEUS_TRACE_DOWNSTREAM':'1'},directory,timeout=1800,perf=False)
            terminal=[line for line in(directory/'stderr').read_text().splitlines()if line.startswith('NUCLEUS_DOWNSTREAM:')]
            assert(result['rc'],terminal[-1]if terminal else None)==expected
            measured[label]=result
        ratio=(measured['candidate']['user']+measured['candidate']['system'])/(measured['baseline']['user']+measured['baseline']['system'])
        paired.append(dict(index=index,order=order,ratio=ratio,results=measured));t.write_json(OUT/'pairs.json',paired)
    geomean=math.exp(sum(math.log(x['ratio'])for x in paired)/3)
    t.write_json(OUT/'stack.json',dict(status='WARRANTED_BOUNDED_PARTIAL_SPEEDUP'if geomean<.95 and all(x['ratio']<1 for x in paired)else'QUALIFIED_COMPOSITION_SPEEDUP_NOT_WARRANTED',qualified=True,baseline_binary=baseline['binary_sha'],binary_sha=q['binary_sha'],source_patch_sha=q['source_patch_sha'],geomean_total_cpu_ratio=geomean,pairs=paired,source_controls=51,native_targets=42,input_sha=t.INPUT_SHA,boundary=expected,complete_mathlib_accept=full['complete_mathlib_accept'],no_official_rank_claim=True))
    canonical=OUT/'candidate';canonical.mkdir(exist_ok=True)
    if canonical.resolve()!=arm.resolve():
        for name in ['nucleus','source.patch','source-manifest.json','source.tar.gz','verdicts.json','native-targets.json']:
            shutil.copyfile(arm/name,canonical/name)
        for path in arm.glob('native-*.log'):shutil.copyfile(path,canonical/path.name)
    shutil.rmtree(arm/'target',ignore_errors=True)
    return json.loads((OUT/'stack.json').read_text())
