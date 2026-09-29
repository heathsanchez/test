#!/usr/bin/env python3
"""Crystal V27: exact full-constructor audit of the first V26 zero-tail separator.

Parent authority:
  collatz-crystal-zero-tail-adversary-v26
  head 360bfe765b3a8aeba625647d8b857e6422908e81
  run 36526634202

V26 rejected the depth-9 93-zero D/S-only bound.  Its first exact separator is
the nonterminal parameter cell (d,r)=(17,65874), reached by a forced bit 1,
whose D/S-only all-zero continuation first exits only after 132 extra bits.

V27 asks exactly one question before earning any new state coordinate:
does the already-qualified lower-source merge constructor M close this same
zero-tail path within the old 93-bit window?

If yes, the D/S-only separator is presentation and the next adversary must use
full D/S/M semantics.  If no, the >93 separator survives the complete V25
constructor interface through 93 zero steps and earns a genuine refinement.

No wider source census is performed.
"""
from __future__ import annotations

import json
import collatz_crystal_parameter_quotient_v25 as v25

PARENT = "collatz-crystal-zero-tail-adversary-v26@360bfe765b3a8aeba625647d8b857e6422908e81"
PARENT_RUN = 36526634202

D0 = 17
R0 = 65_874
OLD_BOUND = 93
EXPECTED_DS_WAIT = 132

PARENT_D = 16
PARENT_R = 338


def interface(d: int, r: int):
    N = v25.N0 + v25.NC * r
    S = v25.NC * (1 << d)
    pref = v25.fixed_prefix(N, S)
    j, A, C, q = pref[-1]
    m = v25.is_pow3(C)
    assert j == 59 + d
    assert m is not None
    return {
        "d": d,
        "r": r,
        "N": N,
        "S": S,
        "depth": j,
        "A": A,
        "C": C,
        "q": q,
        "pow3_exponent": m,
        "A_parity": A & 1,
        "A_mod_8": A % 8,
        "A_mod_24": A % 24,
        "A_mod_81": A % 81,
        # C/S = 3^q / 2^(59+d), since NC=2^59*3^8 and C=3^(8+q).
        "rho_num": 3 ** q,
        "rho_den": 1 << (59 + d),
    }


def main():
    # Reproduce V26's exact first separator under D/S only.
    first_ds = None
    for e in range(EXPECTED_DS_WAIT + 1):
        z = v25.classify_cell(D0 + e, R0, with_merge=False)
        if z["terminal"]:
            first_ds = {"extra_zero_bits": e, "depth": D0 + e, "exit": z["exit"]}
            break
    assert first_ds is not None
    assert first_ds["extra_zero_bits"] == EXPECTED_DS_WAIT, first_ds

    # Reproduce that the separator itself survived full D/S/M at entry.
    root_full = v25.classify_cell(D0, R0, with_merge=True)
    assert not root_full["terminal"], root_full

    # Decisive audit: test full D/S/M semantics for every zero continuation
    # state through the old 93-bit window.  Stop on the first merge witness.
    first_full_exit = None
    audited = 0
    for e in range(OLD_BOUND + 1):
        d = D0 + e
        ds = v25.classify_cell(d, R0, with_merge=False)
        assert not ds["terminal"], (e, ds)  # V26 says first D/S exit is at 132.

        full = v25.classify_cell(d, R0, with_merge=True)
        audited += 1
        print(
            "V27_AUDIT",
            json.dumps({
                "e": e,
                "d": d,
                "terminal": full["terminal"],
                "kind": None if not full["terminal"] else full["exit"]["kind"],
                "reverseStates": full.get("reverseStates", 0),
            }, sort_keys=True),
            flush=True,
        )
        if full["terminal"]:
            first_full_exit = {
                "extra_zero_bits": e,
                "depth": d,
                "exit": full["exit"],
                "reverseStates": full.get("reverseStates", 0),
            }
            break

    p = interface(PARENT_D, PARENT_R)
    c0 = interface(D0, PARENT_R)
    c1 = interface(D0, R0)

    # The V26 separator is exactly the forced odd child of this parent:
    # bit 0 halves the coefficient ratio; bit 1 multiplies it by 3/2.
    assert p["A_parity"] == 0 and (p["C"] & 1) == 1
    assert c0["q"] == p["q"]
    assert c1["q"] == p["q"] + 1
    assert c0["rho_num"] * 2 * p["rho_den"] == p["rho_num"] * c0["rho_den"]
    assert c1["rho_num"] * 2 * p["rho_den"] == 3 * p["rho_num"] * c1["rho_den"]

    if first_full_exit is None:
        verdict = "FULL_DSM_93_BOUND_REJECTED_BY_V26_SEPARATOR"
        next_residual = (
            "The first V26 >93 witness survives every qualified D/S/M exit for "
            "93 zero-tail steps. Treat the forced 3/2 coefficient-ratio jump as "
            "the earned separator and test the minimum source-coherent/3-adic "
            "state needed to predict eventual zero-tail exit."
        )
    else:
        verdict = "V26_DS_SEPARATOR_CLOSED_BY_LOWER_MERGE_WITHIN_93"
        next_residual = (
            "D/S-only wait is presentation at this witness. Re-run the zero-tail "
            "adversary with the full D/S/M protected consequence before adding "
            "any new state coordinate."
        )

    result = {
        "schema": "COLLATZ_CRYSTAL_ZERO_TAIL_SEPARATOR_V27",
        "parent": {"authority": PARENT, "run": PARENT_RUN},
        "separator_cell": {"d": D0, "r": R0, "incoming_bit": 1},
        "ds_control": first_ds,
        "full_dsm_audit": {
            "old_bound": OLD_BOUND,
            "states_audited": audited,
            "first_full_exit": first_full_exit,
        },
        "forced_bit_transition": {
            "parent": p,
            "child_bit_0": c0,
            "child_bit_1": c1,
            "exact_rho_law": {
                "bit_0": "rho -> rho/2",
                "bit_1": "rho -> 3*rho/2",
            },
        },
        "scientific_verdict": verdict,
        "next_residual": next_residual,
        "universal_status": "UNKNOWN",
        "global_collatz": "UNKNOWN",
    }
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
