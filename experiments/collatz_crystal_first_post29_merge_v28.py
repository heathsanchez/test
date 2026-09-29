#!/usr/bin/env python3
"""Crystal V28: first lawful post-depth-29 lower-source transition.

Parent:
  collatz-crystal-110-chamber-v27@848a4305679f0d839e22a1ed4480e28d80fc31b1

V27 replayed the old 12/19 reverse chamber on the exact V26 natural
adversary and found no chamber predecessor below the original source before
the orbit's quarter-splice at ordinary depth 525.

This audit asks the cheaper consequential question directly: when does the
already-Lean-qualified one-step inverse-odd constructor first fire?

For an orbit value y == 2 (mod 3), p=(2*y-1)/3 is a positive odd shortcut
predecessor with shortcut(p)=y.  If p<n, this is an OrdinaryExit for the
original source n.

Everything is exact integer arithmetic on the single frozen V26 adversary.
This closes that adversary; it does not prove the universal V23 cell.
"""

import json

N0 = 38_911_100_780_481_085_467
NC = 3_782_158_995_862_761_504_768
A59 = 91_182_490_942_926_966_077
C59 = 3**46
T_V26 = 685408643048678703309842726690675779814441196540003599299583389096836936979689649632335566636234945811040497388265518

START = 59
LIMIT = 600

def shortcut(x: int) -> int:
    return (3*x + 1)//2 if x & 1 else x//2

def main():
    n = N0 + NC*T_V26
    y = A59 + C59*T_V26

    first_inverse = None
    first_direct = None
    first_splice = None
    mod3_two_before = 0
    closest_predecessor = None

    for k in range(START, LIMIT + 1):
        if y < n and first_direct is None:
            first_direct = {"ordinary_depth": k, "value": y}

        if y % 8 == 5 and y <= 4*n and first_splice is None:
            first_splice = {"ordinary_depth": k, "value": y}

        if y % 3 == 2:
            p = (2*y - 1)//3
            assert 3*p + 1 == 2*y
            assert p & 1
            assert shortcut(p) == y
            gap = p - n
            row = {
                "ordinary_depth": k,
                "endpoint": y,
                "predecessor": p,
                "source_gap": gap,
                "endpoint_mod_12": y % 12,
                "endpoint_mod_81": y % 81,
            }
            if closest_predecessor is None or gap < closest_predecessor["source_gap"]:
                closest_predecessor = row
            if p < n and first_inverse is None:
                first_inverse = row
                break
            mod3_two_before += 1

        y = shortcut(y)

    assert first_inverse is not None
    assert first_inverse["ordinary_depth"] == 518
    assert first_inverse["source_gap"] < 0

    # Independently continue the original orbit to reproduce V27's first D/S exit.
    y = A59 + C59*T_V26
    ds = None
    for k in range(START, LIMIT + 1):
        if y < n:
            ds = {"kind": "D", "ordinary_depth": k, "value": y}
            break
        if y % 8 == 5 and y <= 4*n:
            ds = {"kind": "S", "ordinary_depth": k, "value": y}
            break
        y = shortcut(y)

    assert ds is not None
    assert ds["kind"] == "S"
    assert ds["ordinary_depth"] == 525
    assert first_inverse["ordinary_depth"] < ds["ordinary_depth"]

    result = {
        "schema": "COLLATZ_CRYSTAL_FIRST_POST29_MERGE_V28",
        "parent": "collatz-crystal-110-chamber-v27@848a4305679f0d839e22a1ed4480e28d80fc31b1",
        "source": n,
        "v26_parameter": T_V26,
        "first_lower_source_inverse_odd": first_inverse,
        "mod3_two_states_checked_before_hit": mod3_two_before,
        "closest_inverse_odd_predecessor_through_hit": closest_predecessor,
        "first_existing_direct_or_splice": ds,
        "lean_reuse": {
            "module": "formal/Collatz/OrdinaryInverseOdd.lean",
            "theorem": "ordinary_exit_of_inverse_odd_predecessor_lt",
            "premises_checked": ["endpoint % 3 = 2", "(2*endpoint-1)/3 < source"],
        },
        "scientific_verdict": (
            "V26_ADVERSARY_CLOSED_BY_EXISTING_ONE_STEP_LOWER_SOURCE_MERGE: "
            "the first qualified inverse-odd lower-source constructor fires at "
            "ordinary depth 518, before the quarter-splice at depth 525."
        ),
        "universal_consequence": (
            "The 12/19 chamber is not required to close this adversary. The live "
            "V23-cell residual is now to prove that every indefinitely protected "
            "natural path must eventually enter the inverse-odd source-lowering "
            "window y % 3 = 2 and 2*y < 3*n+1, or another existing OrdinaryExit."
        ),
        "universal_status": "UNKNOWN",
        "global_collatz": "UNKNOWN",
    }
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()
