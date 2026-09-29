#!/usr/bin/env python3
"""Crystal V24: exact uniform affine reverse-word audit for the sole V23 cell.

Cell:
  n(t) = N + L t,  t >= 0
  N = 38911100780481085467
  L = 2^59 * 3^8

The fixed first 59 shortcut steps yield
  y(t) = Y + 3^46 t.

A uniform reverse word is built from:
  E(z) = 2 z
  O(z) = (2 z - 1)/3
where O is allowed only when it is an integer for every t.  If o odd-inverse
steps and e even lifts have been used, the t-coefficient is
  3^46 * 2^(e+o) / 3^o = 2^(e+o) * 3^(46-o).

For p(t) < n(t) for every t>=0, a necessary condition is coefficient(p) <= L.
Each O consumes one factor of 3 and E never restores one, so o<=46.  The
coefficient inequality then bounds e finitely (global maximum 25).

This script exhausts every uniform affine reverse word that could possibly
satisfy coefficient(p)<=L.  It reports all nonexpanding candidates and checks
whether any gives p(t)<n(t) uniformly.

This is an exact symbolic audit of schema #6/#13 at the first fixed interface.
It is not a Collatz proof and makes no claim about later nonuniform/split
constructors or SCC/cycle arguments.
"""
from collections import defaultdict
import json

N = 38911100780481085467
L = (1 << 59) * (3 ** 8)
Y = 91182490942926966077
A = 3 ** 46

def T(x:int)->int:
    return (3*x+1)//2 if x&1 else x//2

# Recheck the 59-step affine interface exactly.
x=N
q=0
for k in range(59):
    if x&1:
        q += 1
    x=T(x)
assert x == Y
assert q == 38
assert L == (1 << 59) * (3 ** 8)

# Max total E allowed by the necessary coefficient inequality at each o.
max_e_by_o = {}
for o in range(47):
    e=-1
    for z in range(0,200):
        lhs=A * (1 << (z+o))
        rhs=L * (3 ** o)
        if lhs <= rhs:
            e=z
        else:
            break
    max_e_by_o[o]=e

admissible_o=[o for o,e in max_e_by_o.items() if e>=0]
assert admissible_o[0] == 38
assert admissible_o[-1] == 46
GLOBAL_E_MAX=max(max_e_by_o.values())
assert GLOBAL_E_MAX == 25

# dp[E][constant] = one exact reverse word after current number o of O steps.
# Coefficient depends only on (o,E), so exact duplicate constants are identical
# affine states and can be safely merged.
dp={0:{Y:""}}
max_states=1
candidate_rows=[]
level_counts=[]

for o in range(0,46):
    nd=defaultdict(dict)
    o2=o+1
    for E,cmap in dp.items():
        for c,w in cmap.items():
            r=c%3
            if r==0:
                continue
            parity=0 if r==2 else 1
            # Every e with the required parity and total E within the exact
            # coefficient-derived global bound is enumerated.
            for e in range(parity, GLOBAL_E_MAX-E+1, 2):
                E2=E+e
                ce=c << e

                # Uniform O-admissibility for the whole affine family.
                coeff_before=A * (1 << (E2+o))
                assert coeff_before % (3 ** o) == 0
                coeff_before//=3**o
                if ce%3 != 2 or coeff_before%3 != 0:
                    continue

                nc=(2*ce-1)//3
                na=(2*coeff_before)//3
                nw=w + ("E"*e) + "O"

                # If coefficient already fits, this is a genuine candidate
                # endpoint for a uniform lower/equal source.
                if na <= L:
                    candidate_rows.append({
                        "odd_inverse_steps":o2,
                        "even_lifts":E2,
                        "constant":nc,
                        "coefficient":na,
                        "constant_delta":nc-N,
                        "coefficient_delta":na-L,
                        "word":nw,
                        "uniform_lower_source": nc < N,
                        "uniform_equal_source": nc == N and na == L,
                    })

                # Exact viability prune: even if every remaining possible O is
                # taken with zero additional E, can the coefficient ever fall
                # to <= L? If not, no descendant can be a candidate.
                rem=46-o2
                if na * (2 ** rem) > L * (3 ** rem):
                    continue

                if nc not in nd[E2]:
                    nd[E2][nc]=nw

    dp=dict(nd)
    states=sum(len(v) for v in dp.values())
    max_states=max(max_states,states)
    level_counts.append({
        "odd_inverse_steps":o2,
        "states":states,
        "E_values":sorted(dp),
    })
    if not dp:
        break

lower=[r for r in candidate_rows if r["uniform_lower_source"]]
equal=[r for r in candidate_rows if r["uniform_equal_source"]]

assert lower == []
assert len(equal) == 1
identity=equal[0]
assert identity["odd_inverse_steps"] == 38
assert identity["even_lifts"] == 21
assert len(identity["word"]) == 59

# Independent replay of the reverse word at t=0 and t=1.
def reverse_apply(y:int, word:str)->int:
    z=y
    for op in word:
        if op=="E":
            z*=2
        else:
            assert op=="O"
            assert z%3==2
            z=(2*z-1)//3
    return z

for t in (0,1):
    n=N+L*t
    y=Y+A*t
    assert reverse_apply(y,identity["word"]) == n

result={
    "schema":"COLLATZ_CRYSTAL_AFFINE_REVERSE_CELL_V24",
    "cell":{
        "N":N,
        "L":L,
        "source":"N + L*t",
        "t_domain":"t>=0",
    },
    "fixed_interface":{
        "depth":59,
        "odd_steps":38,
        "Y":Y,
        "coefficient":A,
        "endpoint":"Y + 3^46*t",
    },
    "finite_exhaustion":{
        "max_uniform_odd_inverse_steps":46,
        "global_max_even_lifts_for_nonexpanding_coefficient":GLOBAL_E_MAX,
        "max_dynamic_states":max_states,
        "levels":level_counts,
    },
    "nonexpanding_candidates":candidate_rows,
    "uniform_lower_source_candidates":len(lower),
    "uniform_equal_source_candidates":len(equal),
    "unique_equal_candidate":identity,
    "verdict":"NO_UNIFORM_LOWER_SOURCE_AT_FIRST_AFFINE_INTERFACE",
    "interpretation":(
        "Schema #6/#13 does not close the V23 cell at the first fixed 59-step "
        "interface. The only uniform affine reverse word whose coefficient does "
        "not exceed the source coefficient is the exact inverse of the source's "
        "own 59-step prefix, yielding p(t)=n(t). The next justified move is an "
        "SCC/cycle/return analysis or a later-interface constructor, not more "
        "one-shot reverse-word search at this interface."
    ),
    "universal_scope":"exact for uniform affine reverse words from the fixed 59-step interface",
    "global_collatz":"UNKNOWN",
}
print(json.dumps(result,indent=2))
