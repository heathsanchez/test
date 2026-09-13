#!/usr/bin/env python3
"""Post-freeze exact vibration worlds for V11.

This file is deliberately challenge-side.  It may use hidden graph coordinates
and the exact update law to generate observations; none of that information is
passed to the frozen kernel.
"""
from __future__ import annotations

from basis import FrameTrace


MODULUS = 5
COUPLING = 1
FRAME_COUNT = 50
BASELINE = 0


def grid_3x3():
    n = 9
    adj = [set() for _ in range(n)]
    for r in range(3):
        for c in range(3):
            i = 3 * r + c
            for dr, dc in ((1,0),(-1,0),(0,1),(0,-1)):
                rr, cc = r + dr, c + dc
                if 0 <= rr < 3 and 0 <= cc < 3:
                    adj[i].add(3 * rr + cc)
    return tuple(frozenset(x) for x in adj)


def path_9():
    adj = [set() for _ in range(9)]
    for i in range(8):
        adj[i].add(i + 1)
        adj[i + 1].add(i)
    return tuple(frozenset(x) for x in adj)


def wave_matrix_rows(adj, modulus=MODULUS, coupling=COUPLING):
    """Binary support of M = 2I - coupling*L modulo p."""
    n = len(adj)
    rows = []
    for i in range(n):
        support = set()
        for j in range(n):
            coeff = 0
            if i == j:
                coeff += 2 - coupling * len(adj[i])
            if j in adj[i]:
                coeff += coupling
            if coeff % modulus != 0:
                support.add(j)
        rows.append(frozenset(support))
    return tuple(rows)


def interventions_from_rows(rows):
    n = len(rows)
    # source j influences target i iff M[i,j] is non-zero.
    by_source = {}
    for j in range(n):
        bits = []
        for i in range(n):
            bits.append(1 if j in rows[i] else 0)
        by_source[j] = tuple(bits)
    return by_source


def laplacian_apply(adj, u, modulus=MODULUS):
    return tuple(
        (
            len(adj[i]) * u[i]
            - sum(u[j] for j in adj[i])
        ) % modulus
        for i in range(len(adj))
    )


def step(adj, prev, cur, modulus=MODULUS, coupling=COUPLING):
    lu = laplacian_apply(adj, cur, modulus)
    nxt = tuple(
        (
            2 * cur[i]
            - prev[i]
            - coupling * lu[i]
        ) % modulus
        for i in range(len(cur))
    )
    return tuple(cur), nxt


def simulate(adj, initial, frame_count=FRAME_COUNT):
    prev = tuple(int(x) % MODULUS for x in initial)
    cur = prev
    frames = [cur]
    for _ in range(frame_count - 1):
        prev, cur = step(adj, prev, cur)
        frames.append(cur)
    return tuple(frames)


def permute_rows(rows, permutation):
    n = len(rows)
    p = tuple(int(x) for x in permutation)
    if sorted(p) != list(range(n)):
        raise ValueError("invalid permutation")
    out = [set() for _ in range(n)]
    for old_i, row in enumerate(rows):
        new_i = p[old_i]
        for old_j in row:
            out[new_i].add(p[old_j])
    return tuple(frozenset(x) for x in out)


def permute_frames(frames, permutation):
    n = len(permutation)
    p = tuple(int(x) for x in permutation)
    out = []
    for frame in frames:
        new = [0] * n
        for old_i, value in enumerate(frame):
            new[p[old_i]] = int(value)
        out.append(tuple(new))
    return tuple(out)


def make_world(name, adj, initial, permutation):
    support_rows = wave_matrix_rows(adj)
    frames = simulate(adj, initial)
    rows_p = permute_rows(support_rows, permutation)
    frames_p = permute_frames(frames, permutation)
    interventions = interventions_from_rows(rows_p)

    persistent_original = tuple(
        i
        for i in range(len(initial))
        if all(frame[i] == BASELINE for frame in frames[:24])
    )
    persistent_permuted = tuple(
        sorted(permutation[i] for i in persistent_original)
    )

    return {
        "name": name,
        "channel_count": len(adj),
        "interventions": interventions,
        "trace": FrameTrace(
            len(adj),
            frames_p,
            BASELINE,
        ),
        "hidden_persistent_channels": persistent_permuted,
    }


GRID = grid_3x3()
PATH = path_9()

VERTICAL_ANTI = (1,0,4, 1,0,4, 1,0,4)
CENTER_IMPULSE = (0,0,0, 0,1,0, 0,0,0)
PATH_ANTI = (1,1,1,1,0,4,4,4,4)

WORLD_A = make_world(
    "grid_vertical_a",
    GRID,
    VERTICAL_ANTI,
    (3,0,6,2,5,1,8,4,7),
)
WORLD_B = make_world(
    "grid_vertical_b",
    GRID,
    VERTICAL_ANTI,
    (8,2,5,0,7,4,1,6,3),
)
WORLD_C = make_world(
    "grid_vertical_c",
    GRID,
    VERTICAL_ANTI,
    (1,7,3,8,0,5,2,6,4),
)
WORLD_DIFFERENT = make_world(
    "grid_center_impulse",
    GRID,
    CENTER_IMPULSE,
    (6,1,8,3,0,7,5,2,4),
)
WORLD_PATH = make_world(
    "path_antisymmetric",
    PATH,
    PATH_ANTI,
    (4,8,1,6,0,7,3,5,2),
)

# Incomplete controls.
WORLD_SHORT = dict(WORLD_A)
WORLD_SHORT["name"] = "grid_vertical_short_trace"
WORLD_SHORT["trace"] = FrameTrace(
    WORLD_A["channel_count"],
    WORLD_A["trace"].frames[:10],
    BASELINE,
)

WORLD_MISSING_INTERVENTION = dict(WORLD_A)
WORLD_MISSING_INTERVENTION["name"] = "grid_vertical_missing_intervention"
WORLD_MISSING_INTERVENTION["interventions"] = dict(WORLD_A["interventions"])
WORLD_MISSING_INTERVENTION["interventions"].pop(5)
