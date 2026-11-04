"""Screen exact canonical parse paths, qualify the best repeated winner."""
import importlib.util
import json
from pathlib import Path,PurePosixPath
import shutil
import tarfile
from concurrent.futures import ThreadPoolExecutor
ROOT=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('performance_gates',ROOT.parent/'nucleus-performance-gates-20261104/gate.py')
G=importlib.util.module_from_spec(spec);spec.loader.exec_module(G)
Q=G.Q
OUT=Path('/tmp/nucleus-canonical-parser')
W=Path('/tmp/qualified-stack')
BASE_SHA='a1d903c6ddf1219a7202db87f14ac3de82a344383501251c928a2a19683e621f'
def materialize(directory,patches):
 directory.mkdir(parents=True,exist_ok=True)
 assert Q.t.digest(W/'candidate/source.tar.gz')=='43418750f5972fc8ffe4451c3f0b63270f01d7f00ff29ac1bd68f88261b99fff'
 assert Q.t.digest(W/'candidate/source-manifest.json')=='89a6ac5c38951f3959f71c815a6f31884b0a7ed235602791fb1d5f068348ec7b'
 with tarfile.open(W/'candidate/source.tar.gz')as archive:archive.extractall(directory,filter='data')
 kernel=directory/'metatron-kernel'
 for name,sha in json.loads((W/'candidate/source-manifest.json').read_text()).items():
  path=PurePosixPath(name);assert not path.is_absolute()and '..'not in path.parts
  assert Q.t.digest(kernel/name)==sha,name
 for patch in patches:
  result=Q.t.run_group(['patch','--batch','--fuzz=0','-p1','-i',str(patch)],cwd=directory,capture_output=True,timeout=30)
  (directory/'patch.log').write_bytes(result.stdout+result.stderr)
  assert result.returncode==0,(patch,result.stdout,result.stderr)
 (directory/'source.patch').write_bytes((W/'candidate/source.patch').read_bytes()+b''.join(p.read_bytes()for p in patches))
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

def library_invariants(kernel,build_env,env,arm):
    # Match the established complete native harness, including its external
    # frozen source fixture and deliberately ignored boundary controls.
    library_env=build_env|env|{'NUCLEUS_FROZEN196':'/tmp/current208/inputs'}
    native=Q.t.run_group(['cargo','test','--release','--locked','--manifest-path',str(kernel/'Cargo.toml'),'--lib','--','--include-ignored','--test-threads=1'],env=library_env,capture_output=True,timeout=600)
    (arm/'lib.stdout').write_bytes(native.stdout)
    (arm/'lib.stderr').write_bytes(native.stderr)
    assert native.returncode==0 and b'0 failed; 0 ignored;'in native.stdout,'Library invariants must pass'

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
    expected=(baseline_full['result']['rc'],baseline_full['terminal'])
    assert expected[0]in(0,2)
    source=Path('/tmp/mathlib.ndjson')
    assert Q.t.digest(source)==baseline_full['source_sha']==Q.t.INPUT_SHA
    rows=json.loads((W/'candidate/verdicts.json').read_text())
    manifest={x['case']:x for x in json.loads(Path('/tmp/current208/inputs-manifest.json').read_text())}
    selected=[row for row in rows if row['rc']in(0,1)or row['case']=='bugs/eta-ctor-alias']
    assert len(selected)==201
    arms={label:[ROOT/(label+'.patch')]for label in ['numeric','names','combined']}
    candidates={}
    screens=[]
    for index,(label,patches)in enumerate(arms.items()):
        arm=OUT/label
        try:
            kernel=materialize(arm,patches)
            binary,build_env=Q.t.build(kernel,arm)
            assert binary is not None,'Compile failure is not a performance result'
            seal_source(kernel,arm)
            library_invariants(kernel,build_env,env,arm)
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
        print('CANONICAL_PARSER_SCREEN',json.dumps(screen),flush=True)
    eligible=[x for x in screens if x['status']=='SCREEN_ONLY'and x['ratio']<0.97]
    if not eligible:
        Q.t.write_json(OUT/'final.json',dict(status='NO_ARM_QUALIFIED_FOR_PROMOTION',screens=screens,no_official_rank_claim=True))
        for _,_,_,arm in candidates.values():shutil.rmtree(arm/'target',ignore_errors=True)
        return
    winner=min(eligible,key=lambda x:x['ratio'])['arm']
    selected_candidate=candidates[winner]
    result=G.qualify_and_pair(selected_candidate,W,OUT/'qualified-winner')
    Q.t.write_json(OUT/'final.json',result|dict(winner=winner,screens=screens))
    for _,_,_,arm in candidates.values():shutil.rmtree(arm/'target',ignore_errors=True)
if __name__=='__main__':main()
