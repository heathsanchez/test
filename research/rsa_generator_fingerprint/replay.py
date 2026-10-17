#!/usr/bin/env python3
"""Reproduce a bounded, exploratory historical RSA prime-gap diagnostic.
This is NOT a factoring algorithm or historical origin attribution.
"""
import json, math, random, subprocess
from pathlib import Path
from itertools import combinations
from math import gcd

ROOT=Path(__file__).resolve().parent
TRIALS=20000
RADII=(6,12,24)
SEED=17061991

def quantile(s,q):
    return round(float(s[int((len(s)-1)*q)]),5)

def simulate(rows,model,seed):
    rng=random.Random(seed)
    pos=1 if model=="scan_plus_6" else 0
    observed=sum(r["gaps"][pos]/r["logp"] for r in rows)/len(rows)
    totals=[0.0]*TRIALS
    for row in rows:
        source=[c[pos] for c in row["controls"]]
        samples=rng.choices(source,weights=None if model=="uniform_prime" else source,k=TRIALS)
        for k,v in enumerate(samples):
            totals[k]+=v/row["logp"]
    totals=[v/len(rows) for v in totals]
    upper=(1+sum(v>=observed for v in totals))/(TRIALS+1)
    lower=(1+sum(v<=observed for v in totals))/(TRIALS+1)
    expected=sum(totals)/TRIALS
    totals.sort()
    return {"observed":round(observed,5),"expected":round(expected,5),
            "p_upper":round(upper,6),"p_lower":round(lower,6),
            "q05_q95":[quantile(totals,.05),quantile(totals,.95)]}

def main():
    data=json.loads((ROOT/"data.json").read_text())
    assert len(data["all"])==56 and len(data["solved"])==18
    corpus=[(v["name"],int(v["n"])) for v in data["all"]]
    collisions=[(a,b,str(gcd(x,y))) for (a,x),(b,y) in combinations(corpus,2) if gcd(x,y)>1]
    assert not collisions
    look=dict(corpus)
    for name,cs in [("RSA-100",294805),("RSA-250",509331),("RSA-270",10237)]:
        assert look[name]%991889==cs
    originals=[v for v in data["solved"] if v["cohort"]=="original"]
    additions=[v for v in data["solved"] if v["cohort"]=="1997_addition"]
    assert len(originals)==16 and len(additions)==2
    for v in data["solved"]:
        n,p,q=map(int,(v["n"],v["p"],v["q"]))
        assert p*q==n and p%3==2 and q%3==2
    factors=[int(v[t]) for v in originals for t in ("p","q")]
    binary=ROOT/"prime_context"
    subprocess.run(["cc","-O3",str(ROOT/"prime_context.c"),"-o",str(binary),"-lgmp","-lm"],check=True)
    output={"status":"EXPLORATORY_BOUNDED_RETROSPECTIVE; no factor or generator recovered",
            "source":data["source"],"original_moduli":16,"original_prime_factors":32,
            "excluded_1997_additions":[v["name"] for v in additions],
            "batch_gcd":{"catalogue_size":56,"pairs_checked":1540,"shared_factors":collisions},
            "primary_checksum_controls":["RSA-100","RSA-250","RSA-270"],"models":{},
            "limitations":"GMP probable prime neighbourhoods, local factor-centred controls, retrospective research direction. Not an RSA DSP code or seed fingerprint."}
    for radius in RADII:
        raw=subprocess.run([str(binary),str(radius)],input="\n".join(str(x) for x in factors)+"\n",
                           text=True,capture_output=True,check=True,timeout=160).stdout.splitlines()
        assert len(raw)==32
        rows=[]
        for prime,line in zip(factors,raw):
            fields=line.split(",")
            assert len(fields)==3+2*radius
            gaps=(int(fields[0]),int(fields[1]))
            logp=float(fields[2])
            controls=[tuple(map(int,z.split(":"))) for z in fields[3:]]
            assert 0<gaps[0]<=gaps[1] and abs(logp-math.log(prime))<1e-9
            assert all(0<a<=b for a,b in controls)
            rows.append({"gaps":gaps,"logp":logp,"controls":controls})
        output["models"][str(radius)]={
            "uniform_prime":simulate(rows,"uniform_prime",SEED+radius),
            "scan_plus_2":simulate(rows,"scan_plus_2",SEED+radius+1),
            "scan_plus_6":simulate(rows,"scan_plus_6",SEED+radius+2)}
    (ROOT/"result.json").write_text(json.dumps(output,indent=2)+"\n")
    print(json.dumps(output,indent=2))

if __name__=="__main__":
    main()
