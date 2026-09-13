#!/usr/bin/env python3
"""Post-freeze hidden worlds for V28 contextual multigrain tests."""
from __future__ import annotations

from basis import MultiContextWorld


# Four anonymous states secretly encode two orthogonal binary regularities.
# The learner never receives those latent coordinates.
MAIN = MultiContextWorld(
    state_count=4,
    context_names=("ctx_alpha","ctx_beta"),
    future_signatures=(
        ((0,), (0,), (1,), (1,)),
        ((0,), (1,), (0,), (1,)),
    ),
    record_signatures=None,
    complete=True,
    world_id="main_incompatible",
)

DUPLICATE = MultiContextWorld(
    state_count=4,
    context_names=("ctx_alpha","ctx_alpha_copy"),
    future_signatures=(
        ((0,), (0,), (1,), (1,)),
        ((0,), (0,), (1,), (1,)),
    ),
    record_signatures=None,
    complete=True,
    world_id="duplicate_relevance",
)

PERTURBED = MultiContextWorld(
    state_count=4,
    context_names=("ctx_alpha","ctx_beta"),
    future_signatures=(
        ((0,), (1,), (2,), (2,)),
        ((0,), (1,), (0,), (1,)),
    ),
    record_signatures=None,
    complete=True,
    world_id="one_context_refined",
)

BRANCH = MultiContextWorld(
    state_count=4,
    context_names=("branch_left","branch_right"),
    future_signatures=MAIN.future_signatures,
    record_signatures=None,
    complete=True,
    world_id="branch_labels",
)

RELEVANCE = MultiContextWorld(
    state_count=4,
    context_names=("future_task_a","future_task_b"),
    future_signatures=MAIN.future_signatures,
    record_signatures=None,
    complete=True,
    world_id="relevance_labels",
)

# Prediction quotient: 2 blocks.
# Record quotient: 4 blocks, leaving a nontrivial interval of lawful refinements.
RECORD_INTERVAL = MultiContextWorld(
    state_count=6,
    context_names=("recorded_future",),
    future_signatures=(
        ((0,), (0,), (0,), (1,), (1,), (1,)),
    ),
    record_signatures=(
        ((0,), (0,), (1,), (2,), (2,), (3,)),
    ),
    complete=True,
    world_id="recordability_interval",
)


def relabel(world: MultiContextWorld, perm: tuple[int, ...], world_id: str) -> MultiContextWorld:
    inv = [0] * len(perm)
    for old, new in enumerate(perm):
        inv[new] = old

    futures = tuple(
        tuple(ctx[inv[new]] for new in range(world.state_count))
        for ctx in world.future_signatures
    )
    records = None
    if world.record_signatures is not None:
        records = tuple(
            tuple(ctx[inv[new]] for new in range(world.state_count))
            for ctx in world.record_signatures
        )

    return MultiContextWorld(
        state_count=world.state_count,
        context_names=world.context_names,
        future_signatures=futures,
        record_signatures=records,
        complete=world.complete,
        world_id=world_id,
    )


RELABELED = relabel(MAIN, (2,0,3,1), "main_relabelled")

INCOMPLETE = MultiContextWorld(
    state_count=4,
    context_names=MAIN.context_names,
    future_signatures=MAIN.future_signatures,
    record_signatures=None,
    complete=False,
    world_id="incomplete",
)
