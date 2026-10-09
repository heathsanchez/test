"""V133 exact symbolic proof-oracle for source23 chart and source27 replay.

All-offset source23→root3 at clocks (7,1):
  T^7(23+384*t)=5+81*t=T(3+54*t).
The source27→23 at (59,0) was already formally qualified in V122;
compose instead of replaying proof development:
  T^66(27)=T(3)=5 and T^70(27)=T(2)=1.

No universal existence theorem or source27 entire CRT-cylinder claim.
"""
import hashlib,json

def T(n):
    assert n>0
    return n//2 if n%2==0 else (3*n+1)//2

def affine_step(b,s):
    assert s%2==0
    return (b//2,s//2) if b%2==0 else ((3*b+1)//2,3*s//2)

def iterative(n,k):
    for _ in range(k):n=T(n)
    return n

def main():
    n0,nc=23,384
    p0,pc=3,54
    source=[(n0,nc)]
    previous=[(p0,pc)]
    for _ in range(7):
        n0,nc=affine_step(n0,nc)
        source.append((n0,nc))
    for _ in range(1):
        p0,pc=affine_step(p0,pc)
        previous.append((p0,pc))
    assert source==[(23,384),(35,576),(53,864),(80,1296),(40,648),(20,324),(10,162),(5,81)]
    assert previous==[(3,54),(5,81)]
    assert source[-1]==previous[-1]
    assert 0<3<23 and 0<54<384
    assert (3+54)%6==3
    samples=[]
    for t in (0,1,2,7,31,127,1000):
        n,p=23+384*t,3+54*t
        assert 0<p<n and p%6==3
        assert iterative(n,7)==iterative(p,1)==5+81*t
        samples.append(dict(t=t,source=n,earlier=p,source_clock=7,
                            earlier_clock=1,common=5+81*t))
    assert iterative(27,59)==23
    assert iterative(23,7)==5 and iterative(3,1)==5
    assert iterative(27,66)==5
    assert iterative(27,70)==1
    assert iterative(2,1)==1
    result={
        "schema":"COLLATZ_V133_ROOT23_CHART_AND_27_LATE_RECONCILIATION",
        "status":"EXACT_SYMBOLIC_FAMILY_PLUS_FINITE_COMPOSITION",
        "root23_source_chart":source,
        "root3_predecessor_chart":previous,
        "all_offset_samples":samples,
        "all_offset_formula":"T^7(23+384*t)=5+81*t=T(3+54*t)",
        "v122_external_premise":"T^59(27)=23; first lower meeting clock 59 has separately qualified theorem",
        "source27_to23_clocks":[59,0],
        "source23_to3_clocks":[7,1],
        "source27_to3_composed_clocks":[66,1],
        "source27_to2_composed_clocks":[70,1],
        "source27_reached_root3":5,
        "source27_reached_root2":1,
        "no_entire_original_crt_class_promotion":True,
        "universal_event_production":"UNKNOWN",
        "global_collatz":"UNKNOWN","qed":False}
    text=json.dumps(result,sort_keys=True,separators=(",",":"))
    result["payload_sha256"]=hashlib.sha256(text.encode()).hexdigest()
    print(json.dumps(result,indent=2,sort_keys=True))

if __name__=="__main__":main()
