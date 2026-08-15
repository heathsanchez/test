from pathlib import Path
import subprocess, json, statistics, random, hashlib, re, os

root=Path.cwd()
out=root/'results/a3-vs-zignodamus'
out.mkdir(parents=True,exist_ok=True)
a3=root/'a3/target/release/sokonanoda'
a3cfg=root/'a3/config.json'
zig=root/'zignodamus/zig-out/bin/zignodamus'
zig_args=[str(zig),'--use-stdin','--nat-extension','--string-extension','--unsafe-permit-all-axioms','--no-unpermitted-axiom-hard-error','-j4']

cases=[]
for kind, exp in [('good',True),('bad',False)]:
    for p in (root/'arena-tests'/kind).rglob('*.ndjson'):
        cases.append((p,exp))

def run_one(which,p):
    with p.open('rb') as f:
        if which=='a3':
            rc=subprocess.run([str(a3),str(a3cfg)],stdin=f,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL).returncode
        else:
            rc=subprocess.run(zig_args,stdin=f,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL).returncode
    return rc==0

correctness={}
for which in ('a3','zignodamus'):
    bad=[]
    for p,exp in cases:
        got=run_one(which,p)
        if got != exp:
            bad.append(str(p.relative_to(root/'arena-tests')))
    correctness[which]={'correct':len(cases)-len(bad),'total':len(cases),'failures':bad}

# Performance only if both preserve the frozen corpus semantics.
if any(v['correct'] != v['total'] for v in correctness.values()):
    (out/'summary.json').write_text(json.dumps({'correctness':correctness},indent=2,sort_keys=True))
    print(json.dumps({'correctness':correctness},indent=2,sort_keys=True))
    raise SystemExit('semantic mismatch')

workload=sorted([p for p,_ in cases], key=lambda p:p.stat().st_size, reverse=True)[:24]
workload=sorted(workload,key=lambda p:hashlib.sha256(str(p.relative_to(root/'arena-tests')).encode()).hexdigest())
(out/'workload.txt').write_text('\n'.join(str(p) for p in workload)+'\n')

runner=out/'run_arm.sh'
runner.write_text('''#!/usr/bin/env bash\nset -euo pipefail\nwhich="$1"\nlist="$2"\nwhile IFS= read -r p; do\n  if [[ "$which" == a3 ]]; then\n    a3/target/release/sokonanoda a3/config.json < "$p" >/dev/null 2>/dev/null || true\n  else\n    zignodamus/zig-out/bin/zignodamus --use-stdin --nat-extension --string-extension --unsafe-permit-all-axioms --no-unpermitted-axiom-hard-error -j4 < "$p" >/dev/null 2>/dev/null || true\n  fi\ndone < "$list"\n''')
runner.chmod(0o755)

def measure(which,idx):
    tf=out/f'time-{idx}-{which}.txt'
    subprocess.run(['/usr/bin/time','-f','wall=%e user=%U sys=%S rss_kb=%M','-o',str(tf),str(runner),which,str(out/'workload.txt')],check=True)
    text=tf.read_text().strip()
    m=re.search(r'wall=([0-9.]+) user=([0-9.]+) sys=([0-9.]+) rss_kb=(\d+)',text)
    if not m: raise RuntimeError(text)
    wall,user,sys,rss=m.groups()
    return {'wall':float(wall),'cpu':float(user)+float(sys),'rss_kb':int(rss)}

samples={k:[] for k in ('a3','zignodamus')}; orders=[]
for seed in range(12):
    order=['a3','zignodamus']; random.Random(seed).shuffle(order); orders.append(order.copy())
    for which in order:
        samples[which].append(measure(which,seed))

def vals(w,k): return [x[k] for x in samples[w]]
def ratio(k): return statistics.median(vals('a3',k))/statistics.median(vals('zignodamus',k))
summary={
 'correctness':correctness,
 'substrates':{'a3':'sokonanoda 9b4ea12 + 2.5MiB/session + E0018; Arena-style PGO','zignodamus':'111372299e41188a159d05f8df780342e12aff1b zig -Drelease -j4'},
 'workload':[str(p.relative_to(root/'arena-tests')) for p in workload],
 'orders':orders,'samples':samples,
 'median':{w:{k:statistics.median(vals(w,k)) for k in ('wall','cpu','rss_kb')} for w in samples},
 'a3_over_zignodamus_ratio':{k:ratio(k) for k in ('wall','cpu','rss_kb')},
 'a3_wins':{k:sum(a<b for a,b in zip(vals('a3',k),vals('zignodamus',k))) for k in ('wall','cpu','rss_kb')}
}
(out/'summary.json').write_text(json.dumps(summary,indent=2,sort_keys=True))
print(json.dumps(summary,indent=2,sort_keys=True))
