"""Hash-bound live Arena census; reuse identical historical checks, run only deltas."""
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import subprocess
import tarfile
import time
from urllib.request import Request, urlopen

OUT = Path('/tmp/nucleus-current-census')
PRIOR = Path('/tmp/k-qualified')

def digest(data):
    return hashlib.sha256(data).hexdigest()

def save(name, value):
    (OUT / name).write_text(json.dumps(value, indent=2) + '\n')

def download(name, limit):
    with urlopen(Request('https://arena.lean-lang.org/' + name, headers={'User-Agent':'Nucleus-source-census'}),timeout=60) as response:
        raw = response.read(limit + 1)
    assert len(raw) <= limit
    (OUT / name).write_bytes(raw)
    return raw

def main():
    OUT.mkdir(exist_ok=True)
    prior = json.loads((PRIOR / 'qualification.json').read_text())['candidate']
    assert prior['qualified'] and prior['binary_sha'] == '16fbebdd703494f5dd1b8e0feb713cf9db06452a403a0db2cf250898708768d1'
    binary = PRIOR / 'candidate/nucleus'
    assert digest(binary.read_bytes()) == prior['binary_sha']
    binary.chmod(0o755)
    historical = {x['case']:x for x in json.loads((PRIOR / 'candidate/verdicts.json').read_text())}
    assert len(historical) == 208
    full = json.loads((PRIOR / 'full.json').read_text())
    assert full['binary_sha']==prior['binary_sha']
    historical['mathlib']=dict(sha256=full['source_sha'],expected=0,rc=full['result']['rc'])
    previous=Path('/tmp/prior-census')
    previous_summary=json.loads((previous/'summary.json').read_text())
    assert previous_summary['binary_sha256']==prior['binary_sha']
    assert previous_summary['configuration']==prior['configuration']
    for row in json.loads((previous/'rows.json').read_text()):
        if row['expected'] in (0,1) and row['rc'] in (0,1,2):
            old=historical.get(row['case'])
            if old and old['sha256']==row['sha256']:
                assert old['expected']==row['expected'] and old['rc']==row['rc']
            historical[row['case']]=row
    raw = download('results.json',32_000_000)
    data = json.loads(raw)
    tests = {x['name']:x for x in data['tests']}
    assert len(tests) == len(data['tests']) and len(tests)>200
    archive = download('lean-arena-tests.tar.gz',32_000_000)
    exported = {}
    with tarfile.open(OUT / 'lean-arena-tests.tar.gz','r:gz') as tar:
        members = tar.getmembers()
        assert len(members)<4096 and sum(x.size for x in members)<512_000_000
        for member in members:
            path = PurePosixPath(member.name)
            assert not path.is_absolute() and '..' not in path.parts
            if member.isdir():
                continue
            assert member.isfile() and 0<member.size<=10_485_760
            assert path.parts[0] in ('good','bad') and path.suffix=='.ndjson'
            name = str(PurePosixPath(*path.parts[1:]).with_suffix(''))
            assert name in tests and name not in exported
            subject = tar.extractfile(member).read()
            test = tests[name]
            assert len(subject)==test['size'] and digest(subject)==test['sha256'], name
            expected = 'accept' if path.parts[0]=='good' else 'reject'
            assert test['outcome']==expected, name
            exported[name] = subject
    rows=[]
    for name,test in sorted(tests.items()):
        old = historical.get(name)
        expected = {'accept':0,'reject':1}.get(test.get('outcome'))
        row = dict(case=name,sha256=test.get('sha256'),size=test.get('size'),expected=expected,
                   old_sha256=old['sha256'] if old else None)
        if old and old['sha256']==test.get('sha256') and old['expected']==expected:
            row.update(authority='EXACT_PRIOR_SAME_BINARY_SOURCE_CONFIGURATION',rc=old['rc'])
        elif name in exported:
            try:
                result = subprocess.run([str(binary)],input=exported[name],capture_output=True,
                    env=dict(os.environ,**prior['configuration']),timeout=60)
                rc = result.returncode
                target=OUT/'fresh'/name
                target.parent.mkdir(parents=True,exist_ok=True)
                Path(str(target)+'.stdout').write_bytes(result.stdout)
                Path(str(target)+'.stderr').write_bytes(result.stderr)
                row.update(authority='FRESH_CURRENT_BYTES',rc=rc)
            except subprocess.TimeoutExpired:
                row.update(authority='FRESH_CURRENT_BYTES_TIMEOUT',rc=None)
        else:
            row.update(authority='UNKNOWN_NO_CURRENT_BYTES',rc=None)
        row['correct'] = row['rc']==expected if expected is not None and row['rc'] in (0,1) else None
        rows.append(row)
        save('rows.json',rows)
    summary=dict(schema='nucleus-current-arena-census-v1',snapshot_unix=time.time(),
        results_sha256=digest(raw),archive_sha256=digest(archive),publisher_meta=data.get('meta'),
        binary_sha256=prior['binary_sha'],configuration=prior['configuration'],
        test_count=len(tests),published_export_count=len(exported),
        reused=sum(x['authority'].startswith('EXACT_PRIOR')for x in rows),
        fresh=sum(x['authority'].startswith('FRESH_')for x in rows),
        missing=sum(x['authority']=='UNKNOWN_NO_CURRENT_BYTES'for x in rows),
        false_accepts=[x for x in rows if x['expected']==1 and x['rc']==0],
        false_rejects=[x for x in rows if x['expected']==0 and x['rc']==1],
        new_or_changed=[x for x in rows if x['old_sha256']!=x['sha256']],
        removed_historical=sorted(set(historical)-set(tests)),
        mathlib_results=[x for x in data['results'] if x.get('test')=='mathlib'],
        no_full_mathlib_or_official_rank_claim=True)
    save('summary.json',summary)
    print(json.dumps({k:v for k,v in summary.items()if k not in ('mathlib_results','configuration','new_or_changed')}),flush=True)

if __name__=='__main__':
    main()
