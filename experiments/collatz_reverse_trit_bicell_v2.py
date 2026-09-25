#!/usr/bin/env python3
"""Progressive intrinsic Q2-prefix refinement of the first-resonance Q3 residual.

Parent V1 leaves 27 first-difference cells after restoring endpoint parity.
This V2 does not add a new certificate family.  It composes:
  * the exact Q3 first-difference residual from V1,
  * progressively deeper exact Q2 forward-prefix cylinders, and
  * the existing coefficient-contracting reverse-predecessor compiler.

For a fixed Q2 prefix of length a, every k<=a shortcut step is affine:
    z = (3^q y + B) / 2^k.
The parent Q3 residue y mod 3^j transports to z mod 3^(j+q).
From z we reuse the exact reverse compiler.  A composed certificate is
accepted only when it proves uniformly for y>=L:
    0 < p < y-G <= n,
where G is the already-certified first-resonance near-return gap.

This is an exact symbolic residual-refinement experiment, not a Collatz proof.
"""
from __future__ import annotations
import argparse, json
from pathlib import Path

import collatz_reverse_trit_separator_v0 as v0
import collatz_reverse_trit_bicell_v1 as v1

G=v0.G
L=v0.L
DEPTH=v0.DEPTH


def parent_residuals():
    acts,_,_=v0.extremal_reverse_actions()
    out=[]
    for j in range(1,DEPTH+1):
        qj=v0.terminal_residue(tuple(acts[:j]))
        base=qj%(3**(j-1)) if j>1 else 0
        qdigit=(qj//(3**(j-1)))%3
        for digit in range(3):
            if digit==qdigit:
                continue
            r=base+digit*3**(j-1)
            direct=v0.best_contracting_prefix(r,j)
            for parity in (0,1):
                kind=None
                if direct is not None:
                    kind="DIRECT_REVERSE"
                elif r%3==0:
                    kind="IMPOSSIBLE_ENDPOINT_MOD3"
                elif v1.one_step_reverse_cert(r,j,parity) is not None:
                    kind="ONE_FORWARD_THEN_REVERSE"
                if kind is None:
                    out.append(dict(
                        depth=j, first_difference_depth=j-1,
                        centre_digit=qdigit, alternate_digit=digit,
                        residue=r, modulus=3**j, parity=parity))
    assert len(out)==27
    assert all(x["parity"]==1 for x in out)
    return out


def forward_affine(q2res:int,k:int):
    """Return A,B with T^k(y)=(A*y+B)/2^k on y=q2res mod 2^k."""
    A=1;B=0;x=q2res
    for t in range(k):
        if x&1:
            A=3*A
            B=3*B+(1<<t)
            x=(3*x+1)//2
        else:
            x//=2
    assert (A*q2res+B)%(1<<k)==0
    return A,B,x


def crt_residue(r3:int,m3:int,r2:int,m2:int):
    t=((r2-r3)*pow(m3,-1,m2))%m2
    return (r3+m3*t)%(m2*m3)


def max_reverse_budget(A:int,k:int,o:int):
    rhs=(1<<k)*(3**o)
    S=0
    # More than enough: log2(3)<2.
    for s in range(1,k+2*o+3):
        if (1<<s)*A < rhs:
            S=s
        else:
            break
    return S


def replay_reverse(z:int,w):
    x=None
    # Build p directly from the cocycle then independently replay.
    S,C=v0.cocycle(w)
    den=3**len(w)
    num=(1<<S)*z-C
    if num%den:
        return None
    p=num//den
    x=p
    for a in reversed(w):
        if not (x&1):
            return None
        x=(3*x+1)//2
        for _ in range(a-1):
            if x%2:
                return None
            x//=2
    return p if x==z else None


def composed_certificate(cell,q2res,a):
    """Try all exact forward prefix lengths k<=a, then existing reverse certs."""
    j=cell["depth"]; r=cell["residue"]
    m3=3**j
    m2=1<<a
    assert q2res%m2==q2res and q2res&1

    # Sample only for independent replay; all inequalities below are uniform.
    y0=crt_residue(r,m3,q2res,m2)
    period=m2*m3
    y=y0
    if y<L:
        y += ((L-y+period-1)//period)*period
    assert y%m3==r and y%m2==q2res

    z_sample=y
    for k in range(1,a+1):
        A,B,_=forward_affine(q2res%(1<<k),k)
        den2=1<<k
        z=(A*y+B)//den2
        assert (A*y+B)%den2==0
        # Independent concrete prefix replay.
        z_sample=y
        for _ in range(k):
            z_sample=z_sample//2 if z_sample%2==0 else (3*z_sample+1)//2
        assert z_sample==z

        # Cheapest possible closure: the forward endpoint itself is below y-G.
        gapcoef=den2-A
        if gapcoef>0:
            margin=gapcoef*L-B-den2*G
            if margin>0:
                assert 0<z<y-G
                return dict(kind="FORWARD_DESCENT",k=k,A=A,B=B,
                            sample_y=y,sample_z=z,uniform_margin_at_L=margin)

        q=v0.farey if False else None
        # A is exactly 3^q; q is its 3-adic exponent.
        tmp=A; qexp=0
        while tmp>1:
            assert tmp%3==0
            tmp//=3;qexp+=1
        prec=j+qexp
        P=3**prec
        zres=((A*r+B)*pow(den2,-1,P))%P
        assert z%P==zres

        for o in range(1,prec+1):
            budget=max_reverse_budget(A,k,o)
            if budget<o:
                continue
            ro=zres%(3**o)
            w=v0.contracting_word(o,ro,budget)
            if w is None:
                continue
            S,C=v0.cocycle(w)
            den3=3**o
            den=den2*den3
            lead=(1<<S)*A
            gap=den-lead
            if gap<=0:
                continue
            const=(1<<S)*B-C*den2
            positive=lead*L+const
            margin=gap*L-const-den*G
            if positive<=0 or margin<=0:
                continue
            p=replay_reverse(z,w)
            if p is None:
                continue
            # Exact combined affine check and target inequality.
            assert p*den==lead*y+const
            assert 0<p<y-G
            return dict(kind="FORWARD_THEN_REVERSE",k=k,qexp=qexp,
                        odd_inverse_steps=o,actions=list(w),S=S,C=C,
                        A=A,B=B,sample_y=y,sample_z=z,sample_p=p,
                        uniform_margin_at_L=margin)
    return None


def run(max_depth:int,output:Path):
    parents=parent_residuals()
    # State is (parent-index, q2 residue at current depth).
    live=[(i,1) for i in range(len(parents))]
    rows=[]
    first_separator=None

    for a in range(1,max_depth+1):
        if a>1:
            old=live
            live=[]
            bit=1<<(a-1)
            for i,s in old:
                live.append((i,s))
                live.append((i,s|bit))

        before=len(live)
        survivors=[]
        closed=0
        kinds={}
        for i,s in live:
            cert=composed_certificate(parents[i],s,a)
            if cert is None:
                survivors.append((i,s))
                if first_separator is None:
                    first_separator=dict(q2_depth=a,q2_residue=s,parent=parents[i])
            else:
                closed+=1
                kinds[cert["kind"]]=kinds.get(cert["kind"],0)+1
        live=survivors
        row=dict(q2_depth=a,input_cells=before,closed=closed,
                 residual=len(live),closure_kinds=kinds,
                 residual_parent_count=len({i for i,_ in live}),
                 first_residual=(dict(parent=parents[live[0][0]],q2_residue=live[0][1])
                                 if live else None))
        rows.append(row)
        print("DEPTH",json.dumps(row,sort_keys=True))
        if not live:
            break

    result=dict(
        schema="COLLATZ_REVERSE_TRIT_BICELL_V2",
        parent="collatz-reverse-trit-bicell-v1@3cc7b84a32a9f2ee22022d6849c2d5e150f1f50c",
        parent_residual_cells=len(parents),
        max_q2_depth=max_depth,
        depth_rows=rows,
        final_residual_cells=len(live),
        final_residual_parent_count=len({i for i,_ in live}),
        first_separator=first_separator,
        final_residual=[
            dict(parent=parents[i],q2_residue=s,q2_modulus=1<<rows[-1]["q2_depth"])
            for i,s in live[:200]
        ],
        verdict=("PASS_ALL_BIADIC_FIRST_DIFFERENCES_CLOSE"
                 if not live else "EXACT_Q2_PREFIX_SEPARATOR_REMAINS"),
        scope=("first-resonance V1 residual x exact endpoint Q2 prefixes; "
               "existing forward/reverse lower-merge certificates only; no Collatz theorem")
    )
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print("FINAL_RESIDUAL",len(live),"PARENTS",result["final_residual_parent_count"])
    print("VERDICT",result["verdict"])


if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--max-q2-depth",type=int,default=10)
    ap.add_argument("--output",type=Path,required=True)
    a=ap.parse_args()
    assert 1<=a.max_q2_depth<=16
    run(a.max_q2_depth,a.output)
