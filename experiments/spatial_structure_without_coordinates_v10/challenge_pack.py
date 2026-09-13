#!/usr/bin/env python3
"""Post-freeze hidden relational worlds for V10."""
from __future__ import annotations


def rows_from_edges(n, edges):
    rows = [set() for _ in range(n)]
    for a, b in edges:
        rows[a].add(b)
        rows[b].add(a)
    return tuple(frozenset(r) for r in rows)


def path_rows(n):
    return rows_from_edges(n, [(i, i + 1) for i in range(n - 1)])


def ring_rows(n):
    return rows_from_edges(
        n,
        [(i, (i + 1) % n) for i in range(n)],
    )


def disjoint_3_4_rows():
    return rows_from_edges(
        7,
        [(0, 1), (1, 2), (3, 4), (4, 5), (5, 6)],
    )


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
    return tuple(frozenset(r) for r in out)


def observations(rows):
    n = len(rows)
    return {
        i: tuple(1 if j in rows[i] else 0 for j in range(n))
        for i in range(n)
    }


PATH7_A_ROWS = permute_rows(
    path_rows(7),
    (3, 0, 6, 2, 5, 1, 4),
)
PATH7_B_ROWS = permute_rows(
    path_rows(7),
    (6, 2, 0, 5, 1, 4, 3),
)
PATH7_C_ROWS = permute_rows(
    path_rows(7),
    (1, 5, 3, 0, 6, 4, 2),
)

RING8_ROWS = permute_rows(
    ring_rows(8),
    (4, 0, 6, 2, 7, 1, 5, 3),
)

BLOCKS7_ROWS = permute_rows(
    disjoint_3_4_rows(),
    (5, 1, 6, 0, 4, 2, 3),
)

PATH7_A_OBS = observations(PATH7_A_ROWS)
PATH7_B_OBS = observations(PATH7_B_ROWS)
PATH7_C_OBS = observations(PATH7_C_ROWS)
RING8_OBS = observations(RING8_ROWS)
BLOCKS7_OBS = observations(BLOCKS7_ROWS)

PATH7_INCOMPLETE_OBS = dict(PATH7_A_OBS)
PATH7_INCOMPLETE_OBS.pop(4)
