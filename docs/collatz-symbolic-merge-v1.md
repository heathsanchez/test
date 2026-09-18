# Symbolic lower-merge portfolio V1

## Verified extension

For a checked cylinder n=2^k q+b, T^k(n)=3^c q+d=y, when c>=1 and d=2 mod 3,
the entire endpoint family has integral odd predecessor

    p(q)=2*3^(c-1)*q+(2*d-1)/3,    T(p(q))=y(q).

Let a=2*3^(c-1), h=(2*d-1)/3 and A=2^k-a. If A>0, the exact lower-merge
threshold is Q=max(0,floor((h-b)/A)+1). The verifier checks positivity at Q,
the strict threshold, uniform odd parity, and both coefficients of 3p+1=2y.
It separately reconstructs the source's full affine cylinder map. Thus every
q>=Q with n>1 has p<n and T(p)=T^k(n). This is a lower merge even if y>=n.

The existing direct-descent constructor remains first in the portfolio. The
new constructor is tried only when direct descent does not give a tail. Every
finite exception is retained; capped scalar proof search leaves failure UNKNOWN.
The full prefix partition audit rejects missing or overlapping cylinders.

## Same-depth comparison

| Quantity, depth 18 | Direct descent | With inverse-odd lower merge |
|---|---:|---:|
| Certificate leaves | 1752 | 1374 |
| Unresolved depth-18 cylinders | 7495 | 6342 |
| Closed sources in 65537..131072 | 63673 | 63950 |
| Unresolved evaluation sources | 1863 | 1586 |

The new bank contains 999 descent and 375 inverse-odd certificates. Earlier
closure replaces some deeper descent leaves. The residual loses 1153 cylinders
(about 15.38%); its exact residue density is 6342/262144. The evaluation interval
gains 277 lower merges. No positive scalar exceptions occur in this run.

Every new residual residue is checked to belong to the old residual set.
Every previously closed evaluation source stays closed. Every portfolio closure
is independently replayed: the source reaches y and its proposed smaller
predecessor reaches the same y (or equals y for direct descent). Qualification
uses 168022 forward steps. Serialization/reload preserves all applications.
Removing the inverse-odd constructor recovers the direct-only comparison.

## Claim boundary

This compiles an already known constructor into the exact frontier; it does not
claim discovery of the inverse-odd identity. The certificate guards cover infinite
families, but the comparison depth and evaluation interval are bounded. These
are Python exact-arithmetic checks, not Lean certification. The 6342 residual
cylinders remain open, including the persistent all-odd family. Neither density
reduction nor finite replay establishes universal termination. No overall speed
advantage is claimed. The S_k obstruction, 119/104 audit and departure-countdown
evidence are untouched.

## Reproduce

```
python -m unittest discover -s experiments -p 'test_collatz_symbolic*.py' -v
python experiments/collatz_symbolic_merge.py --depth 18 --output /tmp/symbolic-merge
```
