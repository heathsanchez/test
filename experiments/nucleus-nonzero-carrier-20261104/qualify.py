"""Bounded source-derived nonzero carriers; retain prior qualification gates."""
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import threading

ROOT=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('ac_qualification',ROOT.parent/'nucleus-ac-sort-20261104/qualify.py')
A=importlib.util.module_from_spec(spec)
spec.loader.exec_module(A)
C,Q=A.C,A.Q
C.OUT=Path('/tmp/nucleus-nonzero-carrier-qualified')
SOURCE_SHA='e7daddaf05fa799dc248bb3f10a502fd5ab5569561a4502d9f48de63256f3113'
BASE_SHA='582dd0ac17d664202a39ee7daa69b640f33916374fc44dbefdc96a37e8bcb238'

def gate(binary,env):
    source=Path('/tmp/information-prefix.ndjson')
    assert Q.t.digest(source)==SOURCE_SHA
    prior=json.loads(Path('/tmp/ac-qualified/qualification.json').read_text())['candidate']
    assert prior['qualified'] and prior['binary_sha']==BASE_SHA
    baseline=Path('/tmp/ac-qualified/candidate/nucleus')
    assert Q.t.digest(baseline)==BASE_SHA and Q.t.digest(binary)!=BASE_SHA
    baseline.chmod(0o755)
    red=Q.t.measure(baseline,source,env,C.OUT/'red-information',timeout=180,perf=False)
    assert red['rc']==2 and 'Lean.Data.AC.ContextInformation'in(C.OUT/'red-information/stderr').read_text()
    cases=C.OUT/'carrier-inputs'
    subprocess.run(['python3',str(C.ROOT/'generate.py'),'--source',str(source),'--out',str(cases),'--information'],check=True)
    manifest=json.loads((cases/'inputs.json').read_text())
    assert len(manifest)==14
    reference=Path('/tmp/k-reference/bundle/kernel')
    assert Q.t.digest(reference)==C.REF_SHA
    C.check_controls(binary,manifest,cases,env,'carrier_gate.json','carrier-differential',dict(red=red))
    A.gate(binary,env)

def main():
    C.OUT.mkdir(exist_ok=True)
    prior=Path('/tmp/ac-qualified')
    controls=json.loads((prior/'differential.json').read_text())
    assert controls['reference_binary']==C.REF_SHA
    cache={}
    for row in controls['rows']:
        assert row['pass_']
        cache[row['sha256']]=(row,prior/'differential'/row['case'])
    for row in json.loads((prior/'ac_gate.json').read_text())['rows']:
        assert row['pass_']
        cache[row['sha256']]=(row,prior/'ac-differential'/row['case'])
    assert len(cache)==21
    original=C.captured
    reused=[]
    cache_lock=threading.Lock()
    def cached_oracle(command,target,**kwargs):
        if Path(command[0]).resolve()==Path('/tmp/k-reference/bundle/kernel'):
            assert Q.t.digest(Path(command[0]))==C.REF_SHA
            sha=Q.t.digest(Path(command[-1]))
            if sha in cache:
                row,directory=cache[sha]
                stage='parse'if '--parse-only'in command else 'reference'
                target.parent.mkdir(parents=True,exist_ok=True)
                for suffix in('.stdout','.stderr'):
                    shutil.copyfile(directory/(stage+suffix),target.with_suffix(suffix))
                rc=row['reference_parse_rc']if stage=='parse'else row['reference_rc']
                with cache_lock:
                    reused.append(dict(source_sha=sha,stage=stage,rc=rc,reference_binary=C.REF_SHA,authority_run=41728727910,artifact=13276242300))
                    Q.t.write_json(C.OUT/'reused_oracles.json',reused)
                return rc
        return original(command,target,**kwargs)
    C.captured=cached_oracle
    try:
        C.main(additional_patch=ROOT/'combined.patch',additional_gate=gate)
    finally:
        C.captured=original
    qualified=json.loads((C.OUT/'qualification.json').read_text())['candidate']
    assert qualified['qualified']
    Q.t.write_json(C.OUT/'carrier_qualification.json',dict(status='WARRANTED_BOUNDED',
        carrier_controls=14,retained_controls=21,reused_oracle_calls=len(reused),
        binary_sha=qualified['binary_sha'],source_patch_sha=qualified['source_patch_sha'],
        full=json.loads((C.OUT/'full.json').read_text())))

if __name__=='__main__':
    main()
