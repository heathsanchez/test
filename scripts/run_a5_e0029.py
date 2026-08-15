from pathlib import Path
import subprocess,time,json,statistics,random,hashlib
root=Path.cwd(); out=root/'results/a5-e0029'; out.mkdir(parents=True,exist_ok=True)
vs=['a5','e0029']; bins={v:root/v/'target/release/sokonanoda' for v in vs}; cfgs={v:root/v/'config.json' for v in vs}
def status(rc): return 'accept' if rc==0 else ('decline' if rc==2 else 'reject')
cases=[]
for kind,exp in [('good','accept'),('bad','reject')]:
    for p in (root/'arena-tests'/kind).rglob('*.ndjson'): cases.append((p,exp))
correctness={}
for v in vs:
    bad=[]; declines=0
    for p,exp in cases:
        with p.open('rb') as f: rc=subprocess.run([str(bins[v]),str(cfgs[v])],stdin=f,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL).returncode
        st=status(rc); declines += st=='decline'
        if st!=exp: bad.append(str(p.relative_to(root/'arena-tests')))
    correctness[v]={'correct':len(cases)-len(bad),'total':len(cases),'declines':declines,'failures':bad}
workload=sorted([p for p,_ in cases],key=lambda p:p.stat().st_size,reverse=True)[:24]
workload=sorted(workload,key=lambda p:hashlib.sha256(str(p.relative_to(root/'arena-tests')).encode()).hexdigest())
samples={v:[] for v in vs}; orders=[]
for seed in range(20):
    order=vs.copy(); random.Random(seed).shuffle(order); orders.append(order.copy())
    for v in order:
        t=time.perf_counter()
        for p in workload:
            with p.open('rb') as f: subprocess.run([str(bins[v]),str(cfgs[v])],stdin=f,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,check=False)
        samples[v].append(time.perf_counter()-t)
med={v:statistics.median(samples[v]) for v in vs}; paired=[(b-a)/a for a,b in zip(samples['a5'],samples['e0029'])]
summary={'substrate':{'sokonanoda':'9b4ea12f4cd437d00b6bcd0e34743065c58dea08','threads':4,'session_budget':2621440,'a5':'E0018 + E0024 App bypass + E0025 Lambda bypass'},'intervention':'direct Var(0..3) lookup through Cons prefix','correctness':correctness,'median_seconds':med,'speedup_e0029_vs_a5':med['a5']/med['e0029'],'paired_median_fractional_change':statistics.median(paired),'paired_win_count_e0029':sum(x<0 for x in paired),'paired_fractional_change_e0029_minus_a5':paired,'samples_seconds':samples,'orders':orders,'workload':[str(p.relative_to(root/'arena-tests')) for p in workload]}
(out/'summary.json').write_text(json.dumps(summary,indent=2,sort_keys=True)); print(json.dumps(summary,indent=2,sort_keys=True))
if any(x['correct']!=x['total'] or x['declines'] for x in correctness.values()): raise SystemExit('correctness regression')
