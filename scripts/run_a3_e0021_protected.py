from pathlib import Path
import subprocess, json, statistics, random, hashlib, re

root=Path.cwd(); out=root/'results/a3-e0021-protected'; out.mkdir(parents=True,exist_ok=True)
vs=['a3','e0021']; bins={v:root/v/'target/release/sokonanoda' for v in vs}; cfgs={v:root/v/'config.json' for v in vs}
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
if any(x['correct']!=x['total'] or x['declines'] for x in correctness.values()):
    (out/'summary.json').write_text(json.dumps({'correctness':correctness},indent=2,sort_keys=True)); raise SystemExit('correctness regression')

workload=sorted([p for p,_ in cases],key=lambda p:p.stat().st_size,reverse=True)[:24]
workload=sorted(workload,key=lambda p:hashlib.sha256(str(p.relative_to(root/'arena-tests')).encode()).hexdigest())
wf=out/'workload.txt'; wf.write_text('\n'.join(str(p) for p in workload)+'\n')
runner=out/'run_arm.sh'; runner.write_text('''#!/usr/bin/env bash\nset -euo pipefail\nbin="$1"\ncfg="$2"\nlist="$3"\nwhile IFS= read -r p; do\n  "$bin" "$cfg" < "$p" >/dev/null 2>/dev/null || true\ndone < "$list"\n'''); runner.chmod(0o755)
def measure(v,i):
    tf=out/f'time-{i}-{v}.txt'
    subprocess.run(['/usr/bin/time','-f','wall=%e user=%U sys=%S rss_kb=%M','-o',str(tf),str(runner),str(bins[v]),str(cfgs[v]),str(wf)],check=True)
    m=re.search(r'wall=([0-9.]+) user=([0-9.]+) sys=([0-9.]+) rss_kb=(\d+)',tf.read_text().strip())
    if not m: raise RuntimeError(tf.read_text())
    wall,user,sys,rss=m.groups(); return {'wall':float(wall),'cpu':float(user)+float(sys),'user':float(user),'sys':float(sys),'rss_kb':int(rss)}
samples={v:[] for v in vs}; orders=[]
for seed in range(12):
    order=vs.copy(); random.Random(seed).shuffle(order); orders.append(order.copy())
    for v in order: samples[v].append(measure(v,seed))
def vals(v,k): return [x[k] for x in samples[v]]
def paired(k): return [(b-a)/a for a,b in zip(vals('a3',k),vals('e0021',k))]
summary={'substrate':{'sokonanoda':'9b4ea12f4cd437d00b6bcd0e34743065c58dea08','threads':4,'session_budget':2621440,'a3':'E0018 apply_many transient prune removal','build':'Arena-style init-prelude PGO + target-cpu=native'},'correctness':correctness,'workload':[str(p.relative_to(root/'arena-tests')) for p in workload],'orders':orders,'samples':samples,'median':{v:{k:statistics.median(vals(v,k)) for k in ('wall','cpu','rss_kb')} for v in vs},'paired_median_fractional_change':{k:statistics.median(paired(k)) for k in ('wall','cpu','rss_kb')},'paired_fractional_change':{k:paired(k) for k in ('wall','cpu','rss_kb')},'wins':{k:sum(b<a for a,b in zip(vals('a3',k),vals('e0021',k))) for k in ('wall','cpu','rss_kb')}}
(out/'summary.json').write_text(json.dumps(summary,indent=2,sort_keys=True)); print(json.dumps(summary,indent=2,sort_keys=True))
