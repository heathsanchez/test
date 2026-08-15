from pathlib import Path
import json, statistics, subprocess, time

root=Path.cwd()
out=root/'results/a2-profile'
out.mkdir(parents=True,exist_ok=True)
bin=root/'a2/target/release/sokonanoda'
cfg=root/'a2/config.json'

def status(rc): return 'accept' if rc==0 else ('decline' if rc==2 else 'reject')

rows=[]
for kind,expected in [('good','accept'),('bad','reject')]:
    for p in sorted((root/'arena-tests'/kind).rglob('*.ndjson')):
        samples=[]; statuses=[]
        for _ in range(3):
            t=time.perf_counter()
            with p.open('rb') as f:
                rc=subprocess.run([str(bin),str(cfg)],stdin=f,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL).returncode
            samples.append(time.perf_counter()-t); statuses.append(status(rc))
        rows.append({
            'file':str(p.relative_to(root/'arena-tests')),
            'expected':expected,
            'statuses':statuses,
            'median_wall_s':statistics.median(samples),
            'samples_wall_s':samples,
            'size_bytes':p.stat().st_size,
        })

bad=[r for r in rows if any(x!=r['expected'] for x in r['statuses'])]
ranked=sorted(rows,key=lambda r:r['median_wall_s'],reverse=True)
summary={'case_count':len(rows),'semantic_failures':bad,'top20':ranked[:20],'all_cases':rows}
(out/'per_case.json').write_text(json.dumps(summary,indent=2,sort_keys=True))
print(json.dumps({'case_count':len(rows),'semantic_failure_count':len(bad),'top20':ranked[:20]},indent=2))
if bad: raise SystemExit('semantic failure in A2 profile')
