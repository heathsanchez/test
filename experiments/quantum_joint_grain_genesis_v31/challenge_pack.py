#!/usr/bin/env python3
"""Post-freeze hidden experiments for V31."""
from __future__ import annotations

from basis import (
    BipartiteExperiment,
    ONE,
    SQRT2_OVER_2,
    X2,
    Z2,
    born_table,
    m2_add,
    m2_scale,
)

# Generic local observable family supplied only in the hidden experiment.
A0 = Z2
A1 = X2
B0 = m2_scale(SQRT2_OVER_2, m2_add(Z2, X2))
B1 = m2_scale(SQRT2_OVER_2, m2_add(Z2, m2_scale(-ONE, X2)))

A_OBS = (A0, A1)
B_OBS = (B0, B1)

# Hidden state is selected only after the scientific core is frozen.
HIDDEN_JOINT = (1, 0, 0, 1)
HIDDEN_PRODUCT = (1, 0, 0, 0)

JOINT = BipartiteExperiment(
    a_observables=A_OBS,
    b_observables=B_OBS,
    probabilities=born_table(HIDDEN_JOINT, A_OBS, B_OBS),
    complete=True,
    world_id="hidden_joint",
)

PRODUCT = BipartiteExperiment(
    a_observables=A_OBS,
    b_observables=B_OBS,
    probabilities=born_table(HIDDEN_PRODUCT, A_OBS, B_OBS),
    complete=True,
    world_id="hidden_product",
)

# Pure setting/outcome relabelling control:
# swap settings on each side and flip one outcome convention on each side.
RA = (
    m2_scale(-ONE, A1),
    A0,
)
RB = (
    B1,
    m2_scale(-ONE, B0),
)

RELABELED = BipartiteExperiment(
    a_observables=RA,
    b_observables=RB,
    probabilities=born_table(HIDDEN_JOINT, RA, RB),
    complete=True,
    world_id="joint_relabelled",
)

INCOMPLETE = BipartiteExperiment(
    a_observables=A_OBS,
    b_observables=B_OBS,
    probabilities=JOINT.probabilities,
    complete=False,
    world_id="incomplete",
)
