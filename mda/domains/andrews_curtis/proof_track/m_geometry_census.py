#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, math
from pathlib import Path

LETTERS=(1,-1,2,-2)

def red(w):
    out=[]
    for x in w:
        if out and out[-1]==-x: out.pop()
        else: out.append(x)
    return tuple(out)

def inv(w): return tuple(-x for x in reversed(tuple(w)))

def abel(w):
    return (sum(1 if x==1 else -1 if x==-1 else 0 for x in w),
            sum(1 if x==2 else -1 if x==-2 else 0 for x in w))

def cyclic_reduce(w):
    z=list(red(w)); pref=[]
    while len(z)>=2 and z[0]==-z[-1]:
        pref.append(z[0]);z=z[1:-1]
    return tuple(pref),tuple(z)

def rotations(w):
    w=tuple(w)
    if not w:return {()}
    return {w[k:]+w[:k] for k in range(len(w))}

def max_piece(core):
    s=sorted(rotations(core)|rotations(inv(core)))
    best=0
    for i,a in enumerate(s):
      for b in s[i+1:]:
        k=0
        while k<min(len(a),len(b)) and a[k]==b[k]:k+=1
        best=max(best,k)
    return best,len(s)

def signed_perms():
    out=[]
    for swap in (False,True):
      base=(2,1) if swap else (1,2)
      for s1 in (-1,1):
       for s2 in (-1,1):
        out.append({1:s1*base[0],2:s2*base[1]})
    return out

def phi_letter(images,g):
    v=images[abs(g)]
    return v if g>0 else tuple(-x for x in reversed(v))

def apply_phi(w,images):
    out=()
    for g in w: out=red(out+phi_letter(images,g))
    return out

def whitehead_type2():
    # Standard Whitehead automorphisms on basis letters; convention:
    # multiplier a is fixed. For generator x != |a|, membership of x and x^-1
    # in A determines x, x a, a^-1 x, or a^-1 x a.
    autos=[]
    for a in LETTERS:
      others=[x for x in LETTERS if x not in (a,-a)]
      # A contains a and excludes -a; choose membership freely for the other
      # signed letters, subject to a map on basis generators.
      for mask in range(1<<len(others)):
        A={a}
        for k,x in enumerate(others):
          if (mask>>k)&1:A.add(x)
        images={}
        for gen in (1,2):
          if gen in (a,-a):
            images[gen]=(gen,)
            continue
          pin=gen in A; nin=(-gen) in A
          if pin and not nin: images[gen]=(gen,a)
          elif not pin and nin: images[gen]=(-a,gen)
          elif pin and nin: images[gen]=(-a,gen,a)
          else: images[gen]=(gen,)
        # multiplier may be inverse of a basis generator: ensure it itself fixed.
        if a<0:
          images[-a]=(-a,)
          # dictionary stores positive generator image; if a=-gen, fixing -gen
          # means fixing gen as well.
          images[abs(a)]=(abs(a),)
        autos.append((a,tuple(sorted(A)),images))
    # dedupe by images
    seen={};out=[]
    for a,A,img in autos:
      key=(img[1],img[2])
      if key not in seen:
        seen[key]=1;out.append((a,A,img))
    return out

TYPE2=whitehead_type2()
PERMS=signed_perms()

def primitive_minimize(w):
    cur=red(w);seq=[]
    while True:
        best=(len(cur),cur,None)
        # type I
        for p in PERMS:
            img={1:(p[1],),2:(p[2],)}
            z=apply_phi(cur,img)
            cand=(len(z),z,("perm",p[1],p[2]))
            if cand[:2]<best[:2]:best=cand
        # type II
        for a,A,img in TYPE2:
            z=apply_phi(cur,img)
            cand=(len(z),z,("whitehead",a,list(A),list(img[1]),list(img[2])))
            if cand[:2]<best[:2]:best=cand
        if best[0]>=len(cur):
            break
        cur=best[1];seq.append(best[2])
    return cur,seq

def classify(w):
    w=red(w);p,c=cyclic_reduce(w)
    amin=primitive_minimize(w)
    mp,ns=max_piece(c)
    v=abel(w);g=math.gcd(abs(v[0]),abs(v[1]))
    return {
      "word":list(w),"length":len(w),"abelianization":list(v),"abelian_gcd":g,
      "cyclic_core":list(c),"cyclic_core_length":len(c),
      "max_piece":mp,"symmetrized_distinct":ns,
      "piece_ratio":None if not c else mp/len(c),
      "cprime_1_6":bool(c) and 6*mp < len(c),
      "whitehead_min_word":list(amin[0]),
      "whitehead_min_length":len(amin[0]),
      "primitive":len(amin[0])==1,
      "whitehead_steps":amin[1],
    }

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--acc-root",required=True)
    ap.add_argument("--out-dir",required=True)
    a=ap.parse_args()
    manifest=json.loads((Path(a.acc_root)/"competition/tools/verifier/data/manifest.json").read_text())
    by={c["challenge_id"]:c for c in manifest["challenges"]}
    ids=["ac-01684","ac-08027","ac-00106","ac-01523","ac-01520"]

    controls={
      "x":(1,),
      "xy":(1,2),
      "commutator":(1,2,-1,-2),
      "square":(1,1),
    }
    ctrl={k:classify(v) for k,v in controls.items()}
    if not ctrl["x"]["primitive"] or not ctrl["xy"]["primitive"]:
        raise RuntimeError(("primitive positive control failed",ctrl))
    if ctrl["commutator"]["primitive"] or ctrl["square"]["primitive"]:
        raise RuntimeError(("primitive negative control failed",ctrl))

    rows=[]
    for cid in ids:
      c=by[cid]
      rels=c["initial_relators"]
      rec={"challenge_id":cid,"relators":[classify(tuple(w)) for w in rels]}
      rows.append(rec)
      print("M_GEOMETRY_CASE",json.dumps({
        "challenge_id":cid,
        "r0_primitive":rec["relators"][0]["primitive"],
        "r0_min":rec["relators"][0]["whitehead_min_length"],
        "r0_c16":rec["relators"][0]["cprime_1_6"],
        "r1_primitive":rec["relators"][1]["primitive"],
        "r1_min":rec["relators"][1]["whitehead_min_length"],
        "r1_c16":rec["relators"][1]["cprime_1_6"],
      },sort_keys=True))
    report={
      "experiment":"ACC_M_GEOMETRY_CENSUS_V1",
      "cases":len(rows),
      "primitive_coordinates":sum(r["primitive"] for x in rows for r in x["relators"]),
      "cprime_1_6_coordinates":sum(r["cprime_1_6"] for x in rows for r in x["relators"]),
      "controls":ctrl,
      "claim_boundary":"Whitehead descent and symmetrized-piece census at the frozen initial presentations only."
    }
    out=Path(a.out_dir);out.mkdir(parents=True,exist_ok=True)
    (out/"report.json").write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
    (out/"cases.json").write_text(json.dumps(rows,indent=2,sort_keys=True)+"\n")
    print("M_GEOMETRY_SUMMARY",json.dumps({
      "primitive_coordinates":report["primitive_coordinates"],
      "cprime_1_6_coordinates":report["cprime_1_6_coordinates"]
    },sort_keys=True))

if __name__=="__main__":main()
