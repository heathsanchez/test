# C9 high-fuel ladder checkpoint — 18 September 2026

**Collatz remains unproved.** This checkpoint records the exact C9 replay-fuel
progress on `collatz-rigid-component-termination-v1`.

The expanding same-anchor return cycle is

[
G(m)=rac{729m+467}{2^9}.
]

Put

[
C=2^9-729=-217,qquad Delta(m)=Cm-467.
]

For every exact replay,

[
v_2(Delta(G(m)))=v_2(Delta(m))-9.
]

Hence (r) consecutive replays require

[
v_2(Delta(m))ge 9r+1.
]

## Replay cylinders

The least positive cofactor residues are

[
egin{array}{c|c|c|c}
r & 	ext{required bits} & m_r & x_r=2m_r-1\ hline
1 & 10 & 885 & 1769\
2 & 19 & 234357 & 468713\
3 & 28 & 163287925 & 326575849
end{array}
]

with the corresponding residue understood modulo (2^{9r+1}) for (m)
and modulo (2^{9r+2}) for the odd episode endpoint (x).

## Million-source stage

For hereditary q=0 RIGID births below (2^{20}), the two-replay endpoint
cylinder did not occur at all. The closest states matched 17 low endpoint bits
but none matched 18.

That absence was **not universal**.

## 24-bit source stage: the separator

Extending to all odd sources below (2^{24}) produced 18-, 19-, and full
20-bit endpoint matches.

There are genuine live-RIGID two-replay hits. The six bounded dangerous hits
found are sources

[
5054715, 5686555, 6397375, 8529833, 9596063, 14394095.
]

All six hit exactly the same endpoint

[
oxed{x=157755113=468713+150cdot2^{20}}.
]

At that endpoint

[
m=78877557,qquad v_2(Delta(m))=19,
]

so the exact replay budget is exactly two. The two C9 replays are

[
78877557	o112308085	o159907411,
]

or in odd episode endpoints,

[
157755113	o224616169	o319814821.
]

A third replay is impossible from this state.

### Complete closure of the live two-replay endpoint

The endpoint itself satisfies

[
T^{36}(157755113)=2668133.
]

A separate exact finite gate checked every integer

[
2le nle2668133
]

and every one directly descends below itself (maximum first-descent time 224,
attained at 1126015 in that finite base).

Therefore **every positive source that ever hits 157755113 is closed**:

* if (n>2668133), the shared tail reaches (2668133<n);
* if (nle2668133), the finite base already supplies direct descent.

So all six observed live two-replay RIGID separators have an exact lower-merge
certificate despite surviving both C9 traversals.

## Three-replay level

Three replays require

[
mequiv163287925pmod{2^{28}},
]

equivalently

[
xequiv326575849pmod{2^{29}}.
]

A 16-shard prospective sweep over every odd source below (2^{24}), following
512 post-q0 boundary steps, found

[
oxed{	ext{RAW THREE-REPLAY HITS}=0}.
]

Thus there were also zero live-RIGID and zero dangerous three-replay hits in
that bounded universe.

The least three-replay endpoint (326575849) was then attacked from the
reverse direction. Through reverse depth 45:

[
egin{aligned}
	ext{max frontier} &=638356,\
q=0	ext{-compatible ancestors} &=20836,\
	ext{direct-descending ancestors} &=20836,\
	ext{non-direct ancestors} &=0.
end{aligned}
]

The first q=0-compatible reverse ancestor appears at depth 33 and is already
larger than the endpoint.

This is a bounded reverse-tree result, not a universal theorem.

## Near-miss dynamics

The unique million-range near miss that was still RIGID at the 17-bit match is
source 966655. It reaches

[
T^{26}(966655)=5580521
]

with only one C9 replay of fuel. It remains RIGID through a long aperiodic
return-switch sequence and finally exits by direct descent:

[
T^{99}(966655)=581864<966655.
]

So the missing fuel bit does not cause an immediate local breaker; it forces a
long novelty episode before discharge.

## Current theorem candidate and boundary

The statement

> “extra C9 replay fuel is incompatible with RIGID”

is false: the six two-replay survivors above are exact counterexamples.

What survives is the more structured ladder:

1. every fixed exact return cycle has finite 2-adic replay fuel unless it is a
   genuine fixed point;
2. higher replay count requires nine new exact 2-adic bits for C9;
3. two-replay RIGID survivors exist, but the first observed live endpoint is
   completely lower-merge closed;
4. three-replay fuel is absent from the (2^{24}) prospective source universe
   and from the searched non-direct reverse ancestry of the least endpoint.

The remaining universal target is therefore not “forbid replay”. It is:

[
oxed{
	ext{show that every arbitrarily deep replay-fuel lift either acquires a
lower merge or forces a new return structure, and that this recursive process
cannot continue forever for one fixed positive source.}
}
]

Any next candidate must survive the exact two-replay separator
(157755113) and the aperiodic near-miss source (966655).
