#!/usr/bin/env python3
"""V68: residual-first refinement of V67's first uncovered coalescence cell.

Parent V67 closes 121 whole cells with q7 class-merger certificates and leaves
r=30 first.  V68 applies the development law literally:

1. Exhaust the currently licensed UNSPLIT uniform-affine reverse-word grammar
   at every exact fixed prefix of r=30.
2. If that grammar cannot beat the identity source, do not add a new state
   coordinate arbitrarily.
3. Refine only the source parameter until an already-warranted protected
   consequence first distinguishes children.

The negative reverse search is finite and exact.  The positive depth-22 child
is separately kernel checked by formal/Collatz/R30FirstSplit.lean.
"""
from __future__ import annotations

import argparse
import collections
import hashlib
import json
from pathlib import Path

N0 = 38_911_100_780_481_085_467
NC = 3_782_158_995_862_761_504_768
R30 = 30
DEPTH0 = 18
V67_RESULT_SHA = "5aeae16666a406e0e9ba9330224d6bcd1ee632194a45f0b3b9f6b10587f999cb"
V67_QUAL_SHA = "1b4a484af5d2858907b8c572054494f2344bd5d530d35ea4751cc8ed06ed17b6"

def shortcut(n: int) -> int:
    return (3*n + 1)//2 if n & 1 else n//2

def source_orbit(n: int, k: int) -> tuple[int, int]:
    q = 0
    for _ in range(k):
        q += n & 1
        n = shortcut(n)
    return n, q

