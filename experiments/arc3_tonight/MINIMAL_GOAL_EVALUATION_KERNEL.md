# Minimal GOAL-Evaluation Kernel (Canonical)

## Primitive

Let A be the action alphabet and M=A* the continuation monoid.

Let H be the set of executable histories/prefixes and let V0 be the independent external authority.

Define the task evaluation pairing

[
e_G:H\times M\to\{0,1\}
]

by

[
e_G(h,t)=1 \iff V_0(h\circ t)=\mathrm{GOAL}.
]

Curry:

[
\Phi_G(h)=e_G(h,-).
]

The exact task-state relation is

[
h_1\sim_G h_2
\iff
\Phi_G(h_1)=\Phi_G(h_2)
\iff
\forall t\in M: e_G(h_1,t)=e_G(h_2,t).
]

Thus

[
\mathrm{State}_G=H/\ker\Phi_G.
]

This is the coarsest exact representation sufficient for GOAL consequence.

## Important asymmetry

Environmental difference is not task-state difference.

A variable, observation, frame feature, resource count, memory bit, latent state, or prediction is retained in task identity only if some future GOAL consequence requires it.

A witnessed environmental separator is therefore only a candidate task distinction.

It becomes a task distinction only after a continuation t is found with

[
e_G(h_1,t)\ne e_G(h_2,t).
]

Otherwise the correct status is UNKNOWN or bounded-equivalent, not automatic state growth.

## Finite developmental object

At time t the kernel stores only

[
K_t=(P_t,S_t,H_t,C_t)
]

where

- P_t is a finite set of access histories/prefixes,
- S_t is a finite set of earned test continuations/suffixes,
- H_t:P_t\times S_t\to\{0,1,?\} is the partial GOAL evaluation table,
- C_t records full acquisition/replay cost and provenance.

Rows with the same known GOAL signature are provisionally merged.

For p in P_t,

[
\rho_t(p)=\big(H_t(p,s)\big)_{s\in S_t}.
]

Provisional equivalence:

[
p\equiv_t q
\iff
\forall s\in S_t:\ H_t(p,s)=H_t(q,s)
]

on jointly known cells.

Each provisional row class keeps only its cheapest warranted access histories, or its nondominated access frontier when costs are genuinely multidimensional.

Columns are retained only when they distinguish at least one pair of surviving rows or directly witness GOAL.

## Development

Every queried cell is an externally grounded experiment.

Given unresolved compatible completions Omega_t of the partial table:

1. If a tested cell is GOAL, independently replay the full continuation and compile the cheapest verified witness.
2. Otherwise choose the cheapest admissible query (p,s) whose possible outcomes make surviving hypotheses disagree about a GOAL-relevant distinction or winning continuation.
3. Execute p∘s against V0.
4. Record the cell.
5. If the observation separates two provisional rows by GOAL consequence, split them.
6. If a row distinction has no remaining distinguishing column under certified closure, merge it.
7. If a column is redundant under the current table/closure, delete it.
8. If two access histories occupy the same task row, keep the cheapest/nondominated representative.
9. Repeat.

The optimization target is not state reconstruction, prediction accuracy, novelty, or model completeness.

It is

[
\min C(w)
\quad\text{s.t.}\quad
V_0(w)=\mathrm{GOAL}.
]

Everything retained in the kernel is subordinate to reducing the expected future cost of finding such a verified continuation.

## The sparse Hankel view

Define the winning language

[
G=\{w\in A^*:V_0(w)=\mathrm{GOAL}\}.
]

Then

[
\mathcal H(p,s)=\mathbf 1[ps\in G]
]

is the GOAL Hankel/observation matrix.

Rows are task states (residual winning languages).
Columns are probes/distinguishing continuations.
Duplicate rows are redundant states.
Duplicate columns are redundant tests.

The kernel does not need to reconstruct the complete matrix.

It must reveal only enough cells to expose a verified 1.

## UNKNOWN

Under finite evidence, do not identify the true kernel with the current observed row partition.

Let Omega_t be all continuation-closed GOAL behaviors consistent with verified cells.

For histories p,q:

- EQ if every completion in Omega_t gives Phi(p)=Phi(q),
- SEP if every completion separates them,
- UNKNOWN otherwise.

A single verified GOAL separator forces a split.
Failure to find a separator does not justify a permanent merge unless the relevant continuation family is closed/exhausted.

## Dynamic consistency

Because continuations compose,

[
\Phi_G(h\circ a)(t)=\Phi_G(h)(a\circ t).
]

Therefore exact GOAL equivalence is automatically a right congruence:

[
h_1\sim_G h_2
\Rightarrow
h_1\circ a\sim_G h_2\circ a.
]

No separate congruence axiom is required.

## The developmental invariant

The kernel is not trying to discover the environment.

It is trying to discover the least self and least interrogation sufficient to produce the required consequence.

[
\boxed{\text{query continuation}\to\text{record consequence}\to\text{compress}\to\text{repeat}}
]

or more exactly:

[
\boxed{
\text{Maintain the smallest warranted partial GOAL pairing until one verified cell is 1.}
}
]

## ARC Level-4 checkpoint

Two independently replayable Level-4 histories, of lengths 4 and 85 after the protected prefix, were environmentally distinct immediately and under every tested continuation through depth 4.

The complete bounded test family contained

[
1+4+16+64+256=341
]

continuations.

Observed:

- 341/341 tested continuations: environmental frames differed,
- 0/341: GOAL consequence differed.

Therefore, through depth 4,

[
\boxed{h_A\equiv_G h_B}
]

while

[
\boxed{h_A\not\equiv_{\mathrm{environment}}h_B}.
]

This is direct evidence that reconstructing environmental state can be strictly finer than the state required by the task.

The earlier #11/#8 distinctions were real environmental variables, but this experiment does not warrant promoting them into GOAL-task identity.

## One-line constitution

[
\boxed{
\textbf{Ask only what can change winning; remember only what winning can distinguish; stop when consequence says GOAL.}
}
]
