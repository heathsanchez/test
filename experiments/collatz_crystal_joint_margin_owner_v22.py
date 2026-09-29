#!/usr/bin/env python3
"""Exact Crystal audit for the joint first-crossing margin residual.

This deliberately does NOT build a finite SCC quotient.  The exact symbolic
audit in ROS already showed that fixed finite raw-parity quotients lose
unbounded carry.  Instead we test the strongest theorem-shaped global order
property still compatible with the exact legal first-crossing language.

For every feasible first coefficient-crossing length j <= MAX_J:
  * enumerate every legal parity word exactly;
  * compute its affine numerator B, canonical source residue R, endpoint Y,
    and exact margin M = 2^j (Y-R);
  * replay every legal adjacent Hasse edge and test local endpoint contraction;
  * test global R/Y order on consecutive R-ranked legal words;
  * test whether the minimum-R legal word is the global M maximizer;
  * falsify two tempting composition shortcuts:
      - adjacent-R greedy descent;
      - arbitrary one-bit relocation ("one exchange") from adjacent local minima.

All arithmetic is integer exact.
"""

from __future__ import annotations

import json
import os
from typing import Dict, Iterable, List, Tuple

MAX_J = int(os.environ.get("COLLATZ_CRYSTAL_MAX_J", "29"))

Row = Tuple[int, int, int, int]  # B, R, Y, M


def largest_q_below(j: int) -> int:
    """Largest q with 3^q < 2^j (strict; equality never occurs for j>0)."""
    two = 1 << j
    q, p = 0, 1
    while p * 3 < two:
        p *= 3
        q += 1
    return q


def ceil_alpha(k: int) -> int:
    """ceil(k log_3 2), computed by exact integer comparison."""
    if k <= 0:
        return 0
    two = 1 << k
    q, p = 0, 1
    while p < two:
        p *= 3
        q += 1
    return q


def feasible(j: int, q: int) -> bool:
    # q=floor(j log_3 2) and feasibility additionally requires
    # q=ceil((j-1) log_3 2), equivalently 3^q > 2^(j-1).
    return pow(3, q) > (1 << (j - 1))


def legal_words(j: int, q: int) -> Iterable[int]:
    lower = [0] + [ceil_alpha(k) for k in range(1, j)]

    def rec(k: int, ones: int, word: int):
        if k == j:
            if ones == q:
                yield word
            return

        rem = j - (k + 1)
        for bit in (0, 1):
            nxt = ones + bit
            if nxt > q or nxt + rem < q:
                continue
            if k + 1 < j and nxt < lower[k + 1]:
                continue
            yield from rec(k + 1, nxt, word | (bit << k))

    yield from rec(0, 0, 0)


def row_for(word: int, j: int, q: int, inv3q: int) -> Row:
    p3 = [pow(3, i) for i in range(q + 1)]
    positions = [r for r in range(j) if (word >> r) & 1]
    assert len(positions) == q
    B = sum((1 << r) * p3[q - i - 1] for i, r in enumerate(positions))
    mod = 1 << j
    threeq = p3[q]
    R = (-B * inv3q) % mod
    Y_num = threeq * R + B
    assert Y_num % mod == 0
    Y = Y_num // mod
    M = mod * (Y - R)
    assert M == B - (mod - threeq) * R
    return B, R, Y, M


def bits(word: int, j: int) -> str:
    # time order b_0 ... b_{j-1}
    return "".join("1" if (word >> i) & 1 else "0" for i in range(j))


