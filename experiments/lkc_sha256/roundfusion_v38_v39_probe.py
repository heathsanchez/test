#!/usr/bin/env python3
from pathlib import Path
import runpy

ROOT=Path(__file__).resolve().parent
OUT=ROOT/"generated"; OUT.mkdir(parents=True,exist_ok=True)

runpy.run_path(str(ROOT/"mulrotate_scalar_v31_probe.py"))
src=(OUT/"Submission_mulrotate_scalar_v31_probe.lean").read_text()
prefix=src.rsplit("\nend Submission",1)[0]

wins=[f"w{i}" for i in range(16)]
sts=["a","b","c","d","e","f","g","h"]
types=" → ".join(["Nat"]*24+["Digest"])

def step_lines(j, kname, w, s):
    a,b,c,d,e,f,g,h=s
    lines=[
        f"      let nw{j} := (smallSigma1Fast {w[14]} + {w[9]} + smallSigma0Fast {w[1]} + {w[0]}) &&& w32",
        f"      let t1{j} := {h} + bigSigma1Fast {e} + chFast {e} {f} {g} + {kname} + {w[0]}",
        f"      let t2{j} := bigSigma0Fast {a} + majFast {a} {b} {c}",
        f"      let na{j} := (t1{j} + t2{j}) &&& w32",
        f"      let ne{j} := ({d} + t1{j}) &&& w32",
    ]
    nw=w[1:]+[f"nw{j}"]
    ns=[f"na{j}",a,b,c,f"ne{j}",e,f,g]
    return lines,nw,ns

def emit_def(name, chunk):
    nilpat=", ".join(["[]"]+["_"]*16+sts)
    lines=[f"def {name} : List Nat → {types}",
           f"  | {nilpat} => ⟨a,b,c,d,e,f,g,h⟩"]
    # Remainders 1..chunk-1 return directly after those rounds.
    for r in range(1,chunk):
        ks=[f"k{i}" for i in range(r)]
        pat=" :: ".join(ks+["[]"])
        args=", ".join(wins+sts)
        lines.append(f"  | {pat}, {args} =>")
        w=wins[:]; s=sts[:]
        for j,k in enumerate(ks):
            ls,w,s=step_lines(j,k,w,s); lines.extend(ls)
        lines.append("      ⟨"+",".join(s)+"⟩")
    ks=[f"k{i}" for i in range(chunk)]
    pat=" :: ".join(ks+["ks"])
    args=", ".join(wins+sts)
    lines.append(f"  | {pat}, {args} =>")
    w=wins[:]; s=sts[:]
    for j,k in enumerate(ks):
        ls,w,s=step_lines(j,k,w,s); lines.extend(ls)
    lines.append(f"      {name} ks "+" ".join(w+s))
    return "\n".join(lines)

body="\n/-! Partial round-fusion probes over the V31 MulRotate scalar runtime. -/\n\n"
body+=emit_def("roundsChunk2V38",2)+"\n\n"
body+=f'''def fastStepChunk2V38 (d : Digest) : Digest :=
  let f := roundsChunk2V38 K
    d.a d.b d.c d.d d.e d.f d.g d.h
    0x80000000 0 0 0 0 0 0 256
    iv.a iv.b iv.c iv.d iv.e iv.f iv.g iv.h
  feedForwardIV f

def implChunk2V38 (n : Nat) : Nat :=
  encodeDigest (iterDigest fastStepChunk2V38
    (sha256Steps n) (seedDigest (sha256Seed n)))

'''
body+=emit_def("roundsChunk4V39",4)+"\n\n"
body+=f'''def fastStepChunk4V39 (d : Digest) : Digest :=
  let f := roundsChunk4V39 K
    d.a d.b d.c d.d d.e d.f d.g d.h
    0x80000000 0 0 0 0 0 0 256
    iv.a iv.b iv.c iv.d iv.e iv.f iv.g iv.h
  feedForwardIV f

def implChunk4V39 (n : Nat) : Nat :=
  encodeDigest (iterDigest fastStepChunk4V39
    (sha256Steps n) (seedDigest (sha256Seed n)))

end Submission
'''

p=OUT/"Submission_roundfusion_v38_v39_probe.lean"
p.write_text(prefix+body)
print(f"generated {p} bytes={len(p.read_bytes())}")
