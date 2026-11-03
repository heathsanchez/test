"""Several owner universes through the existing fully typed record validator."""
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import threading

ROOT=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('nonzero_carrier',ROOT.parent/'nucleus-nonzero-carrier-20261104/qualify.py')
I=importlib.util.module_from_spec(spec)
spec.loader.exec_module(I)
C,Q=I.C,I.Q
C.OUT=Path('/tmp/nucleus-universe-record-qualified')
SOURCE_SHA='f37e9434b2cee5f9623a2218fb6418c58d43dbe5ac3582cadd9cc844dfa215b4'
BASE_SHA='013e742dc3bf541301235b6e6d37615b62c9800b923b7c9506b254cffdbfe61e'

def new_gate(binary,env):
    prior=Path('/tmp/nonzero-qualified')
    q=json.loads((prior/'qualification.json').read_text())['candidate']
    assert q['qualified']and q['binary_sha']==BASE_SHA
    baseline=prior/'candidate/nucleus'
    assert Q.t.digest(baseline)==BASE_SHA
    baseline.chmod(0o755)
    source=Path('/tmp/evaluation-prefix.ndjson')
    assert Q.t.digest(source)==SOURCE_SHA
    red=Q.t.measure(baseline,source,env,C.OUT/'red-evaluation',timeout=180,perf=False)
    assert red['rc']==2 and 'Lean.Data.AC.EvalInformation'in(C.OUT/'red-evaluation/stderr').read_text()
    cases=C.OUT/'universe-inputs'
    subprocess.run(['python3',str(C.ROOT/'generate.py'),'--source',str(source),'--out',str(cases),'--evaluation'],check=True)
    manifest=json.loads((cases/'inputs.json').read_text())
    assert len(manifest)==13
    C.check_controls(binary,manifest,cases,env,'universe_gate.json','universe-differential',dict(red=red))

def main():
    C.OUT.mkdir(exist_ok=True)
    prior=Path('/tmp/nonzero-qualified')
    report=json.loads((prior/'carrier_gate.json').read_text())
    assert report['reference_binary']==C.REF_SHA
    cache={row['sha256']:(row,prior/'carrier-differential'/row['case'])for row in report['rows']}
    assert len(cache)==14 and all(row['pass_']for row,_ in cache.values())
    original_capture=C.captured
    original_gate=I.gate
    original_root=I.ROOT
    reused=[]
    lock=threading.Lock()
    def capture(command,target,**kwargs):
        if Path(command[0]).resolve()==Path('/tmp/k-reference/bundle/kernel'):
            assert Q.t.digest(Path(command[0]))==C.REF_SHA
            source_sha=Q.t.digest(Path(command[-1]))
            if source_sha in cache:
                row,directory=cache[source_sha]
                stage='parse'if '--parse-only'in command else 'reference'
                target.parent.mkdir(parents=True,exist_ok=True)
                for suffix in('.stdout','.stderr'):shutil.copyfile(directory/(stage+suffix),target.with_suffix(suffix))
                rc=row['reference_parse_rc']if stage=='parse'else row['reference_rc']
                with lock:
                    reused.append(dict(source_sha=source_sha,stage=stage,rc=rc,reference_binary=C.REF_SHA,authority_run=41733591868,artifact=13276734778))
                    Q.t.write_json(C.OUT/'reused_parent_oracles.json',reused)
                return rc
        return original_capture(command,target,**kwargs)
    def all_gates(binary,env):
        new_gate(binary,env)
        original_gate(binary,env)
    C.captured=capture
    I.gate=all_gates
    I.ROOT=ROOT
    try:
        I.main()
    finally:
        C.captured=original_capture
        I.gate=original_gate
        I.ROOT=original_root
    q=json.loads((C.OUT/'qualification.json').read_text())['candidate']
    assert q['qualified']
    Q.t.write_json(C.OUT/'universe_qualification.json',dict(status='WARRANTED_BOUNDED',
        new_controls=13,retained_controls=35,reused_parent_oracle_calls=len(reused),
        binary_sha=q['binary_sha'],source_patch_sha=q['source_patch_sha'],
        full=json.loads((C.OUT/'full.json').read_text())))

if __name__=='__main__':
    main()
