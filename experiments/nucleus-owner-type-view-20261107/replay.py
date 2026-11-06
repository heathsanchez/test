#!/usr/bin/env python3
"""Reproduce a source-pinned Nucleus capture-budget transfer; no discovery claims."""
import argparse, concurrent.futures, hashlib, json, os, re, shutil, subprocess, tarfile, time, zipfile
from pathlib import Path

PARENT_SHA='701a10eb5f4ca3cf4f7ef1ea0caa9534bde26952d443a20e2bba89134559e262'
CORPUS_SHA='a9582eadc0d9893cbe39e6bcfccd79bfaec2032838851b8a487c35df16096763'
def digest(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def unpack(path, destination, expected):
    assert digest(path)==expected, 'artifact digest mismatch'
    with zipfile.ZipFile(path) as z:
        assert z.testzip() is None
        for entry in z.infolist():
            assert (destination/entry.filename).resolve().is_relative_to(destination.resolve())
        z.extractall(destination)
def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--parent-artifact',type=Path,required=True)
    ap.add_argument('--corpus-artifact',type=Path,required=True)
    ap.add_argument('--work',type=Path,required=True)
    a=ap.parse_args(); work=a.work.resolve(); work.mkdir(parents=True,exist_ok=False)
    here=Path(__file__).resolve().parent; t0=time.monotonic()
    unpack(a.parent_artifact,work/'parent',PARENT_SHA)
    unpack(a.corpus_artifact,work/'corpus',CORPUS_SHA)
    with tarfile.open(work/'parent/candidate/source.tar.gz') as t:t.extractall(work/'source',filter='data')
    with tarfile.open(work/'corpus/lean-arena-tests.tar.gz') as t:t.extractall(work/'inputs',filter='data')
    source=work/'source/metatron-kernel'
    for line in (work/'parent/reports/source.sha256').read_text().splitlines():
        sha,name=line.split(maxsplit=1); assert digest(work/'source'/name.strip())==sha
    shutil.copyfile(here/'owner_capture_transfer.rs',source/'tests/owner_capture_transfer.rs')
    flags=json.loads((work/'parent/flags.json').read_text())
    env={k:v for k,v in os.environ.items() if not k.startswith('NUCLEUS_')}
    env.update(flags);env.update(RUST_MIN_STACK='16777216',CARGO_BUILD_JOBS='2')
    def run(cmd,label,expected=0,target='candidate'):
        local={**env,'CARGO_TARGET_DIR':str(work/('target-'+target))}
        with (work/(label+'.log')).open('w') as log:
            p=subprocess.run(cmd,cwd=source,env=local,stdout=log,stderr=subprocess.STDOUT,timeout=1800)
        assert p.returncode==expected,(label,p.returncode)
        return (work/(label+'.log')).read_text()
    red=run(['cargo','test','--locked','--features','diagnostics','--test','owner_capture_transfer'],'red',101,'parent')
    assert 'a_source_pi_converts_to_its_semantic_pi_with_sufficient_owner_work ... FAILED' in red
    assert 'rigid-type-constructor-mismatch' in red
    with (here/'transfer.patch').open() as patch:
        subprocess.run(['patch','--fuzz=0','-p1'],cwd=source,stdin=patch,check=True)
    native=run(['cargo','test','--locked','--features','diagnostics'],'native')
    totals=[tuple(map(int,m)) for m in re.findall(r'test result: ok\. (\d+) passed; (\d+) failed; (\d+) ignored',native)]
    assert totals and sum(x[1] for x in totals)==0
    run(['cargo','build','--locked','--release','--features','diagnostics','--bin','metatron-kernel'],'release')
    binary=work/'target-candidate/release/metatron-kernel'
    expected={x['case'].split('/',1)[1]:x for x in json.loads((work/'parent/reports/authoritative-parity.json').read_text()) if x['case'].startswith('arena207/')}
    def case(p):
        name=str(p.relative_to(work/'inputs')); old=expected[name]; h=digest(p); assert h==old['input_sha256']
        with p.open('rb') as f:r=subprocess.run([str(binary)],stdin=f,stdout=subprocess.PIPE,stderr=subprocess.PIPE,env=env,timeout=180)
        return dict(case=name,input_sha256=h,old=old['new'],new=r.returncode,expected=old['expected'])
    inputs=sorted((work/'inputs').rglob('*.ndjson'));assert len(inputs)==207
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:rows=list(pool.map(case,inputs))
    (work/'corpus.json').write_text(json.dumps(rows,indent=2))
    assert all(x['old']==x['new'] for x in rows),'corpus changed: investigate before promotion'
    # Negative control: bypass only this guard, in a separate build directory.
    p=source/'src/convert.rs'; candidate=p.read_text()
    old='            *remaining -= allowance - opening_budget;\n            if !safe { return None; }'
    assert candidate.count(old)==1
    try:
        p.write_text(candidate.replace(old,old.replace('if !safe','if false && !safe')))
        mutant=run(['cargo','test','--locked','--features','diagnostics','--test','owner_capture_transfer','a_real_capture_collision','--','--nocapture'],'guard-ablation',101,'guard-ablation')
        assert 'capture guard must remain mandatory: Proven' in mutant
    finally:p.write_text(candidate)
    receipt=dict(schema='nucleus.capture-transfer.v1',status='WARRANTED_BOUNDED_MECHANICS',
        source_run=42230809276,source_commit='172553e51028bad98d7c0d86abc72affd54c1004',
        source_artifact=13510395400,source_artifact_sha256=PARENT_SHA,
        patch_sha256=digest(here/'transfer.patch'),tests_sha256=digest(here/'owner_capture_transfer.rs'),
        binary_sha256=digest(binary),passed=sum(x[0] for x in totals),ignored=sum(x[2] for x in totals),
        corpus_cases=len(rows),corpus_changes=0,guard_ablation='DETECTED_UNSAFE_PROVEN',
        elapsed_seconds=time.monotonic()-t0,
        boundary='Constructed representation-transfer regression and exact 207-corpus parity; not independent held-out task discovery, six-case closure, full Mathlib, speedup or exponential improvement.')
    (work/'receipt.json').write_text(json.dumps(receipt,indent=2));print(json.dumps(receipt,indent=2))
if __name__=='__main__': main()
