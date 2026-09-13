# Event-Frame Genesis V35 — Frozen Protocol

## Question

Can the event segmentation and frame assumptions still present in V34 be weakened?

V35 gives the kernel only a raw finite binary cycle. The scientific core does not treat the serialization start point or traversal direction as automatically meaningful.

Four generic frame classes are available:

- UNFRAMED: quotient by rotations and reversal;
- ORIENTED: quotient by rotations only;
- ANCHORED: preserve the serialized cut but quotient the two traversal directions around that cut;
- FRAMED: preserve both cut and direction.

These are not domain concepts. They are the finite symmetry lattice of a serialized cycle.

The hidden challenge pack is committed only after this kernel is frozen.

## Event-window construction

For each lawful frame class, the kernel forms the canonical representative of the cycle under that class.

It then searches the smallest contiguous prefix window k whose induced partition is exactly the authoritative consequence partition.

The accepted structure therefore has two components:

1. how much boundary symmetry had to be broken;
2. how much contiguous boundary span had to remain distinguishable.

The developmental metric is lexicographic:

    (number of symmetry breaks, event-window length)

with all exact ties preserved.

A frame class that violates verified consequence is rejected by an explicit finite symmetry-obstruction witness.

A representation whose event window merely refines the consequence partition is rejected; the window quotient must equal the authoritative consequence quotient exactly.

## What is and is not supplied

Supplied:

- binary boundary symbols;
- circular adjacency;
- finite complete authority in the primary tests;
- the generic cycle-symmetry lattice;
- the structural ordering above;
- external verified consequence.

Not supplied:

- a semantic event start;
- a semantic direction;
- named channels or variables;
- a history register;
- a joint-system register;
- relation, pair, tuple, switch, or Boolean constructors;
- the hidden challenge's required frame class or event span.

The raw cycle is stored as a tuple in software, but its serialization cut and direction are treated only as candidate symmetry-breaking structure. They are not presumed meaningful unless the verifier forces retention of them.

## Frozen post-challenge gates

E1. Frozen core remains byte-identical after the challenge pack is committed.
E2. One frozen kernel exactly classifies all post-freeze worlds.
E3. A constant consequence retains no frame and a zero-length event.
E4. A dihedral-invariant one-symbol event is recovered with no frame break.
E5. A larger dihedral-invariant event requires a larger verified window but still no frame break.
E6. A rotation-invariant but reversal-sensitive consequence rejects UNFRAMED and earns ORIENTED structure.
E7. A cut-sensitive but direction-insensitive consequence rejects UNFRAMED/ORIENTED and earns ANCHORED structure.
E8. A cut- and direction-sensitive consequence earns FRAMED structure.
E9. Increasing the hidden event span increases the selected event-window length without changing the required frame class.
E10. Reversal-sensitive obstruction is witnessed by two cycles in one dihedral orbit with different consequences.
E11. Cut-sensitive obstruction is witnessed by two cycles in one rotation orbit with different consequences.
E12. Consequence-label relabelling preserves selected frame class and event span.
E13. Incomplete encounter authority remains UNKNOWN_AUTHORITY.
E14. Verifier ablation authorizes no frame or event construction.
E15. Named challenge axes, channels, history, joint objects, READ/ATOM/PAIR/TUPLE/SWITCH/APPLY are absent from the frozen executable kernel.
E16. The only developmental dimensions supplied by the scientific kernel are boundary symmetry class and contiguous event-window length.

## Claim boundary

A pass does not establish event genesis from structureless reality.

V35 still supplies binary symbols and circular adjacency. It also supplies the generic symmetry lattice through which boundary structure may be retained.

What it can establish is narrower:

> a semantic start point, semantic traversal direction, and retained event span need not be supplied as facts. They can be treated as initially removable symmetries and retained only when verified consequence proves the corresponding quotient inadequate.

If V35 passes, the remaining handhold is circular adjacency/symbolization itself: the boundary is still already decomposed into elementary binary differences arranged in a neighborhood structure.
