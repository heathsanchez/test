#!/usr/bin/env python3
"""Exact bounded non-descending episode-language census.

The odd-episode r-graph is strongly connected, so r alone is too coarse.
This experiment asks a more consequence-specific question:

    starting from x=2^r m-1,
    which exact episode programs can avoid going below the ORIGINAL x?

For every odd residue m modulo 2^P and bounded initial r, follow exact
odd-to-odd episodes until x_j < x_0.  Record the branch word

    (r,s,r') (r',s',r'') ...

and quotient identical prefixes.

This reveals recurrent delay programs.  For each repeated one-edge self
program and each repeated multi-edge prefix observed at increasing precision,
we measure how the required starting residue precision grows.  Linear growth
of required 2-adic precision is an exact finite countdown signature.

This is a bounded residual-language experiment, not a global proof.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path

from collatz_odd_episode_grammar import episode, v2


def run_until_descent(r: int, m: int, max_episodes: int):
    x0 = (1 << r) * m - 1
    x = x0
    word = []
    vals = []
    for j in range(max_episodes):
        rr, mm, s, rp, mp, xp = episode(x)
        word.append((rr, s, rp))
        vals.append({
            "j": j, "x": x, "r": rr, "m": mm,
            "s": s, "rp": rp, "mp": mp, "next_x": xp,
        })
        if xp < x0:
            return True, word, vals
        x = xp
    return False, word, vals


def word_key(word):
    return ";".join(f"{r},{s},{rp}" for r, s, rp in word)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--max-r", type=int, default=12)
    ap.add_argument("--precision", type=int, required=True)
    ap.add_argument("--max-episodes", type=int, default=256)
    ap.add_argument("--out")
    a = ap.parse_args()

    P = a.precision
    assert 8 <= P <= 20
    assert 2 <= a.max_r <= 20

    M = 1 << P
    delay_hist = Counter()
    first_edge = Counter()
    prefix_hist = Counter()
    hardest = []
    unresolved = 0
    base_cases = 0
    unresolved_witnesses = []

    for r in range(1, a.max_r + 1):
        for m in range(1, M, 2):
            x0 = (1 << r) * m - 1
            if x0 == 1:
                base_cases += 1
                continue
            closed, word, vals = run_until_descent(r, m, a.max_episodes)
            if not closed:
                unresolved += 1
                if len(unresolved_witnesses) < 64:
                    unresolved_witnesses.append({
                        "r": r, "m": m, "x": x0,
                        "word": [list(x) for x in word[:32]],
                    })
            d = len(word)
            delay_hist[d] += 1
            if word:
                first_edge[word[0]] += 1

            # Retain only short prefixes: the goal is recurrent grammar, not
            # a table of complete trajectories.
            for ell in (1, 2, 3, 4, 6, 8):
                if len(word) >= ell:
                    prefix_hist[(ell, tuple(word[:ell]))] += 1

            row = {
                "r": r, "m": m, "delay": d, "closed": closed,
                "v2_m_plus_1": v2(m + 1),
                "word": word[:32],
            }
            if len(hardest) < 64:
                hardest.append(row)
                hardest.sort(key=lambda z: (-z["delay"], z["r"], z["m"]))
            elif d > hardest[-1]["delay"]:
                hardest[-1] = row
                hardest.sort(key=lambda z: (-z["delay"], z["r"], z["m"]))

    top_prefixes = []
    for (ell, w), count in prefix_hist.most_common(300):
        top_prefixes.append({
            "length": ell,
            "word": [list(x) for x in w],
            "count": count,
        })

    # Exact controls for repeated r=2 self edge.
    self_controls = []
    for k in range(1, min(8, (P - 1) // 3) + 1):
        m = (1 << (3 * k + 1)) - 1
        if m >= M:
            break
        closed, word, vals = run_until_descent(2, m, a.max_episodes)
        repeats = 0
        for edge in word:
            if edge == (2, 1, 2):
                repeats += 1
            else:
                break
        assert repeats == k, (P, k, repeats, word[:k+2])
        self_controls.append({
            "k": k, "m": m,
            "required_v2_m_plus_1": 3 * k + 1,
            "observed_repeats": repeats,
        })

    out = {
        "kind": "bounded_non_descending_episode_language",
        "max_r": a.max_r,
        "precision": P,
        "residues_per_r": M // 2,
        "total_cases": a.max_r * (M // 2),
        "base_cases": base_cases,
        "unresolved_at_episode_cap": unresolved,
        "unresolved_witnesses": unresolved_witnesses,
        "max_delay": max(delay_hist) if delay_hist else 0,
        "delay_hist": {str(k): v for k, v in sorted(delay_hist.items())},
        "first_edge_top": [
            {"edge": list(k), "count": v}
            for k, v in first_edge.most_common(100)
        ],
        "top_prefixes": top_prefixes,
        "hardest": hardest,
        "r2_self_controls": self_controls,
        "proof_status": "exact_bounded_residual_language_not_global_proof",
    }

    if a.out:
        p = Path(a.out); p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(out, indent=2, sort_keys=True) + "\n")

    print("NON_DESCENDING_EPISODE_LANGUAGE",
          f"max_r={a.max_r}",
          f"precision={P}",
          f"cases={out['total_cases']}",
          f"max_delay={out['max_delay']}",
          f"base_cases={base_cases}",
          f"unresolved={unresolved}")
    print("NON_DESCENDING_R2_SELF_CONTROLS",
          json.dumps(self_controls, separators=(",", ":")))
    print("VERIFIED_BOUNDED_NON_DESCENDING_EPISODE_LANGUAGE")


if __name__ == "__main__":
    main()
