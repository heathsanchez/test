#!/usr/bin/env python3
"""Exact bounded fiber-product census for the first Farey live resonance.

This joins the canonical endpoint survivor language to the only extra
source-relative datum forced by 0 <= y-n <= G: the displacement carry across
an endpoint Q2 cylinder. It is a falsifier/representation census, not a Collatz
proof. No coefficient-persistent source-admission theorem is assumed.
"""
import argparse, json
from pathlib import Path
import collatz_reverse_trit_bicell_v3_quotient as v3
import collatz_transfer_farey as farey

G=farey.live_gap_ceiling
L=farey.L

def source_residues_for_endpoint(yres,a):
    M=1<<a
    # n=y-delta, 0<=delta<=G.  Return all source residues modulo M.
    if G>=M-1:
        return list(range(M))
    return sorted({(yres-d)%M for d in range(G+1)})

def carry_classes(yres,a):
    M=1<<a
    # y = yres + M*q, n=y-d.  Relative quotient carry is
    # floor((yres-d)/M); it is bounded even when source residue is not.
    lo=(yres-G)//M
    return list(range(lo,1))

def run(max_depth,out):
    parents,langs,rows=v3.evolve(max_depth)
    result_rows=[]
    for a in range(1,max_depth+1):
        sets=[tuple(sorted(langs[a][i])) for i in range(len(parents))]
        assert all(x==sets[0] for x in sets)
        E=sets[0]
        M=1<<a
        carries=sorted({c for y in E for c in carry_classes(y,a)})
        saturated=G>=M-1
        # If saturated, the near-return relation itself imposes no source
        # residue restriction at this depth: every residue occurs.
        source_count=M if saturated else len({r for y in E for r in source_residues_for_endpoint(y,a)})
        row=dict(depth=a,endpoint_cells=len(E),modulus=M,
                 gap_saturates_source_residues=saturated,
                 source_residue_count=source_count,
                 carry_min=min(carries),carry_max=max(carries),
                 carry_class_count=len(carries))
        result_rows.append(row)
        print("FIBER",json.dumps(row,sort_keys=True))
    result=dict(schema="COLLATZ_FIRST_RESONANCE_FIBER_V0",
        gap=G,live_lower=L,max_depth=max_depth,rows=result_rows,
        interpretation=("For every depth with 2^a <= G+1, the near-return gap "
          "alone leaves every source residue possible. Endpoint language plus "
          "gap is therefore not the missing source-admission theorem."),
        missing_premise=("exact coefficient-persistence/minimal-bad source language "
          "and its relation to the endpoint survivor quotient"),
        verdict="EXACT_FIBER_REPRESENTATION_WITH_SOURCE_ADMISSION_RESIDUAL",
        scope="first Farey live resonance; exact endpoint quotient and gap only; no Collatz theorem")
    out.parent.mkdir(parents=True,exist_ok=True); out.write_text(json.dumps(result,indent=2)+"\n")

if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--max-depth",type=int,default=14);p.add_argument("--output",type=Path,required=True)
    a=p.parse_args();run(a.max_depth,a.output)
