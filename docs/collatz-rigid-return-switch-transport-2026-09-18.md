# RIGID return-switch transport checkpoint — 18 September 2026

**Status: exact conditional algebra plus bounded executable controls. This is not
a Collatz proof.**

Work on `collatz-rigid-component-termination-v1` has reduced the recurrent
q=0 boundary problem to exact same-anchor return switches.

For a return word (W), write

[
F_W(m)=rac{A_Wm+B_W}{2^{D_W}},qquad
C_W=2^{D_W}-A_W,qquad
Delta_W(m)=C_Wm-B_W.
]

Here (A_W) and (C_W) are odd.  The exact return cylinder of (W) is
equivalently

[
v_2(Delta_W(m))ge D_W+1.
]

For two distinct deterministic first-return cylinders (W,V) at the same
anchor, let

[
J_{W,V}=(A_V-2^{D_V})B_W+C_WB_V,qquad
h=v_2(J_{W,V}).
]

Disjointness of the exact cylinders gives

[
v_2(Delta_W(m))=h
]

when (V) is the next return executed from (m).  If

[
v_2(Delta_V(m))=D_V+1+e,
]

then the exact three-way switch law is

[
e<h-1Rightarrowmathrm{drop},qquad
e>h-1Rightarrowmathrm{flat},qquad
e=h-1Rightarrowmathrm{recharge}.
]

## Switch-to-switch law

Because (V) transports its own defect with zero injection,

[
2^{D_V}Delta_V(F_V(m))=A_VDelta_V(m),
]

and (A_V) is odd.  Therefore, at the next visit to the same anchor,

[
v_2(Delta_V(m'))=1+e.
]

If the following return cylinder is a distinct (U), first-order separation
applied to (V,U) gives

[
oxed{h_{V,U}=e+1.}
]

Consequently, along consecutive distinct switches,

[
oxed{
egin{array}{c|c}
	ext{outcome }W	o V & h_{m next}\ hline
mathrm{drop} & <h\
mathrm{recharge} & =h\
mathrm{flat} & >h
end{array}}
]

This is an exact algebraic identity, not a statistical observation.

## Recharge forces a new pattern

For a recharge, (e=h-1), hence after executing (V),

[
v_2(Delta_V(m'))=h.
]

Distinct cylinder separation satisfies (h<D_V+1).  Therefore (m') is not
in the exact domain of (V) again.  Thus

[
oxed{	ext{after a recharge, the target return pattern cannot immediately repeat.}}
]

If another return to the anchor occurs, it must switch to a different pattern,
and its separation valuation is the same (h).

This explains why a recharge graph must retain the concrete second-order
valuation state: the same pair of return patterns can be flat on one visit and
recharge on another.

## Current bounded evidence

At source limit 8191 and depth 80 the exact RIGID-filtered census found 463
returns, 78 recharge occurrences, 17 distinct recharge-capable pattern edges,
and no directed cycle in the recharge-capable pattern graph.  This is bounded
evidence only.

The remaining universal problem is not to forbid recharge.  It is to prove
that no fixed positive integer can realize an infinite RIGID switch sequence
that avoids every lower-merge certificate.  The switch-to-switch law above is
the current minimal exact control state for that problem.