def verify_json_certificate(path: Path, expected: str):
    d = json.loads(path.read_text())
    claimed = d.pop("certificate_sha256")
    assert claimed == expected
    got = hashlib.sha256(
        json.dumps(d, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    assert got == claimed
    d["certificate_sha256"] = claimed
    return d

def v3(x: int) -> int:
    q = 0
    while x and x % 3 == 0:
        q += 1
        x //= 3
    return q

def fixed_prefix(N: int, S: int):
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

def reverse_audit(N: int, S: int, X: int, R: int):
    """Exhaust every uniform reverse word capable of ending with slope <= S.

    State after o O-steps and E total E has affine slope
      R * 2^(E+o) / 3^o.
    O consumes one factor of 3 and E cannot restore it, so o<=v3(R).
    The final slope<=S condition globally bounds E.  Identical constants at
    fixed (o,E) are identical affine states and may be quotient-merged.
    """
    max_o = v3(R)
    global_e = -1
    for o in range(max_o + 1):
        for e in range(300):
            if R * 2**(e + o) <= S * 3**o:
                global_e = max(global_e, e)
            else:
                break
    assert global_e >= 0

    dp = {0: {X: ""}}
    states = 1
    max_states = 1
    candidates = []

    for o in range(max_o):
        nxt = collections.defaultdict(dict)
        o2 = o + 1
        for E, cmap in dp.items():
            for c, word in cmap.items():
                residue = c % 3
                if residue == 0:
                    continue
                parity = 0 if residue == 2 else 1
                for e in range(parity, global_e - E + 1, 2):
                    E2 = E + e
                    ce = c << e
                    coeff_before = R * 2**(E2 + o) // 3**o
                    if ce % 3 != 2 or coeff_before % 3:
                        continue

                    nc = (2*ce - 1)//3
                    na = (2*coeff_before)//3
                    nw = word + "E"*e + "O"
                    states += 1

                    if na <= S:
                        candidates.append(dict(
                            word=nw,
                            reverse_steps=len(nw),
                            odd_inverse_steps=o2,
                            even_lifts=E2,
                            constant=nc,
                            slope=na,
                            constant_margin=N-nc,
                            slope_margin=S-na,
                        ))

                    # If even all remaining O steps with no extra E cannot
                    # restore slope <= S, no descendant can be a candidate.
                    remaining = max_o - o2
                    if na * 2**remaining > S * 3**remaining:
                        continue
                    if nc not in nxt[E2]:
                        nxt[E2][nc] = nw

        dp = dict(nxt)
        max_states = max(max_states, sum(len(v) for v in dp.values()))
        if not dp:
            break

    return candidates, states, max_states


def q7_bank():
    """Reproduce the 13 exact q7 first-contraction merger laws from V67."""
    Q = 7
    D = 3**Q
    max_depth = D.bit_length() - 1
    raw = []
    def visit(word, a, cc, d, odd):
        if len(word) >= max_depth:
            return
        for ch in ("E", "O"):
            if ch == "E":
                na, nc, nd, no = 2*a, 2*cc, d, odd
            else:
                if odd >= Q:
                    continue
                na, nc, nd, no = 2*a, 2*cc + d, 3*d, odd + 1
            nw = word + ch
            if no and na < nd:
                residue = (nc * pow(na, -1, nd)) % nd
                raw.append((nw, len(nw), no, na, nc, nd, residue))
            else:
                visit(nw, na, nc, nd, no)
    visit("", 1, 0, 1, 0)
    killed = bytearray(D)
    selected = []
    for z in sorted(raw, key=lambda x: (x[2], x[6], x[1], x[0])):
        added = 0
        for rr in range(z[6], D, z[5]):
            if not killed[rr]:
                killed[rr] = 1
                added += 1
        if added:
            selected.append(z)
    assert len(selected) == 13 and sum(killed) == 1013
    return selected

Q7_LAWS = q7_bank()

def q7_mergers(r: int, h: int):
    """Replay the full current q7 capability on one refined source cell."""
    N = N0 + NC*r
    S = NC * 2**h
    hits = []
    for j, X, R, q in fixed_prefix(N, S):
        for word, b, oq, a, cc, d, residue in Q7_LAWS:
            if R % d or X % d != residue:
                continue
            p0 = (a*X - cc)//d
            ps = a*R//d
            if 0 < p0 < N and ps <= S:
                hits.append(dict(
                    kind="Q7", r=r, h=h, prefix_steps=j, word=word,
                    lower0=p0, lower_slope=ps, source_slope=S,
                ))
    return hits

def simple_certificate(r: int, h: int):
    """Reuse exactly the D/M1/S constructor grammar of the certified cover."""
    n = N0 + NC*r
    y, q = n, 0
    P = NC * 2**h
    for k in range(59 + h + 1):
        assert P % 2**k == 0
        C = 3**q * (P // 2**k)
        if 0 < y < n and C <= P:
            return dict(kind="D", r=r, h=h, n=n, k=k, y=y, q=q, p=None,
                        source_slope=P)
        if y % 3 == 2 and C % 3 == 0:
            p = (2*y - 1)//3
            if 0 < p < n and 2*C//3 <= P:
                assert shortcut(p) == y
                return dict(kind="M1", r=r, h=h, n=n, k=k, y=y, q=q, p=p,
                            source_slope=P)
        if y % 8 == 5 and y <= 4*n and C % 8 == 0 and C//4 <= P:
            p = (y - 1)//4
            Y, Q = y, q
            for _ in range(3):
                Q += Y & 1
                Y = shortcut(Y)
            assert shortcut(p) == Y and 0 < p < n
            assert P % 2**(k+3) == 0
            return dict(kind="S", r=r, h=h, n=n, k=k+3, y=Y, q=Q, p=p,
                        source_slope=P)
        q += y & 1
        y = shortcut(y)
    return None

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--parent-dir", required=True)
    args = ap.parse_args()
    parent = Path(args.parent_dir)

    v67 = verify_json_certificate(parent/"result.json", V67_RESULT_SHA)
    qual = verify_json_certificate(parent/"qualification.json", V67_QUAL_SHA)
    assert qual["status"] == "WARRANTED_BOUNDED"
    assert qual["kernel_checked_whole_cell_mergers"] == 121
    assert v67["remaining_cells"] == 14813
    assert v67["remaining_residues"][0] == R30
    assert v67["first_residual_separator"]["residual"] == R30

    # Phase A: exact unsplit reverse-grammar exhaustion on r=30.
    N = N0 + NC*R30
    S = NC * 2**DEPTH0
    total_states = 0
    max_states = 0
    all_candidates = []
    prefix_rows = []

    prefixes = list(fixed_prefix(N, S))
    assert len(prefixes) == 78
    for j, X, R, q in prefixes:
        candidates, states, peak = reverse_audit(N, S, X, R)
        total_states += states
        max_states = max(max_states, peak)
        for z in candidates:
            z = dict(z)
            z.update(prefix_steps=j, source_odd_count=q)
            all_candidates.append(z)
        prefix_rows.append(dict(
            prefix_steps=j,
            source_odd_count=q,
            endpoint0=str(X),
            endpoint_slope=str(R),
            reverse_states=states,
            peak_quotient_states=peak,
            nonexpanding_candidates=len(candidates),
        ))

    identity = [
        z for z in all_candidates
        if z["constant"] == N and z["slope"] == S
        and z["constant_margin"] == 0 and z["slope_margin"] == 0
    ]
    strict = [
        z for z in all_candidates
        if z["constant_margin"] > 0 and z["slope_margin"] >= 0
    ]

    assert total_states == 8_325_986
    assert max_states == 85_892
    assert len(all_candidates) == 77
    assert len(identity) == 77
    assert strict == []

    # Phase B: refine only until an existing protected merger first separates
    # descendants of r=30.
    live = [R30]
    refinement = []
    first_closed = None
    for h in range(DEPTH0, 23):
        closed, residual = [], []
        kinds = collections.Counter()
        q7_closed = 0
        overlap = 0
        for r in live:
            c = simple_certificate(r, h)
            qhits = q7_mergers(r, h)
            if c is None and not qhits:
                residual.append(r)
            else:
                if c is not None:
                    row = dict(c)
                    kinds[c["kind"]] += 1
                else:
                    row = dict(qhits[0])
                    kinds["Q7"] += 1
                row["q7_hits"] = len(qhits)
                if qhits:
                    q7_closed += 1
                if c is not None and qhits:
                    overlap += 1
                closed.append(row)
        refinement.append(dict(
            depth=h,
            input_cells=len(live),
            closed=len(closed),
            closed_kinds=dict(sorted(kinds.items())),
            q7_closed=q7_closed,
            compiled_overlap=overlap,
            residual=len(residual),
            closed_residues=[c["r"] for c in closed],
        ))
        if closed and first_closed is None:
            first_closed = closed
            first_depth = h
            break
        live = [x for r in residual for x in (r, r + 2**h)]

    assert [z["closed"] for z in refinement[:4]] == [0, 0, 0, 0]
    assert [z["q7_closed"] for z in refinement[:4]] == [0, 0, 0, 0]
    assert first_depth == 22
    assert len(first_closed) == 1
    assert refinement[-1]["q7_closed"] == 1
    assert refinement[-1]["compiled_overlap"] == 1
    c = first_closed[0]
    assert c["r"] == 3_670_046
    assert c["kind"] == "D"
    assert c["k"] == 81
    assert c["q"] == 51
    assert c["n"] == 13_880_697_533_041_245_190_008_864_795
    assert c["y"] == 12_364_188_933_328_561_335_056_835_446
    assert c["source_slope"] == 15_863_524_604_983_164_030_494_441_472
    assert c["source_slope"] // 2**81 == 6561

    result = {
        "schema": "COLLATZ_R30_SEPARATOR_V68",
        "parent_v67_run": 36843884976,
        "parent_v67_head": "20e4047ea14787bdf98919d49c8f8035866b6c64",
        "parent_v67_qualification_sha256": V67_QUAL_SHA,
        "residual_cell": dict(r=R30, depth=DEPTH0, source0=str(N),
                              source_slope=str(S)),
        "unsplit_uniform_reverse_exhaustion": {
            "fixed_prefixes": len(prefixes),
            "exact_reverse_states": total_states,
            "max_quotient_states": max_states,
            "nonexpanding_candidates": len(all_candidates),
            "identity_candidates": len(identity),
            "strict_lower_source_candidates": len(strict),
            "verdict": "REJECT_UNSPLIT_UNIFORM_AFFINE_REVERSE_GRAMMAR",
        },
        "minimal_reused_constructor_split": {
            "refinement": refinement,
            "first_consequential_depth": first_depth,
            "extra_parameter_bits": first_depth - DEPTH0,
            "child": c,
            "next_four_bit_value": (c["r"] - R30)//2**DEPTH0,
            "interpretation": (
                "After reclosure under the full currently compiled D/M1/S + q7 "
                "capability set, depths 19..21 separate no protected "
                "consequence; depth 22 first does. The one depth-22 child "
                "is witnessed by both direct descent and q7."
            ),
        },
        "status": "CANDIDATE_NEGATIVE_EXHAUSTION_PLUS_POSITIVE_SPLIT_PENDING_KERNEL",
        "next_residual": (
            "Compile the depth-22 merger, remove that child, then reclose the "
            "15 sibling subcells before inventing any new representation. "
            "If a surviving sibling again has only identity reverse candidates, "
            "repeat residual-first refinement rather than global deepening."
        ),
        "qed": False,
        "global_collatz": "UNKNOWN",
        "scope": (
            "One V67 residual cell r=30. Reverse exhaustion covers every uniform "
            "affine reverse word from each of its 78 fixed prefixes that can have "
            "source slope no larger than the original r=30 cylinder. The split "
            "minimality claim is relative to the currently compiled D/M1/S + q7 capability set."
        ),
    }
    result["certificate_sha256"] = hashlib.sha256(
        json.dumps(result, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    print(json.dumps(result, indent=2, sort_keys=True))

if __name__ == "__main__":
    main()
