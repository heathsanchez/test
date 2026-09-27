#!/usr/bin/env python3
"""Crystal falsifier: stationary canonical source vs threshold-admissible continuation."""
import json
from collatz_live_origin_bridge_v1 import language_counts, first_crossing

BITS=24; DEPTH=2000
qmin,_,_=language_counts(DEPTH)

# For every odd finite source, after j>=bit_length(n), its canonical residue mod 2^j
# is literally n. Measure how long its actual parity continuation remains threshold-live
# after that stationarity point. This directly falsifies any claimed uniform small bound.
records=[]; censored=[]
for n in range(1,1<<BITS,2):
    m=n.bit_length()
    y=n; q=0; crossed=None
    for j in range(1,DEPTH+1):
        bit=y&1
        if bit: y=(3*y+1)//2; q+=1
        else: y//=2
        if q<qmin[j]:
            crossed=j; break
    if crossed is None:
        censored.append({"n":n,"m":m})
    elif crossed>=m:
        records.append({"n":n,"m":m,"crossing":crossed,
                        "stationary_live_length":crossed-m})
records.sort(key=lambda r:(-r["stationary_live_length"],-r["crossing"],r["n"]))
out={"schema":"COLLATZ_CRYSTAL_STATIONARY_SOURCE_THRESHOLD_V0",
 "source_bits":BITS,"depth":DEPTH,
 "tested_odd_sources":1<<(BITS-1),
 "censored_stationary_survivors":len(censored),
 "first_censored":censored[:20],
 "max_stationary_live_length":records[0]["stationary_live_length"] if records else None,
 "record_survivors":records[:40],
 "status":"FINITE_NO_INFINITE_STATIONARY_THRESHOLD_PATH_OBSERVED" if not censored else "FINITE_CENSORED",
 "candidate_theorem":"finite fixed source cannot realize an all-depth threshold-admissible parity continuation",
 "global_collatz":"UNKNOWN"}
print(json.dumps(out,indent=2))
