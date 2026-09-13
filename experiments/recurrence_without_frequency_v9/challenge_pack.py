#!/usr/bin/env python3
"""Post-freeze temporal challenge pack for V9."""
from __future__ import annotations

from basis import (
    BIT,
    finite_carrier,
    relation_from_outputs,
    permute_relation,
    permute_observer,
)


C6A = finite_carrier("six_a", 6)
T6A = relation_from_outputs(
    C6A,
    C6A,
    (1, 2, 0, 4, 5, 3),
    provenance=("challenge_transition",),
)
O6A = relation_from_outputs(
    C6A,
    BIT,
    (0, 0, 1, 0, 0, 1),
    provenance=("challenge_observer",),
)

C6B = finite_carrier("six_b", 6)
P6B = (2, 0, 1, 5, 3, 4)
T6B = permute_relation(T6A, P6B, C6B)
O6B = permute_observer(O6A, P6B, C6B)

C6C = finite_carrier("six_c", 6)
P6C = (4, 2, 5, 1, 3, 0)
T6C = permute_relation(T6A, P6C, C6C)
O6C = permute_observer(O6A, P6C, C6C)

# Same carrier/observer arities, different temporal organization.
C6D = finite_carrier("six_d", 6)
T6D = relation_from_outputs(
    C6D,
    C6D,
    (1, 0, 3, 2, 5, 4),
    provenance=("challenge_transition_different",),
)
O6D = relation_from_outputs(
    C6D,
    BIT,
    (0, 1, 0, 1, 0, 1),
    provenance=("challenge_observer_different",),
)

C8 = finite_carrier("eight", 8)
T8 = relation_from_outputs(
    C8,
    C8,
    (1, 2, 3, 0, 5, 6, 7, 4),
    provenance=("challenge_transition",),
)
O8 = relation_from_outputs(
    C8,
    BIT,
    (0, 0, 0, 1, 0, 0, 0, 1),
    provenance=("challenge_observer",),
)

C4T = finite_carrier("transient4", 4)
T4T = relation_from_outputs(
    C4T,
    C4T,
    (1, 2, 3, 3),
    provenance=("challenge_transient",),
)
O4T = relation_from_outputs(
    C4T,
    BIT,
    (0, 0, 1, 1),
    provenance=("challenge_observer",),
)

EXPECTED_3_CLASSES = ((0, 3), (1, 4), (2, 5))
EXPECTED_4_CLASSES = ((0, 4), (1, 5), (2, 6), (3, 7))
