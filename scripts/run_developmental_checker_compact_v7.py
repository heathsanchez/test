#!/usr/bin/env python3
from pathlib import Path
import collections,json,re,statistics,subprocess,time
root=Path.cwd(); out=root/'results/developmental-checker-compact-v7'; out.mkdir(parents=True,exist_ok=True)
B=root/'baseline/target/release/sokonanoda'; T=root/'trace/target/release/sokonanoda'
BC=root/'baseline/config.json'; TC=root/'trace/config.json'; ARENA=root/'arena-tests'

def status(rc): return 'accept' if rc==0 else ('decline' if rc==2 else 'reject')
tr=re.compile(r'^\[MGTRACE\]\s+(.*)$')
def parse(stderr):
    xs=[]
    for line in stderr.splitlines():
        m=tr.match(line.strip())
        if not m: continue
        d={}
        for tok in m.group(1).split():
            if '=' in tok:
                k,v=tok.split('=',1); d[k]=v
        xs.append(d)
    return xs
cases=[]
for kind,expected in [('good','accept'),('bad','reject')]:
    for p in sorted((ARENA/kind).rglob('*.ndjson')): cases.append((p,kind,expected))
rows=[]; mismatch=[]; expected_fail=[]
for p,kind,expected in cases:
    rec={'case':str(p.relative_to(ARENA)),'kind':kind,'expected':expected}
    for arm,binp,cfg in [('binary',B,BC),('compact',T,TC)]:
        t0=time.perf_counter()
        with p.open('rb') as f:
            cp=subprocess.run([str(binp),str(cfg)],stdin=f,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)
        rec[arm]={'status':status(cp.returncode),'seconds':time.perf_counter()-t0,
                  'events':parse(cp.stderr.decode('utf-8','replace')) if arm=='compact' else []}
    if rec['binary']['status']!=rec['compact']['status']: mismatch.append(rec['case'])
    if rec['binary']['status']!=expected: expected_fail.append(rec['case'])
    rows.append(rec)
rejects=[r for r in rows if r['binary']['status']=='reject']; nonempty=[r for r in rejects if r['compact']['events']]
sigs=collections.Counter(tuple((e.get('kind'),e.get('site'),e.get('ok'),e.get('heads_match')) for e in r['compact']['events'][-24:]) for r in nonempty)
b=[r['binary']['seconds'] for r in rows]; t=[r['compact']['seconds'] for r in rows]
events_total=sum(len(r['compact']['events']) for r in rows)
summary={
 'status':'LIVE_COMPACT_TRACE_V7','cases_total':len(rows),'good_cases':sum(r['kind']=='good' for r in rows),'bad_cases':sum(r['kind']=='bad' for r in rows),
 'semantic_mismatches':mismatch,'baseline_expected_failures':expected_fail,
 'rejects_total':len(rejects),'rejects_with_trace':len(nonempty),'reject_trace_coverage':len(nonempty)/len(rejects) if rejects else None,
 'distinct_reject_signatures':len(sigs),'events_total_all_cases':events_total,
 'timing':{'binary_total_seconds':sum(b),'compact_total_seconds':sum(t),'total_ratio':sum(t)/sum(b),
           'binary_mean_ms':1000*statistics.mean(b),'compact_mean_ms':1000*statistics.mean(t),
           'median_case_ratio':statistics.median([tt/bb for bb,tt in zip(b,t) if bb>0])},
 'gate_semantic_identity_pass':not mismatch,'gate_expected_correctness_pass':not expected_fail,
}
(out/'summary.json').write_text(json.dumps(summary,indent=2,sort_keys=True)); (out/'rows.json').write_text(json.dumps(rows,indent=2,sort_keys=True)); print(json.dumps(summary,indent=2,sort_keys=True))
if mismatch or expected_fail: raise SystemExit('semantic/correctness gate failed')
