# RIGID return-cycle fuel lemma — 18 September 2026

**Status: exact conditional algebra. Collatz remains unproved.**

This checkpoint isolates what a repeated same-anchor return-pattern cycle can and
cannot do. It builds on the exact return-cylinder and switch-transport algebra
already recorded on `collatz-rigid-component-termination-v1`.

## 1. Exact same-anchor return map

For any deterministic same-anchor return word (W), write

[
F_W(m)=\frac{A_Wm+B_W}{2^{D_W}},
qquad
C_W=2^{D_W}-A_W,
qquad
\Delta_W(m)=C_Wm-B_W.
]

For the episode language in this repository, (A_W) and (B_W) are odd and
(D_W>0), hence (C_W) is odd.

The exact return cylinder of (W) is equivalently

[
v_2(\Delta_W(m))\ge D_W+1.
]

The extra bit says that the quotient after division by (2^{D_W}) is odd, so
the word returns to the same episode anchor.

## 2. Exact defect transport

A direct calculation gives

[
\begin{aligned}
2^{D_W}\Delta_W(F_W(m))
&=C_W(A_Wm+B_W)-2^{D_W}B_W\\
&=A_W(C_Wm-B_W)\\
&=A_W\Delta_W(m).
\end{aligned}
]

Because (A_W) is odd, whenever (\Delta_W(m)\ne0),

[
\boxed{
v_2(\Delta_W(F_W(m)))
=
v_2(\Delta_W(m))-D_W.
}
]

So one complete replay of the same return word consumes exactly (D_W)
2-adic defect bits.

## 3. Finite replay theorem

Suppose the same exact return word can be executed successively from

[
m_0,m_1,\ldots,m_t,
qquad m_{i+1}=F_W(m_i),
]

and (\Delta_W(m_0)\ne0). Put

[
V=v_2(\Delta_W(m_0)).
]

Before each execution the exact-domain condition requires at least (D_W+1)
defect bits. After (i) executions the valuation is (V-iD_W). Therefore

[
V-(t-1)D_W\ge D_W+1,
]

and hence the number of executions is bounded by

[
\boxed{
t\le \left\lfloor\frac{V-1}{D_W}\right\rfloor.
}
]

Thus no non-fixed positive integer can execute one fixed exact return cycle
forever.

This applies equally to a composite cycle in the return-pattern switch graph:
compose all target return maps around the cycle to obtain another map

[
G(m)=\frac{Am+B}{2^D},
]

then use its own defect

[
\Delta_G(m)=(2^D-A)m-B.
]

## 4. The only zero-fuel exception is an actual periodic orbit

If

[
\Delta_W(m)=0,
]

then

[
m=\frac{B_W}{2^{D_W}-A_W}
]

and

[
F_W(m)=m.
]

Because the exact-domain condition is then satisfied at arbitrarily high
2-adic precision, this is not a bookkeeping recurrence: replaying the
deterministic return word gives a genuine periodic shortcut-Collatz orbit.

There is also an immediate sign deletion. Since (B_W>0), if

[
A_W>2^{D_W},
]

then (C_W<0), so the fixed point (B_W/C_W) is negative. Therefore an
expanding positive return cycle cannot have zero defect:

[
\boxed{
A_W>2^{D_W}, m>0
\Longrightarrow
\Delta_W(m)\ne0
\Longrightarrow
\text{finite replay fuel}.
}
]

For a contracting cycle (A_W<2^{D_W}), a positive zero-defect integer would
be a genuine nontrivial periodic-orbit obstruction and must be handled as such.

## 5. Consequence for the RIGID termination architecture

A repeated control cycle no longer needs to be forbidden combinatorially.
For a fixed concrete return cycle there are only two possibilities:

1. **nonzero defect:** it has a finite, exact natural-number replay budget,
   decreased by (D) on every traversal;
2. **zero defect:** it is a genuine positive periodic orbit.

Therefore the remaining recurrent RIGID problem separates into:

[
\boxed{
\text{aperiodic infinite novelty}
\quad\text{or}\quad
\text{a positive periodic orbit}.
}
]

The former must continually escape previously exhausted exact return cycles;
the latter is an actual Collatz-cycle obstruction rather than an abstraction
artifact.

This does **not** prove that only finitely many distinct return cycles can be
visited, and it does **not** exclude a positive nontrivial Collatz cycle.
Those are the remaining theorem boundaries.

## 6. Relation to the current executable audit

The current audit computes composite ((A,B,D)) data for observed concrete
pattern cycles and checks the same defect transport identity directly. It also
reports whether an observed cycle has enough initial valuation fuel to replay
more than once, and separately flags zero-defect cycles.

The executable checks are bounded discovery controls. The finite-replay lemma
above is algebraic and does not depend on a search horizon.
