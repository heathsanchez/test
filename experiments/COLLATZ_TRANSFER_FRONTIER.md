# Collatz transfer frontier: first dangerous coefficient contraction

## Exact setup

For the shortcut map

[
T(n)=egin{cases}
n/2,&n	ext{ even},\
(3n+1)/2,&n	ext{ odd},
end{cases}
]

a parity prefix of length (t) with (q) odd steps has

[
T^t(n)=rac{3^q n+A}{2^t}.
]

At a **first coefficient contraction**,

[
3^q<2^t,
qquad
3^{q_s}ge 2^squad(s<t).
]

If the odd positions are (p_1<cdots<p_q), then survival before the
(j)-th odd step implies

[
2^{p_j}le 3^{j-1}.
]

Since

[
A=sum_{j=1}^q2^{p_j}3^{q-j},
]

the intercept is maximized by delaying every odd step as far as the
barrier permits:

[
p_j^{max}=lfloor (j-1)log_2 3floor.
]

In particular,

[
A<q3^{q-1}.
]

Thus the largest possible seed rescued at a first contraction satisfies

[
x_*=rac{A}{2^t-3^q}
<
rac{q}{3(e^epsilon-1)}
<
rac{q}{3epsilon},
qquad
epsilon=tln2-qln3>0.
]

## Farey collapse of all earlier crossing depths

Let

[
rac{6,586,818,670}{10,439,860,591}<alpha=rac{ln2}{ln3}
<
rac{65,470,613,321}{103,768,467,013}.
]

These two fractions are Farey neighbors: their cross determinant is (1).
Therefore no rational strictly between them has denominator below the
sum of their denominators.

Their mediant is

[
rac{72,057,431,991}{114,208,327,604}.
]

The exact rational-log certificate in
`experiments/collatz_transfer_farey.py` proves that every lower rational
(q/t<alpha) with

[
t<114,208,327,604
]

has a rescue ceiling strictly below

[
L=2075,2^{60}=2,392,312,122,059,207,475,200.
]

Hence:

[
oxed{	ext{Any live seed whose first coefficient contraction occurs before }
114,208,327,604	ext{ must descend there.}}
]

This collapses roughly (114) billion potential crossing depths to one
first unresolved resonance.

## Rigorous live-resonance ceiling

For the latest-odd extremal word,

[
rac{A_q}{3^q}
=
sum_{j=0}^{q-1}rac13,2^{-{jlog_2 3}}.
]

At the live resonance, (q=72,057,431,991) is the sum of two consecutive
continued-fraction denominators for the rotation by (log_2 3).
For (f(x)=rac13 2^{-x}),

[
int_0^1 f(x),dx=rac{1}{6ln2},
qquad
operatorname{Var}(f)=rac13.
]

Applying Denjoy–Koksma to the two convergent blocks gives

[
rac{A_q}{3^q}
le
rac{q}{6ln2}+rac23.
]

Together with (e^epsilon-1geepsilon), the exact rational certificate
gives the safe live-resonance ceiling

[
oxed{nle 3,143,983,941,795,894,239,301}
]

for any seed rescued at that first dangerous crossing.

This is a theorem-level contraction of the live interval, not an
equidistribution heuristic.

## Remaining residual

A hypothetical live counterexample must therefore both:

1. avoid coefficient contraction for at least (114,208,327,604)
   shortcut steps, **or** survive exactly at the first dangerous resonance;
2. lie in the much smaller seed interval
   [
   2,392,312,122,059,207,475,200
   le nle
   3,143,983,941,795,894,239,301.
   ]

The next representation should exploit the fact that only 72 seed bits
must encode a parity history satisfying this enormous positive-drift
constraint.
