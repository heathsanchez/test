#!/usr/bin/env python3
"""Exact final zero-carry excursion audit on the protected Q18 residual.

This does two things only:
  1. extracts the last positive threshold-slack excursion before first crossing
     for the three reverse-irreducible record setters;
  2. checks the universal exponent boundary identity used by
     formal/Collatz/FinalExcursion.lean on those concrete traces.

It is theorem discovery/regression, not a universal Collatz proof.
"""
from __future__ import annotations
import json
from fractions import Fraction

from collatz_live_origin_bridge_v1 import language_counts

H = 1024
SOURCES = [13421671, 8088063, 63728127]
qmin, _, _ = language_counts(H)


def T(x: int) -> int:
    return (3*x+1)//2 if x & 1 else x//2


def trace_to_cross(n: int):
    y=n; q=0
    rows=[{"j":0,"y":n,"q":0,"h":0,"bit":None,"delta":None}]
    for j in range(1,H+1):
        bit=y&1
        y=T(y); q+=bit
        delta=qmin[j]-qmin[j-1]
        rows.append({"j":j,"y":y,"q":q,"h":q-qmin[j],
                     "bit":bit,"delta":delta})
        if q<qmin[j]:
            return rows
    raise AssertionError(("no first crossing",n))


def affine_word(word: str):
    # 2^D F(x) = A*x+B on the declared parity cylinder.
    A=1; B=0; D=0
    for ch in word:
        if ch=="1":
            A=3*A
            B=3*B+(1<<D)
        D+=1
    return A,B,D


def audit(n: int):
    tr=trace_to_cross(n)
    d=tr[-1]["j"]; e=d-1
    assert tr[d]["h"] == -1
    assert tr[e]["h"] == 0
    assert tr[d]["bit"] == 0
    assert tr[d]["delta"] == 1

    # Nearest prior zero boundary. If the interval is nontrivial, its interior
    # is positive by construction.
    zeros=[j for j in range(e) if tr[j]["h"]==0]
    assert zeros
    s=zeros[-1]
    interior=[tr[j]["h"] for j in range(s+1,e)]
    positive_excursion=bool(interior) and min(interior)>0
    word="".join(str(tr[j]["bit"]) for j in range(s+1,e+1))

    A,B,D=affine_word(word)
    ys=tr[s]["y"]; ye=tr[e]["y"]; yd=tr[d]["y"]
    qs=tr[s]["q"]; qe=tr[e]["q"]; r=qe-qs
    assert D == e-s
    assert A == 3**r
    assert (1<<D)*ye == A*ys+B

    # For a genuine positive excursion, h_{s+1}>0 forces threshold-flat
    # start, while first crossing forces threshold increment after e.
    if positive_excursion:
        assert tr[s+1]["delta"] == 0 and tr[s+1]["bit"] == 1
        assert (1<<(s+1)) <= 3**qs
        assert 3**qe < (1<<(e+1))
        assert A < (1<<D)

    # The current exact residual records all fire direct descent on the next
    # even crossing step.
    assert ye == 2*yd
    assert yd < n
    assert ye < 2*n

    denom=(1<<D)-A
    fixed=None if denom<=0 else Fraction(B,denom)
    return {
      "n":n,
      "start_boundary":s,
      "end_boundary":e,
      "crossing":d,
      "word":word,
      "positive_excursion":positive_excursion,
      "A":A,"B":B,"D":D,
      "slope":[A,1<<D],
      "fixed_point":None if fixed is None else [fixed.numerator,fixed.denominator],
      "start_endpoint":ys,
      "end_boundary_endpoint":ye,
      "crossing_endpoint":yd,
      "start_over_source":[ys,n],
      "end_over_source":[ye,n],
      "coefficient_contracts":A < (1<<D),
      "end_below_2source":ye < 2*n,
      "direct_descent_next_step":yd < n,
    }


rows=[audit(n) for n in SOURCES]
assert all(r["positive_excursion"] for r in rows)
assert [r["word"] for r in rows] == ["1111110100100","10","10"]

print(json.dumps({
  "schema":"COLLATZ_FINAL_ZERO_CARRY_EXCURSION_V1",
  "sources":SOURCES,
  "rows":rows,
  "warranted_general_algebra":
    "zero-carry positive excursion boundary inequalities force 3^r < 2^L",
  "bounded_residual_observation":
    "all three Q18 reverse-irreducible record setters have a contractive final positive excursion whose output is <2n, hence the next forced even crossing step descends below n",
  "remaining_universal_obligation":
    "derive the additive/source-relative inequality end_boundary_endpoint < 2*n (or another lower-source certificate) for every actual lower-merge-free final boundary phase; multiplicative contraction alone does not imply it",
  "global_collatz":"UNKNOWN"
},indent=2))
