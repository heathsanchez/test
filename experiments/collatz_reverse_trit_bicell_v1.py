#!/usr/bin/env python3
"""Intrinsic Q2 x Q3 refinement of the live-resonance reverse-trit separator.

Parent V0 classified 40 first-difference Q3 cylinders using direct reverse
predecessors. This V1 restores the one Q2 parity bit of the endpoint y.

For each residual Q3 cylinder and each endpoint parity:
  * take the exact first shortcut step z=T(y);
  * use all Q3 precision transported through that step;
  * search an exact coefficient-contracting reverse word from z;
  * certify uniformly on y>=L that the resulting predecessor p satisfies
        p < y-G <= n,
    where n is the hypothetical live seed and 0 <= y-n <= G.

Thus p and n have a common future z and p<n: an exact lower merge.
Any unclosed parity cell is emitted explicitly.

Bounded/symbolic theorem-discovery audit only. No Collatz theorem.
"""
from __future__ import annotations
import argparse, json
from pathlib import Path

import collatz_reverse_trit_separator_v0 as v0

G=v0.G
L=v0.L
DEPTH=v0.DEPTH


def first_above_L(residue, modulus):
    return residue + ((L-residue + modulus-1)//modulus)*modulus


def one_step_reverse_cert(r:int, j:int, parity:int):
    """Uniform lower merge after the exact first forward step from y."""
    assert 1 <= j <= DEPTH
    M=3**j
    r%=M

    # CRT representative only for replay control; formulas below are uniform.
    mod2M=2*M
    y0=next(x for x in range(r, r+2*M, M) if x%2==parity)

    if parity==0:
        # z=y/2; Q3 precision stays j.
        prec=j
        P=3**prec
        zres=(r*pow(2,-1,P))%P
        def max_budget(o):
            # 2^(S-1) < 3^o
            return (3**o).bit_length()
        mode="EVEN"
    else:
        # z=(3y+1)/2; multiplication by 3 gains one known Q3 digit.
        prec=j+1
        P=3**prec
        zres=((3*r+1)*pow(2,-1,P))%P
        def max_budget(o):
            # 3*2^(S-1) < 3^o  <=> 2^(S-1) < 3^(o-1)
            if o<=1:
                return 0
            return (3**(o-1)).bit_length()
        mode="ODD"

    for o in range(1,prec+1):
        budget=max_budget(o)
        if budget < o:
            continue
        ro=zres%(3**o)
        w=v0.contracting_word(o,ro,budget)
        if w is None:
            continue
        S,C=v0.cocycle(w)
        den=3**o

        if parity==0:
            assert S>=1
            coeff=1<<(S-1)
            gapcoef=den-coeff
            const_num=-C
            # p=(coeff*y-C)/den
            positive_num=coeff*L-C
            margin=gapcoef*L+C-den*G
        else:
            assert S>=1
            h=1<<(S-1)
            coeff=3*h
            gapcoef=den-coeff
            const_num=h-C
            # p=(coeff*y + h-C)/den
            positive_num=coeff*L+h-C
            margin=gapcoef*L+C-h-den*G

        if gapcoef<=0 or positive_num<=0 or margin<=0:
            continue

        # Exact replay on first endpoint in this Q2xQ3 cell above L.
        # Need y with both residue r mod 3^j and chosen parity.
        step=2*M
        y=y0
        if y<L:
            y += ((L-y + step-1)//step)*step
        assert y%M==r and y%2==parity
        z=y//2 if parity==0 else (3*y+1)//2
        p=((1<<S)*z-C)//den
        assert ((1<<S)*z-C)%den==0
        assert 0<p<y-G

        x=p
        for a in reversed(w):
            assert x&1
            x=(3*x+1)//2
            for _ in range(a-1):
                assert x%2==0
                x//=2
        assert x==z
        assert (y//2 if parity==0 else (3*y+1)//2)==z

        return dict(
            mode=mode, odd_inverse_steps=o, actions=list(w), S=S, C=C,
            transported_residue=ro, transported_modulus=den,
            sample_y=y, sample_z=z, sample_p=p,
            uniform_margin_at_L=margin,
        )
    return None


def run(output:Path):
    acts,_,_=v0.extremal_reverse_actions()
    centre=[]
    cells=[]
    closed=0

    for j in range(1,DEPTH+1):
        qj=v0.terminal_residue(tuple(acts[:j]))
        if j>1:
            assert qj%(3**(j-1))==centre[-1]
        centre.append(qj)
        base=qj%(3**(j-1)) if j>1 else 0
        qdigit=(qj//(3**(j-1)))%3

        for digit in range(3):
            if digit==qdigit:
                continue
            r=base+digit*3**(j-1)

            direct=v0.best_contracting_prefix(r,j)
            for parity in (0,1):
                cert=None
                kind=None

                # A direct reverse predecessor ignores the Q2 bit.
                if direct is not None:
                    cert=direct
                    kind="DIRECT_REVERSE"
                elif r%3==0:
                    # Any shortcut orbit after at least one odd step is nonzero mod 3.
                    # The first dangerous resonance has Q>0 odd steps.
                    kind="IMPOSSIBLE_ENDPOINT_MOD3"
                    cert={"reason":"after any odd shortcut step, value is nonzero mod 3"}
                else:
                    cert=one_step_reverse_cert(r,j,parity)
                    if cert is not None:
                        kind="ONE_FORWARD_THEN_REVERSE"

                status="CLOSED" if kind is not None else "RESIDUAL"
                closed += status=="CLOSED"
                cells.append(dict(
                    depth=j, first_difference_depth=j-1,
                    centre_digit=qdigit, alternate_digit=digit,
                    residue=r, modulus=3**j, parity=parity,
                    status=status, closure_kind=kind, certificate=cert,
                ))

    residual=[x for x in cells if x["status"]=="RESIDUAL"]
    result=dict(
        schema="COLLATZ_REVERSE_TRIT_BICELL_V1",
        parent="collatz-reverse-trit-separator-v0",
        cells=len(cells), closed=closed, residual=len(residual),
        first_residual=residual[0] if residual else None,
        residual_cells=residual,
        verdict=("PASS_ALL_FIRST_DIFFERENCE_BICELLS_CLOSE"
                 if not residual else "EXACT_BICELL_SEPARATOR_REMAINS"),
        scope=("extremal live-resonance first-difference cylinders x endpoint parity; "
               "direct or one-forward reverse certificates; no universal Collatz claim"),
    )
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print("CELLS",len(cells),"CLOSED",closed,"RESIDUAL",len(residual))
    print("FIRST_RESIDUAL",json.dumps(result["first_residual"],sort_keys=True))
    for x in residual:
        print("RESIDUAL_CELL",json.dumps({k:x[k] for k in
              ("depth","first_difference_depth","alternate_digit",
               "residue","modulus","parity")},sort_keys=True))
    print("VERDICT",result["verdict"])


if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--output",type=Path,required=True)
    a=ap.parse_args()
    run(a.output)
