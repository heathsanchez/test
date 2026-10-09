"""Exact V118 source-11 modulo 16 and source-45 modulo 729 certification.

An all-offset lower-source coalescence family:
  T^4(10251+11664*z) = T^13(7199+8192*z), 0<p<n, all z>=0.
Exhaustively compare its old 2^12*3^7 residue classes with V108,V109,
V110, and the original V112 12+12 bounded mixed-reverse compiler.

This is a novel bounded certificate family, NOT universal Collatz.
"""
import hashlib,json
from research.collatz_v108_reclosure import candidates,prefixes,shortcut
from research.collatz_v109_reverse_reclosure import reverse_witness
from research.collatz_v110_q7_crt_reclosure import (
    DYADIC,TERNARY,PRODUCT,crt_base,ternary_reverse)

N0,NM=10251,11664
P0,PM=7199,8192


def affine_step(b,c):
    assert c%2==0
    return (b//2,c//2) if b%2==0 else ((3*b+1)//2,3*c//2)


def old_v112_reverse_witness(n0):
    # This is the exact V112 producer scope: prefixes<=12, reverse<=12,
    # original full CRT modulus P=4096*2187, all-offset source cap.
    for j,x,odd,a_dyadic in prefixes(n0):
        a=a_dyadic*TERNARY
        states=[(x,a,"")]
        seen={(x,a)}
        for _ in range(12):
            nxt=[]
            for b,c,w in states:
                bb,cc=2*b,2*c
                if bb>0 and cc<50*PRODUCT and (bb,cc) not in seen:
                    nxt.append((bb,cc,w+"E"))
                    seen.add((bb,cc))
                if b>=2 and b%3==2 and c%3==0:
                    bb,cc=(2*b-1)//3,2*c//3
                    if bb>0 and (bb,cc) not in seen:
                        nxt.append((bb,cc,w+"O"))
                        seen.add((bb,cc))
            for b,c,w in nxt:
                if 0<b<n0 and c<=PRODUCT:
                    return (j,len(w),b,c,w)
            states=nxt
            if not states:
                break
    return None


def audit_family():
    assert N0%16==11 and N0%729==45
    assert N0==45+729*14
    assert P0==31+512*14
    assert 0<P0<N0 and 0<PM<NM
    n_b,n_s=N0,NM
    f_b,f_s=3*N0+2,3*NM
    prefix=[]
    for j in range(1,5):
        n_b,n_s=affine_step(n_b,n_s)
        f_b,f_s=affine_step(f_b,f_s)
        # Symbolic all-offset original-source nondescending guard:
        assert n_b>=N0 and n_s>=NM
        # Exact source-capped ternary condition is strict; reject all offsets.
        if n_b%3==2:
            assert 2*n_b-1>=3*N0 and 2*n_s>=3*NM
        prefix.append(dict(j=j,endpoint_base=n_b,endpoint_slope=n_s,
                           F_base=f_b,F_slope=f_s,
                           direct_descent=False,source_capped_hit=False))
    assert (n_b,n_s)==(f_b,f_s)==(17300,19683)
    # Actual lawful reverse word, symbolic in all affine offsets:
    b,c=3*45+2,3*729
    for op in "OEOEOOOOO":
        if op=="E":
            b,c=2*b,2*c
        else:
            assert op=="O" and b%3==2 and c%3==0
            old_b,old_c=b,c
            b,c=(2*b-1)//3,(2*c)//3
            assert 3*b+1==2*old_b and 3*c==2*old_c
    assert (b,c)==(31,512)
    sampled=[]
    for z in (0,1,2,7,14):
        n,p=N0+NM*z,P0+PM*z
        assert 0<p<n
        y=n
        for _ in range(4):
            y=shortcut(y)
        v=p
        for _ in range(13):
            v=shortcut(v)
        assert y==v==17300+19683*z
        sampled.append(dict(offset=z,n=n,p=p,common=y))
    return prefix,sampled


def audit_frontier():
    residual_dyadic=[r for r in range(11,DYADIC,16)
                     if not candidates(r) and reverse_witness(r) is None]
    assert len(residual_dyadic)==31
    a_values=[45,774,1503]
    assert all(ternary_reverse(a) is None for a in a_values)
    new=[]
    for r in residual_dyadic:
        for a in a_values:
            n0=crt_base(r,a)
            assert n0%16==11 and n0%729==45
            assert old_v112_reverse_witness(n0) is None
            new.append(dict(dyadic_residue=r,ternary_residue=a,crt_source=n0))
    assert len(new)==93
    return residual_dyadic,new


def main():
    prefix,samples=audit_family()
    residual,new=audit_frontier()
    result=dict(
        schema="COLLATZ_V118_NEW_SOURCE_11_MOD16_F_MERGER",
        status="BOUNDED_EXACT_SYMBOLIC_CERTIFICATE",
        source_base=N0,source_slope=NM,
        predecessor_base=P0,predecessor_slope=PM,
        source_clock=4,predecessor_clock=13,
        no_original_direct_descent_prefix=4,
        no_strict_source_capped_hit_prefix=4,
        new_old_CRT_residue_classes_vs_V112=len(new),
        original_V112_remaining_unknown=164439,
        candidate_remaining_after_V118=164439-len(new),
        residual_dyadic_residues=residual,
        newly_covered_old_CRT_classes=new,
        exact_prefix=prefix,samples=samples,
        individual_93_lean_reified=False,
        global_collatz="UNKNOWN",qed=False)
    canonical=json.dumps(result,sort_keys=True,separators=(",",":"))
    result["payload_sha256"]=hashlib.sha256(canonical.encode()).hexdigest()
    print(json.dumps(result,sort_keys=True,indent=2))


if __name__=="__main__":
    main()
