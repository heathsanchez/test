# C9 periodic Bellman-geodesic checkpoint — 18 September 2026

**Status: exact finite evidence and a failed induction attempt. Collatz remains unproved.**

This checkpoint records a strong recurring Complete-O pattern but deliberately
does **not** claim the pattern is optimal for every repetition count.

## The return block

The concrete C9 same-anchor return block has reverse Complete-O exponent word

[
W=(2,2,1,1,1,2).
]

It has six reverse odd actions and total cost (S(W)=9). Its reverse cocycle
is (C(W)=1151), hence

[
R_W(y)=rac{512y-1151}{729},
qquad
H(x)=rac{729x+1151}{512}
]

for the inverse/forward block pair. One-block terminal legality is

[
yequiv334pmod{729}.
]

A complete enumeration of positive six-tuples with total cost at most 9 shows
that (W) is the unique legal six-action word at this residue with cost
(le9).

## Exact finite Bellman evidence

An independent Complete-O reconstruction of the exact repeated C9 cylinders
found the unique optimum

[
W^t
]

with total cost (9t) for every tested repetition count

[
t=1,2,ldots,8.
]

The recovered words are literally eight concatenated copies of
((2,2,1,1,1,2)), not merely equal-score alternatives.

Thus the strong empirical statement is:

[
oxed{	ext{C9 repeated cylinders remain exactly RIGID through }t=8.}
]

This already disproves any small fixed pumping threshold.

## Why the naive induction is invalid

A tempting argument is: terminal-prefix legality forces the first six reverse
actions to be legal at the one-block residue; those six actions cost at least
9; therefore strip (W) and induct.

That argument has a gap.

A global competitor of total cost at most (9t) may spend **more than 9** on
its first six actions and compensate by spending **less than 9 per six
actions later**. The one-block base theorem does not rule out this transfer of
budget between blocks.

Therefore one-block uniqueness does not by itself imply uniqueness of
(W^t).

A valid universal proof would need an additive/telescoping lower bound, a
potential on intermediate 3-adic states, or another argument showing that
total cost over every (6t)-action competitor is at least (9t).

## Positive block geometry

For positive (x),

[
H(x)-x=rac{217x+1151}{512}>0.
]

So the C9 block endpoints themselves are expanding, not direct descent.

The nested infinite C9 cylinder nevertheless converges 2-adically to the
negative rational fixed point

[
x_*=-rac{1151}{217},
]

equivalently (m_*=-467/217) in the episode coordinate. Hence one fixed
positive integer cannot execute C9 forever even though arbitrarily long finite
repetition is possible.

## Current theorem boundary

The correct open subproblem is now:

[
oxed{
	ext{prove or refute }
operatorname{OptCost}(W^t)=9t
	ext{ for all }t.
}
]

Even if that periodic optimality is universal, it would be an obstruction to
Bellman pumping rather than a route to Collatz. The broader termination target
remains control of **fuel regeneration across changes of return pattern**.
