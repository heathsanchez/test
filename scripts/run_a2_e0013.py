from pathlib import Path
import hashlib, json, random, statistics, subprocess, time

root = Path.cwd()
out = root / "results/a2-e0013-public"
out.mkdir(parents=True, exist_ok=True)
variants = ["a2", "e0013"]
bins = {v: root / v / "target/release/sokonanoda" for v in variants}
cfgs = {v: root / v / "config.json" for v in variants}

def status(rc):
    return "accept" if rc == 0 else ("decline" if rc == 2 else "reject")

cases=[]
for kind, expected in [("good","accept"),("bad","reject")]:
    for p in (root/"arena-tests"/kind).rglob("*.ndjson"):
        cases.append((p,expected))

correctness={}
for v in variants:
    failures=[]; declines=0
    for p,expected in cases:
        with p.open("rb") as f:
            rc=subprocess.run([str(bins[v]),str(cfgs[v])],stdin=f,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL).returncode
        got=status(rc); declines += int(got=="decline")
        if got!=expected:
            failures.append({"file":str(p.relative_to(root/"arena-tests")),"expected":expected,"got":got,"rc":rc})
    correctness[v]={"correct":len(cases)-len(failures),"total":len(cases),"declines":declines,"failures":failures}

if any(x["correct"]!=x["total"] or x["declines"]!=0 for x in correctness.values()):
    (out/"summary.json").write_text(json.dumps({"correctness":correctness},indent=2,sort_keys=True))
    raise SystemExit("semantic regression")

workload=sorted([p for p,_ in cases],key=lambda p:p.stat().st_size,reverse=True)[:24]
workload=sorted(workload,key=lambda p:hashlib.sha256(str(p.relative_to(root/"arena-tests")).encode()).hexdigest())
samples={v:[] for v in variants}; orders=[]
for seed in range(16):
    order=variants.copy(); random.Random(seed).shuffle(order); orders.append(order)
    for v in order:
        t=time.perf_counter()
        for p in workload:
            with p.open("rb") as f:
                subprocess.run([str(bins[v]),str(cfgs[v])],stdin=f,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,check=False)
        samples[v].append(time.perf_counter()-t)

med={v:statistics.median(samples[v]) for v in variants}
paired=[(c-b)/b for b,c in zip(samples["a2"],samples["e0013"])]
summary={
  "substrate":{"sokonanoda":"9b4ea12f4cd437d00b6bcd0e34743065c58dea08","threads":4,"session_budget":2621440},
  "correctness":correctness,
  "median_seconds":med,
  "speedup_e0013_vs_a2":med["a2"]/med["e0013"],
  "paired_fractional_change_e0013_minus_a2":paired,
  "paired_median_fractional_change":statistics.median(paired),
  "samples_seconds":samples,
  "orders":orders,
  "workload":[str(p.relative_to(root/"arena-tests")) for p in workload]
}
(out/"summary.json").write_text(json.dumps(summary,indent=2,sort_keys=True))
print(json.dumps(summary,indent=2,sort_keys=True))
