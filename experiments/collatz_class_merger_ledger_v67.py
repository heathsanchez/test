#!/usr/bin/env python3
"""V67: normalize an existing q7 predecessor bank into V66 class-merger consequences.

Protected object (V66): future-coalescence class.
Protected progress: a future endpoint lies on the orbit of some positive source
strictly smaller than the original source.

This experiment does not search a new feature space.  It reuses the exact q7
reverse-predecessor bank, pulls every law through every exact affine prefix of
the frozen V61 residual, preserves the original source inequality, and emits
Lean consumers for each whole residual cell actually closed.

The residual after this reclosure is the input to the next iteration.
"""
from __future__ import annotations

import argparse
import collections
import hashlib
import json
from pathlib import Path

N0 = 38_911_100_780_481_085_467
NC = 3_782_158_995_862_761_504_768
SOURCE_SLOPE = NC * 2**18
STATE_SHA256 = "a4dcc7bd5d51e6eb5f375140fd29ed722c9337bb11fde9c14ce6e6e9d51353b6"

EXPECTED_Q7 = {
    (3, 2), (9, 4), (81, 10), (729, 433), (729, 604),
    (2187, 205), (2187, 325), (2187, 919), (2187, 991),
    (2187, 1000), (2187, 1090), (2187, 1171), (2187, 2170),
}

def shortcut(n: int) -> int:
    return (3 * n + 1) // 2 if n & 1 else n // 2

def orbit(n: int, k: int) -> tuple[int, int]:
    q = 0
    for _ in range(k):
        q += n & 1
        n = shortcut(n)
    return n, q

def reverse_apply(n: int, word: str) -> int | None:
    x = n
    for ch in word:
        if ch == "E":
            x *= 2
        else:
            z = 2 * x - 1
            if z % 3:
                return None
            x = z // 3
            if not (x & 1):
                return None
    return x

def q7_bank():
    """Reproduce the old exact first-contraction tree, then quotient it."""
    Q = 7
    D = 3**Q
    max_depth = D.bit_length() - 1
    raw = []

    def visit(word: str, a: int, c: int, d: int, odd: int) -> None:
        if len(word) >= max_depth:
            return
        for ch in ("E", "O"):
            if ch == "E":
                na, nc, nd, no = 2*a, 2*c, d, odd
            else:
                if odd >= Q:
                    continue
                na, nc, nd, no = 2*a, 2*c + d, 3*d, odd + 1
            nw = word + ch
            if no and na < nd:
                residue = (nc * pow(na, -1, nd)) % nd
                raw.append(dict(
                    word=nw, steps=len(nw), odd_inverse_steps=no,
                    a=na, c=nc, d=nd, residue=residue,
                ))
            else:
                visit(nw, na, nc, nd, no)

    visit("", 1, 0, 1, 0)

    killed = bytearray(D)
    selected = []
    for z in sorted(raw, key=lambda x: (
        x["odd_inverse_steps"], x["residue"], x["steps"], x["word"])):
        added = 0
        for residue in range(z["residue"], D, z["d"]):
            if not killed[residue]:
                killed[residue] = 1
                added += 1
        if added:
            z = dict(z)
            z["new_mod_3q_residues"] = added
            selected.append(z)

    assert len(selected) == 13
    assert sum(killed) == 1013
    assert {(z["d"], z["residue"]) for z in selected} == EXPECTED_Q7

    # Independent arithmetic replay on fresh members of every exact class.
    for z in selected:
        for mult in (5, 17):
            n = z["residue"] + mult*z["d"]
            p = reverse_apply(n, z["word"])
            assert p is not None
            assert p == (z["a"]*n-z["c"])//z["d"]
            assert 0 < p < n
            y, q = orbit(p, z["steps"])
            assert y == n and q == z["odd_inverse_steps"]
    return selected

def fixed_prefix(N: int, S: int):
    """Exact affine future until the free-parameter slope first becomes odd."""
    j = 0
    X, R, q = N, S, 0
    while True:
        yield j, X, R, q
        if R & 1:
            return
        if X & 1:
            X = (3*X + 1)//2
            R = 3*R//2
            q += 1
        else:
            X //= 2
            R //= 2
        j += 1

