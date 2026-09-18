# C9 three-replay t=153 family closure — 18 September 2026

**Status: exact symbolic family closure. Collatz remains unproved.**

The first discovered q=0-compatible non-direct reverse ancestor of a C9
three-replay endpoint occurred at

[
t=153,
qquad
x(t)=326575849+2^{29}t=82467825385,
]

with source

[
n=30098547115
]

satisfying

[
n<2^{35},qquad n<x,qquad T^{35}(n)=x.
]

So this is genuinely q=0-compatible and non-direct at the endpoint.

However the full hereditary audit shows

[
oxed{T^5(n)=25395649129<n}.
]

Therefore the source is already closed before q=0 and is not a hereditary
q=0 residual.

The local q=0 birth classifier is nevertheless RIGID. This cleanly separates:

* **local birth status**: RIGID at depth 35;
* **hereditary survival**: false, because a prefix descent exists at depth 5.

## Infinite reverse-word family

The 35-step parity word is

[
W=	exttt{OOEOEOEOOOOEEOOEEOOOOOOOOEOOOEOEEOE},
]

containing 23 odd steps.

For this word,

[
2^{35}x=3^{23}n+526178937575.
]

With

[
x(t)=326575849+2^{29}t,
]

integrality of (n) forces the unique residue

[
oxed{tequiv153pmod{3^{23}}}.
]

Thus every nonnegative source in this fixed reverse-word family is

[
oxed{
t_s=153+3^{23}s,qquad
n_s=30098547115+2^{64}s.
}
]

All such sources share the first five parity symbols (	exttt{OOEOE}), and
the exact prefix identity is

[
oxed{32T^5(n_s)=27n_s+23}.
]

Hence

[
32(n_s-T^5(n_s))=5n_s-23>0
]

for every positive source in the family, so

[
oxed{T^5(n_s)<n_s}.
]

Therefore the entire infinite t=153 reverse-word family is closed by direct
descent before q=0.

## Consequence

This kills the first apparent three-replay non-direct separator not by a
finite exception list but by an infinite arithmetic family theorem.

The authoritative three-replay residual is therefore narrower:

> find a q=0-compatible non-direct reverse ancestor whose **entire pre-q0
> history** is lower-merge-free.

Local non-direct ancestry alone is insufficient.
