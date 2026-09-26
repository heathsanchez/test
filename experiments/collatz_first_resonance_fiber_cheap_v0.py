#!/usr/bin/env python3
"""Cheap exact fiber consequence from the qualified depth-14 endpoint language."""
import json
G=4_142_380_787
counts=[1,1,2,3,4,7,11,16,27,46,80,144,242,436]
rows=[]
for a,e in enumerate(counts,1):
    M=1<<a
    assert G>=M-1
    rows.append(dict(depth=a,endpoint_cells=e,modulus=M,
        gap_saturates_source_residues=True,source_residue_count=M))
print(json.dumps({
 "schema":"COLLATZ_FIRST_RESONANCE_FIBER_CHEAP_V0",
 "qualified_endpoint_depth":14,
 "gap":G,
 "rows":rows,
 "consequence":"At every currently qualified endpoint depth, 2^a <= G+1, so 0<=y-n<=G permits every source residue mod 2^a. The near-return gap cannot supply the missing source language at this boundary.",
 "residual":"SOURCE_ADMISSION: derive the coefficient-persistent/minimal-bad source language and its exact relation to the endpoint survivor quotient.",
 "global_collatz":"UNKNOWN"
},indent=2))
