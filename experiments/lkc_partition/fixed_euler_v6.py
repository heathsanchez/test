#!/usr/bin/env python3
"""V6 fixed Euler polynomial screen; source-generated, not formally proved."""
from pathlib import Path
import runpy,hashlib,json
root=Path(__file__).resolve().parent
old=runpy.run_path(str(root/"euler_horner_v5.py"))
base=old["source_for"]("horner_helper")
assert "def packedEuler (n : Nat) : Nat :=" in base
start=base.index("def packedEuler (n : Nat) : Nat :=")
end=base.index("\ndef impl : Nat → Nat := packedEuler",start)
prefix=base[:start].replace("def packedEulerFallback (n : Nat) : Nat :=","def packedEulerFallback (n : Nat) : Nat :=")
suffix=base[end:].replace("def impl : Nat → Nat := packedEuler","def impl : Nat → Nat := packedEulerFixed",1)
terms=[]
for j in range(1,13):
    s=1 if j%2==0 else -1
    terms.extend([(j*(3*j-1)//2,s),(j*(3*j+1)//2,s)])
def expr(degree,flat=False):
    xs=[(g,s) for g,s in terms if g<=degree]
    pos=[degree]+[degree-g for g,s in xs if s>0]
    neg=[degree-g for g,s in xs if s<0]
    def render(exps):
        exps=sorted(set(exps),reverse=True)
        if not exps:return "(0 : Nat)"
        if flat:return " + ".join(f"((1 : Nat) <<< (w * {e}))" for e in exps)
        a="(1 : Nat)"
        for u,v in zip(exps,exps[1:]):a=f"(({a} <<< (w * {u-v})) + 1)"
        if exps[-1]:a=f"({a} <<< (w * {exps[-1]}))"
        return a
    return f"extract w n {degree} ({render(pos)}) ({render(neg)})"
arms={
 "fixed40_horner":[(51,40,False)],
 "fixed57_horner":[(70,57,False)],
 "fixed57_flat":[(70,57,True)],
 "stage26_40_57_horner":[(35,26,False),(51,40,False),(70,57,False)]
}
def reference(n):
    a=[0]*(n+1);a[0]=1
    for k in range(1,n+1):
        for i in range(k,n+1):a[i]+=a[i-k]
    return a[n]
def value(n,steps):
    for threshold,degree,flat in steps:
        if n<threshold:
            B=1<<(n+3)
            pos=[degree]+[degree-g for g,s in terms if g<=degree and s>0]
            neg=[degree-g for g,s in terms if g<=degree and s<0]
            return (B**(n+degree)//(sum(B**e for e in pos)-sum(B**e for e in neg)))%B
    return old["coeff"](n)
out=root/"generated";out.mkdir(exist_ok=True)
record={"status":"FINITE_EXACT_PASS","cases":241,"arms":{},"universal_Lean_proof":False,"formal_submission":False}
for name,steps in arms.items():
    assert all(value(n,steps)==reference(n) for n in range(241)),name
    lines=["def packedEulerFixed (n : Nat) : Nat :=","  let w := n + 3"]
    for i,(threshold,degree,flat) in enumerate(steps):
        lines.append(f"  {'if' if i==0 else 'else if'} n < {threshold} then")
        lines.append("    "+expr(degree,flat))
    lines.append("  else packedEulerFallback n")
    source=prefix+"\n".join(lines)+"\n"+suffix
    target=out/f"Submission_fixed_euler_{name}_probe.lean"
    target.write_text(source)
    record["arms"][name]={"sha256":hashlib.sha256(source.encode()).hexdigest(),"bytes":len(source.encode())}
(out/"fixed_euler_v6_finite.json").write_text(json.dumps(record,indent=2)+"\n")
print(json.dumps(record,indent=2))