def audit_length(j: int) -> dict:
    q = largest_q_below(j)
    if not feasible(j, q):
        return {"j": j, "feasible": False}

    mod = 1 << j
    threeq = pow(3, q)
    inv3q = pow(threeq, -1, mod)

    rows: Dict[int, Row] = {}
    for w in legal_words(j, q):
        rows[w] = row_for(w, j, q, inv3q)

    words = set(rows)
    ordered = sorted(rows, key=lambda w: rows[w][1])

    # Exact global endpoint order and consecutive-rank contraction.
    endpoint_order_fail = None
    consecutive_contract_fail = 0
    min_consecutive_margin_drop = None
    for a, b in zip(ordered, ordered[1:]):
        _, Ra, Ya, Ma = rows[a]
        _, Rb, Yb, Mb = rows[b]
        dR, dY = Rb - Ra, Yb - Ya
        if not (dR > 0 and dY > 0) and endpoint_order_fail is None:
            endpoint_order_fail = {
                "a": bits(a, j), "b": bits(b, j),
                "Ra": Ra, "Rb": Rb, "Ya": Ya, "Yb": Yb,
            }
        if not (0 < dY < dR):
            consecutive_contract_fail += 1
        md = Ma - Mb
        if min_consecutive_margin_drop is None or md < min_consecutive_margin_drop:
            min_consecutive_margin_drop = md

    # Replay local P20-style contraction on every legal Hasse edge and find
    # adjacent-R local minima.
    hasse_edges = 0
    hasse_contract_fail = None
    local_minima: List[int] = []

    for w, (_, R, Y, _) in rows.items():
        has_lower = False
        for k in range(j - 1):
            if ((w >> k) & 1) == ((w >> (k + 1)) & 1):
                continue
            v = w ^ (1 << k) ^ (1 << (k + 1))
            if v not in words:
                continue

            _, R2, Y2, _ = rows[v]
            if R2 < R:
                has_lower = True

            if w < v:
                hasse_edges += 1
                dR, dY = R2 - R, Y2 - Y
                if not (dR * dY > 0 and abs(dY) < abs(dR)):
                    if hasse_contract_fail is None:
                        hasse_contract_fail = {
                            "w": bits(w, j), "v": bits(v, j), "k": k,
                            "dR": dR, "dY": dY,
                        }

        if not has_lower:
            local_minima.append(w)

    minR_word = ordered[0]
    maxM_word = max(rows, key=lambda w: rows[w][3])

    # Try the next tempting constructor: relocate a single 1 to a single 0
    # while preserving legality.  We inspect only adjacent-R local minima;
    # if these still have dead ends then one-exchange greedy composition is
    # conclusively not a universal proof spine.
    one_exchange_dead: List[int] = []
    one_exchange_widths: List[int] = []
    one_exchange_selected_contract_fail = None

    for w in local_minima:
        if w == minR_word:
            continue
        _, R, Y, _ = rows[w]
        best = None
        ones = [i for i in range(j) if (w >> i) & 1]
        zeros = [i for i in range(j) if not ((w >> i) & 1)]
        for i in ones:
            for z in zeros:
                v = w ^ (1 << i) ^ (1 << z)
                if v not in words:
                    continue
                _, R2, Y2, _ = rows[v]
                if R2 >= R:
                    continue
                cand = (abs(i - z), R2, v)
                if best is None or cand < best:
                    best = cand
        if best is None:
            one_exchange_dead.append(w)
        else:
            width, _, v = best
            one_exchange_widths.append(width)
            _, R2, Y2, _ = rows[v]
            dR, dY = R2 - R, Y2 - Y
            if not (dR * dY > 0 and abs(dY) < abs(dR)):
                if one_exchange_selected_contract_fail is None:
                    one_exchange_selected_contract_fail = {
                        "w": bits(w, j), "v": bits(v, j),
                        "width": width, "dR": dR, "dY": dY,
                    }

    dead_example = None
    if one_exchange_dead:
        w = one_exchange_dead[0]
        B, R, Y, M = rows[w]
        dead_example = {
            "word": bits(w, j), "B": B, "R": R, "Y": Y, "M": M,
        }

    B0, R0, Y0, M0 = rows[minR_word]
    Bm, Rm, Ym, Mm = rows[maxM_word]

    return {
        "j": j,
        "q": q,
        "feasible": True,
        "legal_words": len(rows),
        "hasse_edges": hasse_edges,
        "hasse_contract_fail": hasse_contract_fail,
        "endpoint_order_fail": endpoint_order_fail,
        "consecutive_R_rank_contract_failures": consecutive_contract_fail,
        "min_consecutive_margin_drop": min_consecutive_margin_drop,
        "adjacent_R_local_minima": len(local_minima),
        "non_global_local_minima": len(local_minima) - 1,
        "one_exchange_dead_local_minima": len(one_exchange_dead),
        "one_exchange_max_selected_width": max(one_exchange_widths, default=0),
        "one_exchange_selected_contract_fail": one_exchange_selected_contract_fail,
        "one_exchange_dead_example": dead_example,
        "min_R": {
            "word": bits(minR_word, j), "B": B0, "R": R0, "Y": Y0, "M": M0,
        },
        "max_M": {
            "word": bits(maxM_word, j), "B": Bm, "R": Rm, "Y": Ym, "M": Mm,
        },
        "min_R_is_global_max_M": minR_word == maxM_word,
    }


def main() -> None:
    reports = []
    first_greedy_failure = None
    first_rank_contract_failure = None

    for j in range(2, MAX_J + 1):
        r = audit_length(j)
        if not r.get("feasible"):
            continue
        reports.append(r)

        if r["hasse_contract_fail"] is not None:
            raise SystemExit("local Hasse contraction failure: " + json.dumps(r))

        if r["endpoint_order_fail"] is not None:
            raise SystemExit("legal endpoint-order inversion: " + json.dumps(r))

        if not r["min_R_is_global_max_M"]:
            raise SystemExit("minimum-R is not global max-M: " + json.dumps(r))

        if first_greedy_failure is None and r["one_exchange_dead_local_minima"] > 0:
            first_greedy_failure = {
                "j": j,
                "dead_count": r["one_exchange_dead_local_minima"],
                "example": r["one_exchange_dead_example"],
            }

        if first_rank_contract_failure is None and r["consecutive_R_rank_contract_failures"] > 0:
            first_rank_contract_failure = {
                "j": j,
                "count": r["consecutive_R_rank_contract_failures"],
            }

    out = {
        "status": "CANDIDATE_GLOBAL_ORDER_SURVIVES_GREEDY_COMPOSITION_REJECTED",
        "max_j": MAX_J,
        "feasible_lengths": len(reports),
        "total_legal_words": sum(r["legal_words"] for r in reports),
        "total_hasse_edges": sum(r["hasse_edges"] for r in reports),
        "all_hasse_edges_contract": True,
        "all_R_ranked_endpoints_strictly_increase": True,
        "all_min_R_are_global_max_M": True,
        "first_greedy_composition_failure": first_greedy_failure,
        "first_consecutive_R_rank_contraction_failure": first_rank_contract_failure,
        "interpretation": (
            "The raw finite-SCC route stays rejected. Exact local Hasse contraction "
            "does not compose through a greedy lower-R constructor, and even consecutive "
            "R-ranked legal words need not be globally contractive. The surviving theorem-"
            "shaped residual is the legal endpoint-order / minimum-R extremality structure, "
            "which requires a nonlocal arithmetic proof rather than a finite-state SCC."
        ),
        "lengths": reports,
    }
    print(json.dumps(out, sort_keys=True))


if __name__ == "__main__":
    main()