def choose_hit(rows):
    # Cheapest exact consumer: earliest actual prefix, then shortest reverse word.
    return min(rows, key=lambda z: (z["prefix_steps"], z["reverse_steps"], z["word"]))

def emit_lean(hits, path: Path):
    with path.open("w") as f:
        f.write("import Collatz.ClassMergerCylinder\n")
        f.write("set_option maxRecDepth 100000\n")
        f.write("set_option maxHeartbeats 0\n")
        f.write("namespace CollatzFinal.SourceProduct\n")
        for row in hits:
            r = row["residual"]
            N = row["source0"]
            S = row["source_slope"]
            j = row["prefix_steps"]
            X = row["endpoint0"]
            q = row["source_odd_count"]
            p = row["lower0"]
            b = row["reverse_steps"]
            oq = row["lower_odd_count"]
            su = row["source_unit"]
            lu = row["lower_unit"]
            f.write(
                f"theorem v67_q7_merge_{r} (u : Nat) : "
                f"EarlierSourceCollision ({N} + {S} * u) "
                f"(iter shortcut {j} ({N} + {S} * u)) := by\n"
            )
            f.write(
                "  have hx := earlier_source_collision_of_coalescent_cylinders "
                f"(n := {N}) (k := {j}) (x := {X}) (q := {q}) "
                f"(p := {p}) (b := {b}) (r := {oq}) "
                f"(sourceUnit := {su}) (lowerUnit := {lu}) "
                "(by decide) (by decide) (by decide) (by decide) "
                "(by decide) (by decide) u\n"
            )
            f.write(f"  have hS : 2 ^ {j} * {su} = {S} := by decide\n")
            f.write(
                f"  have heq : {N} + 2 ^ {j} * ({su} * u) = "
                f"{N} + {S} * u := by\n"
                "    rw [← Nat.mul_assoc, hS]\n"
            )
            f.write("  simpa only [heq] using hx\n")
            f.write(f"#print axioms v67_q7_merge_{r}\n")
        f.write("end CollatzFinal.SourceProduct\n")

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--state", required=True)
    ap.add_argument("--lean-out", default="GeneratedClassMergerV67.lean")
    args = ap.parse_args()

    state = json.loads(Path(args.state).read_text())
    claimed = state.pop("certificate_sha256")
    assert claimed == STATE_SHA256
    assert hashlib.sha256(json.dumps(state, sort_keys=True).encode()).hexdigest() == claimed
    live = state["joined_reclosure"]["residual_residues"]
    assert len(live) == 14934

    laws = q7_bank()
    counts = collections.Counter()
    word_hist = collections.Counter()
    by_cell = collections.defaultdict(list)
    near = collections.defaultdict(list)

    for residual in live:
        N = N0 + NC*residual
        for j, X, R, q in fixed_prefix(N, SOURCE_SLOPE):
            counts["prefixes"] += 1
            assert SOURCE_SLOPE % 2**j == 0
            source_unit = SOURCE_SLOPE // 2**j
            assert 3**q * source_unit == R

            for law in laws:
                d = law["d"]
                if R % d or X % d != law["residue"]:
                    continue
                counts["q7_congruence_matches"] += 1

                p0 = (law["a"]*X - law["c"])//d
                ps = law["a"]*R//d
                margin0 = N - p0
                margin_slope = SOURCE_SLOPE - ps

                if len(near[residual]) < 8:
                    near[residual].append(dict(
                        prefix_steps=j, word=law["word"],
                        margin0=str(margin0), margin_slope=str(margin_slope),
                        lower0=str(p0), lower_slope=str(ps),
                    ))

                # Protected progress is relative to the ORIGINAL source family.
                if not (0 < p0 < N and ps <= SOURCE_SLOPE):
                    counts["matches_failing_original_source_inequality"] += 1
                    continue

                assert reverse_apply(X, law["word"]) == p0
                yy, lower_q = orbit(p0, law["steps"])
                assert yy == X
                assert lower_q == law["odd_inverse_steps"]
                assert ps % 2**law["steps"] == 0
                lower_unit = ps // 2**law["steps"]
                assert 3**lower_q * lower_unit == R
                assert 2**law["steps"]*lower_unit <= 2**j*source_unit

                row = dict(
                    residual=residual,
                    source0=N,
                    source_slope=SOURCE_SLOPE,
                    prefix_steps=j,
                    endpoint0=X,
                    endpoint_slope=R,
                    source_odd_count=q,
                    source_unit=source_unit,
                    word=law["word"],
                    reverse_steps=law["steps"],
                    lower_odd_count=lower_q,
                    lower0=p0,
                    lower_slope=ps,
                    lower_unit=lower_unit,
                    q7_modulus=d,
                    q7_residue=law["residue"],
                )
                by_cell[residual].append(row)
                counts["valid_q7_merger_hits"] += 1
                word_hist[law["word"]] += 1

    chosen = [choose_hit(rows) for _, rows in sorted(by_cell.items())]
    closed = {z["residual"] for z in chosen}
    remaining = [r for r in live if r not in closed]

    assert counts["prefixes"] == 1_164_852
    assert counts["valid_q7_merger_hits"] == 130
    assert len(chosen) == 121
    assert len(remaining) == 14_813
    assert remaining[0] == 30

    # Exact first separator: q7 applies congruentially many times, but every
    # resulting predecessor fails to be strictly below the protected source.
    first = remaining[0]
    Nfirst = N0 + NC*first
    first_rows = []
    for j, X, R, q in fixed_prefix(Nfirst, SOURCE_SLOPE):
        for law in laws:
            if R % law["d"] or X % law["d"] != law["residue"]:
                continue
            p0 = (law["a"]*X-law["c"])//law["d"]
            ps = law["a"]*R//law["d"]
            first_rows.append(dict(
                prefix_steps=j, word=law["word"],
                source_minus_lower0=Nfirst-p0,
                source_slope_minus_lower_slope=SOURCE_SLOPE-ps,
                lower0=str(p0), lower_slope=str(ps),
            ))
    assert len(first_rows) == 74
    assert max(z["source_minus_lower0"] for z in first_rows) == 0
    assert max(z["source_slope_minus_lower_slope"] for z in first_rows) == 0
    best = sorted(
        first_rows,
        key=lambda z:(-z["source_minus_lower0"], -z["source_slope_minus_lower_slope"],
                      z["prefix_steps"], len(z["word"]), z["word"])
    )[0]
    assert best["source_minus_lower0"] == 0
    assert best["source_slope_minus_lower_slope"] == 0

    emit_lean(chosen, Path(args.lean_out))

    result = {
        "schema": "COLLATZ_CLASS_MERGER_LEDGER_V67",
        "parent_v66": "collatz-future-coalescence-quotient-v66@1d23ed2a87465fd968db7b333103b6f558d0a433",
        "source_state_sha256": claimed,
        "protected_consequence": "exists 0<p<original_source and a,b with T^a(original_source)=T^b(p)",
        "compiled_capability": "q7 exact reverse-predecessor class-merger bank",
        "q7_nonredundant_laws": len(laws),
        "q7_killed_residues_mod_2187": 1013,
        "input_cells": len(live),
        "counts": dict(counts),
        "whole_cells_closed": len(chosen),
        "remaining_cells": len(remaining),
        "word_histogram": dict(sorted(word_hist.items())),
        "closed_residues": sorted(closed),
        "remaining_residues": remaining,
        "first_residual_separator": {
            "residual": first,
            "q7_congruence_matches": len(first_rows),
            "best_candidate": best,
            "constraint": (
                "q7 congruence is available, but no q7 reverse predecessor is "
                "strictly below the original source family; the best candidates "
                "are exact identity-margin ties."
            ),
        },
        "status": "CANDIDATE_PENDING_KERNEL_CONSUMERS",
        "next_least_change": (
            "Do not add a state coordinate. On the residual, extend reverse-word "
            "certificate generation against the protected original-source bound, "
            "starting from the exact identity-margin tie at residual 30."
        ),
        "qed": False,
        "global_collatz": "UNKNOWN",
        "scope": (
            "Exact pullback of the 13 q7 first-contraction laws through all maximal "
            "fixed affine prefixes of the frozen V61 14,934-cell residual. Whole-cell "
            "promotion requires the generated Lean consumers to kernel-check."
        ),
    }
    result["certificate_sha256"] = hashlib.sha256(
        json.dumps(result, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    print(json.dumps(result, indent=2, sort_keys=True))

if __name__ == "__main__":
    main()
