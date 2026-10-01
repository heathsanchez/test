#!/usr/bin/env python3
"""V69: repeat the residual-first development law on V68's surviving r=30 ray.

For four successive zero siblings, first exhaust the licensed unsplit
uniform-affine reverse grammar.  Only if it produces no strict lower-source
merger do we expose more source-parameter bits, and then only until an already
warranted D/M1/S or q7 consequence first separates a child.

This is a bounded controller/lineage result, not a Collatz proof.
"""
from __future__ import annotations

import hashlib
import json
import multiprocessing as mp

import collatz_r30_separator_v68 as v68

R = 30

EXPECTED_AUDITS = {
    22: dict(prefixes=82, states=14448921, peak=118108, candidates=81, identities=81),
    25: dict(prefixes=85, states=22198788, peak=204623, candidates=84, identities=84),
    29: dict(prefixes=89, states=40112918, peak=381323, candidates=88, identities=88),
    33: dict(prefixes=93, states=66532773, peak=438208, candidates=92, identities=92),
}

EXPECTED_SPLITS = {
    22: dict(depth=25, residue=25165854, suffix=6, kind="M1", k=84),
    25: dict(depth=29, residue=201326622, suffix=6, kind="D", k=88),
    29: dict(depth=33, residue=536870942, suffix=1, kind="D", k=92),
    33: dict(depth=38, residue=180388626462, suffix=21, kind="D", k=97),
}

def audit_prefix(args):
    N, S, row = args
    j, X, slope, q = row
    cs, states, peak = v68.reverse_audit(N, S, X, slope)
    identities = sum(
        z["constant"] == N and z["slope"] == S
        and z["constant_margin"] == 0 and z["slope_margin"] == 0
        for z in cs
    )
    strict = sum(z["constant_margin"] > 0 and z["slope_margin"] >= 0 for z in cs)
    return dict(prefix=j, states=states, peak=peak, candidates=len(cs),
                identities=identities, strict=strict)

def audit_root(h):
    N = v68.N0 + v68.NC * R
    S = v68.NC * 2**h
    prefixes = list(v68.fixed_prefix(N, S))
    args = [(N, S, row) for row in prefixes]
    with mp.Pool(processes=2) as pool:
        rows = pool.map(audit_prefix, args)
    out = dict(
        depth=h,
        prefixes=len(prefixes),
        exact_reverse_states=sum(z["states"] for z in rows),
        max_quotient_states=max(z["peak"] for z in rows),
        nonexpanding_candidates=sum(z["candidates"] for z in rows),
        identity_candidates=sum(z["identities"] for z in rows),
        strict_lower_source_candidates=sum(z["strict"] for z in rows),
    )
    e = EXPECTED_AUDITS[h]
    assert out["prefixes"] == e["prefixes"]
    assert out["exact_reverse_states"] == e["states"]
    assert out["max_quotient_states"] == e["peak"]
    assert out["nonexpanding_candidates"] == e["candidates"]
    assert out["identity_candidates"] == e["identities"]
    assert out["strict_lower_source_candidates"] == 0
    assert out["nonexpanding_candidates"] == out["identity_candidates"]
    return out

def first_split(root_h, target_h):
    live = [R]
    levels = []
    first = None
    for h in range(root_h + 1, target_h + 1):
        closed = []
        residual = []
        for r in live:
            c = v68.simple_certificate(r, h)
            qhits = v68.q7_mergers(r, h)
            if c is None and not qhits:
                residual.append(r)
                continue
            row = dict(c if c is not None else qhits[0])
            row["q7_hits"] = len(qhits)
            closed.append(row)
        levels.append(dict(depth=h, input_cells=len(live),
                           closed=len(closed), residual=len(residual),
                           closed_residues=[z["r"] for z in closed]))
        if closed:
            assert len(closed) == 1
            first = closed[0]
            break
        live = [x for r in residual for x in (r, r + 2**h)]
    assert first is not None
    e = EXPECTED_SPLITS[root_h]
    assert h == e["depth"]
    assert first["r"] == e["residue"]
    assert first["kind"] == e["kind"]
    assert first["k"] == e["k"]
    suffix = (first["r"] - R) // 2**root_h
    assert suffix == e["suffix"]
    assert first["q7_hits"] >= 1
    return dict(root_depth=root_h, levels=levels,
                first_consequential_depth=h,
                extra_parameter_bits=h-root_h,
                suffix_value=suffix,
                child=first)

def main():
    audits = []
    splits = []
    for h in (22, 25, 29, 33):
        audits.append(audit_root(h))
        splits.append(first_split(h, EXPECTED_SPLITS[h]["depth"]))

    suffixes = [z["suffix_value"] for z in splits]
    assert suffixes == [6, 6, 1, 21]

    result = {
        "schema": "COLLATZ_R30_RECURSIVE_REFINEMENT_V69",
        "parent_v68_head": "8bff295a9c4167f819520d86b2ce4052460598d3",
        "protected_present": ["original_source", "current_endpoint"],
        "unsplit_reverse_audits": audits,
        "consequence_forced_splits": splits,
        "total_exact_reverse_states": sum(z["exact_reverse_states"] for z in audits),
        "all_nonexpanding_candidates_are_identity": True,
        "periodic_suffix_6_candidate": "REJECTED_PROSPECTIVELY",
        "periodic_suffix_sequence": suffixes,
        "warranted_bounded_interpretation": (
            "On these four successive r=30 zero siblings, unsplit uniform-affine "
            "reverse search only reconstructs the source ancestry. Progress is "
            "obtained by refining until an already-warranted lower-class merger "
            "first becomes applicable. No fixed suffix/cadence law is promoted."
        ),
        "next_residual": (
            "Test whether ancestry-only reverse candidates can be proved as a "
            "general obstruction for the r=30 zero-tail lineage; otherwise continue "
            "residual-first splitting from the depth-38 zero sibling. Do not expand "
            "protected semantic state."
        ),
        "status": "CANDIDATE_PENDING_KERNEL",
        "global_collatz": "UNKNOWN",
        "qed": False,
    }
    result["certificate_sha256"] = hashlib.sha256(
        json.dumps(result, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    print(json.dumps(result, indent=2, sort_keys=True))

if __name__ == "__main__":
    main()
