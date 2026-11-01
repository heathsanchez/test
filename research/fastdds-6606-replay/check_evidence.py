#!/usr/bin/env python3
"""Independently validate the raw two-arm replay artifacts, including same-report race attribution."""
import argparse, hashlib, json, pathlib, re
p=argparse.ArgumentParser(); p.add_argument('root'); a=p.parse_args()
root=pathlib.Path(a.root)
expected={'baseline':('b9e087308b4ef02f2c8c8982abaf8286166f8457','3ea5706b773be63000cfc57d3dcd69f1e9975ca3'),
          'candidate':('2352189bb628adff80b86e52ec4257b2ea003318','18633fbd6b8f1f9575fe6165786b2e2478effa55')}
report={'arms':{}}; fixtures={}
for arm,(sha,tree) in expected.items():
    d=root/arm
    lines=(d/'source-and-environment.txt').read_text().splitlines()
    assert lines[:2]==[sha,tree], (arm,lines[:2])
    assert 'SANITIZER:BOOL=THREAD' in (d/'CMakeCache.txt').read_text()
    fixtures[arm]=hashlib.sha256((d/'regression.cpp').read_bytes()).hexdigest()
    results=json.loads((d/arm/'results.json').read_text()); assert len(results)==5
    assert [r['trial'] for r in results]==list(range(5))
    target_reports=[]
    for r in results:
        assert r['label']==arm and not r['timeout'] and r['mapped_ok']
        assert len(r['mapped_libraries'])==2
        assert all('build-dds/src/cpp/libfastdds.so' in path for ps in r['mapped_libraries'].values() for path in ps)
        logs='\n'.join(f.read_text(errors='replace') for f in (d/arm).glob(f"tsan-{r['trial']}.*"))
        reports=re.split(r'(?m)^={10,}\s*$',logs)
        hits=[x for x in reports if 'WARNING: ThreadSanitizer: data race' in x and 'TypeLookupManager' in x]
        target_reports.extend(hits)
        if arm=='candidate':
            assert r['writers']==200 and r['resolved_types']==200 and set(r['exits'].values())=={0}
            assert 'WARNING: ThreadSanitizer:' not in logs and 'FATAL: ThreadSanitizer:' not in logs
        else:
            assert all(x in (0,66) for x in r['exits'].values())
    if arm=='baseline': assert target_reports, 'No same-report TypeLookup race witness'
    report['arms'][arm]={'source_sha':sha,'source_tree':tree,'trials':5,'same_report_typelookup_races':len(target_reports),'outcomes':results}
assert fixtures['baseline']==fixtures['candidate']
neg=root/'candidate'/'negative-control'
r=json.loads((neg/'results.json').read_text()); assert len(r)==1
r=r[0]; assert not r['timeout'] and r['mapped_ok'] and r['writers']==200 and r['resolved_types']==0
assert r['exits']=={'discover':1,'announce':0}
logs='\n'.join(f.read_text(errors='replace') for f in neg.glob('tsan-*'))
assert 'WARNING: ThreadSanitizer:' not in logs and 'FATAL: ThreadSanitizer:' not in logs
assert 'xtypes::TypeIdentifier{},' in (root/'candidate'/'negative.cpp').read_text()
report.update({'passed':True,'identical_workload_sha256':fixtures['candidate'],'negative_control':r,
               'boundary':'Five trials per arm; aggregate callback counts, no independent distinct-type census; unsuppressed TSan, not exhaustive race freedom.'})
(root/'independent-review.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'passed':True,'target_baseline_reports':report['arms']['baseline']['same_report_typelookup_races'],'candidate_trials':5,'candidate_resolution_observations':1000,'negative_resolutions':0}))
