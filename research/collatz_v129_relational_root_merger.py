"""V129: exact symbolic relational odd-three-root class-merger law.

Rather than expand V128's deterministic canonical root grammar after its
proved all-clock failure at source 21, compile a new source-attached
two-clock family into the existing protected relation:

  n(t) = 21+72*t, p(t) = 3+12*t,
  T^3(n(t)) = 8+27*t = T^2(p(t)),
  0<p(t)<n(t), both congruent 3 mod 6, for EVERY t>=0.

Coefficient equality at every permitted parity step is checked
symbolically for all offsets. Samples are independent regressions.
This is not a universal Collatz proof.
"""
import hashlib
import json

def T(n: int) -> int:
    assert n > 0
    return n // 2 if n % 2 == 0 else (3 * n + 1)//2

def affine_step(base: int, slope: int):
    assert slope % 2 == 0, "affine parity must hold for every offset"
    if base % 2 == 0:
        return base//2, slope//2
    return (3*base+1)//2, 3*slope//2

def certificate():
    n0,nc=21,72
    p0,pc=3,12
    source=[(n0,nc)]
    predecessor=[(p0,pc)]
    for _ in range(3):
        n0,nc=affine_step(n0,nc)
        source.append((n0,nc))
    for _ in range(2):
        p0,pc=affine_step(p0,pc)
        predecessor.append((p0,pc))
    assert source==[(21,72),(32,108),(16,54),(8,27)]
    assert predecessor==[(3,12),(5,18),(8,27)]
    assert source[-1]==predecessor[-1]
    # Base and slope guards inductively protect every t>=0.
    assert 0<3<21 and 0<12<72
    assert 21%6==3 and 3%6==3 and 72%6==12%6==0
    samples=[]
    for t in (0,1,2,7,31,256,4096):
        x=21+72*t
        p=3+12*t
        assert 0<p<x and x%6==3 and p%6==3
        xx,pp=x,p
        for _ in range(3): xx=T(xx)
        for _ in range(2): pp=T(pp)
        assert xx==pp==8+27*t
        samples.append(dict(t=t,source=x,earlier=p,source_clock=3,
                            earlier_clock=2,common=xx))
    return source, predecessor, samples

def main():
    source, predecessor, samples=certificate()
    result=dict(
        schema="COLLATZ_V129_RELATIONAL_ODD_THREE_ROOT_LOWER_MERGER",
        status="EXACT_AFFINE_ALL_OFFSETS_FORMAL_CANDIDATE",
        source_family="n(t)=21+72*t",
        strictly_smaller_odd_three_root="p(t)=3+12*t",
        real_source_clock=3,
        real_predecessor_clock=2,
        all_offset_meeting="8+27*t",
        source_affine_prefix=source,
        predecessor_affine_prefix=predecessor,
        samples=samples,
        guards=["0<p(t)<n(t)","n(t)%6=3","p(t)%6=3",
                "parity at each actual shortcut step independent of t"],
        v128_separator="canonical root selector stutters at original source21",
        source_integration="existing V124 LawfulFutureJoin relation",
        bulk_residue_percentage_not_claimed=True,
        universal_odd_root_event_production=False,
        global_collatz="UNKNOWN",
        qed=False)
    data=json.dumps(result,sort_keys=True,separators=(",",":"))
    result["payload_sha256"]=hashlib.sha256(data.encode()).hexdigest()
    print(json.dumps(result,sort_keys=True,indent=2))

if __name__=="__main__":main()
