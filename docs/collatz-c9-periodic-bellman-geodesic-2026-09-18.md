# C9 periodic Bellman-geodesic obstruction — 18 September 2026

**Status: exact algebraic theorem plus a finite base check. Collatz remains unproved.**

This checkpoint closes the proposed "Bellman precision pumping" route in its
strong form.

## The return block

The concrete C9 same-anchor return block has reverse Complete-O exponent word

[
W=(2,2,1,1,1,2).
]

It has six reverse odd actions and total cost

[
S(W)=9.
]

Its reverse cocycle is

[
C(W)=1151,
]

so the exact reverse map is

[
R_W(y)=rac{512y-1151}{729}.
]

Equivalently the forward 9-step block map on the odd episode endpoint is

[
H(x)=rac{729x+1151}{512}.
]

The terminal legality residue for one block is

[
yequiv 1151cdot512^{-1}equiv334pmod{729}.
]

## Finite base theorem

Enumerate every positive six-tuple
[
(a_1,ldots,a_6),qquad sum a_ile9.
]

Terminal legality at the residue (334mod729) holds for exactly one such
word:

[
oxed{(2,2,1,1,1,2)}.
]

No legal six-action word has cost below 9, and (W) is the unique legal word
at cost 9.

This is a finite check over the compositions of totals 6,7,8,9.

## Induction theorem

Let (W^t) denote (t) concatenated copies of (W). Consider any endpoint
residue for which (W^t) is legal.

Claim:

[
oxed{
W^t	ext{ is the unique legal }6t	ext{-action word of total cost }le9t.
}
]

Proof is by induction on (t).

For any legal competing (6t)-action word, terminal legality implies legality
of every prefix. In particular its first six reverse actions are legal modulo
(3^6=729). The endpoint residue modulo 729 is the one-block C9 residue 334.
By the finite base theorem, those first six actions cost at least 9, with
equality only for (W).

If they cost more than 9, the total word cannot have cost at most (9t) once
the remaining (6(t-1)) positive actions are accounted for in an optimal
competitor. If they cost exactly 9, the prefix is exactly (W). Applying
(R_W) leaves the endpoint residue for (W^{t-1}). The induction hypothesis
forces the remaining reverse word to be (W^{t-1}), with cost (9(t-1)).

Hence the unique optimum is (W^t), with total cost (9t).

## Consequence

At the block endpoints of the positive C9 repeated family, Complete-O cannot
eventually discover a cheaper reverse reconstruction merely because the return
precision grows.

The corresponding forward block satisfies

[
H(x)-x=rac{217x+1151}{512}>0
qquad(x>0),
]

so the positive block endpoints are not direct descents either.

Therefore arbitrarily long periodic Bellman-geodesic RIGID chains exist:

[
oxed{
	ext{unbounded return precision does not imply eventual Bellman improvement.}
}
]

This is a structural obstruction, not a bounded counterexample.

It does not imply that one fixed positive ordinary integer can follow C9
forever. The nested C9 cylinders converge 2-adically to the negative rational
fixed point

[
x_*=-rac{1151}{217},
]

equivalently (m_*=-467/217) in the episode coordinate. Every fixed positive
integer has only finite C9 replay fuel.

Thus the remaining termination target is not Bellman pumping of one repeated
return word. It is control of **fuel regeneration across changes of return
pattern**.
