#!/usr/bin/env python3
"""Post-freeze literal families for V15 parametric grammar genesis."""
from __future__ import annotations

from basis import VerifiedLiteral


def lit(tokens, name, verified=True):
    return VerifiedLiteral(
        tokens=tuple(tokens),
        provenance=(name,),
        verified=verified,
        interface="opaque_lower_token_sequence",
    )


A, B, C, D, E, F, G, H = (
    "tok_a1", "tok_b2", "tok_c3", "tok_d4",
    "tok_e5", "tok_f6", "tok_g7", "tok_h8",
)

ALL_EQUAL_1 = lit((A, A, A, A), "all_equal_world_1")
ALL_EQUAL_2 = lit((B, B, B, B), "all_equal_world_2")

DISTINCT_1 = lit((C, D, C, D), "split_world_1")
DISTINCT_2 = lit((E, F, E, F), "split_world_2")

HELDOUT = (G, H, G, H)
WRONG = (G, H, H, G)
WRONG_LITERAL = lit(WRONG, "wrong_structure_future")

# Opaque V14-style grammar tokens. V15 sees only token equality/type compatibility.
V14_RULE_X = "g_verified_lower_x"
V14_RULE_Y = "g_verified_lower_y"
V14_HELDOUT = (V14_RULE_X, V14_RULE_Y, V14_RULE_X, V14_RULE_Y)

HET_1 = lit((A, A, B), "heterogeneous_world_1")
HET_2 = lit((C, C, D), "heterogeneous_world_2")

SINGLE = lit((C, D, C, D), "single_schema_example")

BAD = VerifiedLiteral(
    tokens=(A, B, A, B),
    provenance=("bad_unverified_literal",),
    verified=False,
    interface="opaque_lower_token_sequence",
)
