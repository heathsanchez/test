#!/usr/bin/env python3
"""Crystal exact-state separator search for stationary-source threshold failure.

No future-label feature is admitted into candidate state. We test simple exact
relations among n, y, q, qmin, affine carry A=2^j*y-3^q*n, and normalized
multiplicative surplus D=3^q*n-2^j*n. The output is diagnostic only.
"""
import json
from fractions import Fraction
from collatz_live_origin_bridge_v1 import language_counts
BITS=24; DEPTH=2000
qmin,_,_=language_counts(DEPTH)
# Focus on record-hard sources from qualified stationary-source run plus deterministic
# broad sample. Record list is explicit evidence, not a learned future feature.
records=[13421671,14378779,8088063,12132095,9280639,13774695,1126015,2252031,1689023,6206655]
sample=set(records)
step=max(1,(1<<BITS)//200000)
for n in range(1,1<<BITS,2*step):
    sample.add(n|1)
rows=[]; source_summary=[]
for n in sorted(sample):
    m=n.bit_length(); y=n; q=0; max_ratio=None; min_margin=None; cross=None; hard=[]
    for j in range(1,DEPTH+1):
        bit=y&1
        if bit:y=(3*y+1)//2;q+=1
        else:y//=2
        A=(y<<j)-(3**q)*n
        assert A>=0
        s=q-qmin[j]
        if j>=m and s>=0:
            # exact present-state coordinates only
            margin=y-n
            # carry relative to multiplicative threshold debt, represented exactly
            mult=(3**q-(1<<j))*n
            hard.append((j,s,bit,y,A,margin,mult))
        if s<0:
            cross=j;break
    if hard:
        # tail state nearest failure (minimum slack, then latest)
        z=min(hard,key=lambda x:(x[1],-x[0]))
        rows.append((n,cross,z))
        source_summary.append({"n":n,"m":m,"crossing":cross,
          "nearest":{"j":z[0],"slack":z[1],"bit":z[2],"y":z[3],
                     "A":str(z[4]),"margin":z[5],"mult_surplus":str(z[6])}})
# Exact identities useful for theorem extraction:
# y-n = ( (3^q-2^j)n + A ) / 2^j.
# At threshold-live states this is >=0 automatically. Test whether A alone must
# eventually fail to compensate when multiplicative surplus turns negative: impossible
# here because s>=0 => 3^q>=2^j. Thus that route is tautological and explicitly rejected.
out={"schema":"COLLATZ_CRYSTAL_STATIONARY_EXACT_STATE_SEPARATOR_V0",
 "sampled_sources":len(sample),"record_sources":records,
 "identity":"2^j*(y-n)=(3^q-2^j)*n+A",
 "finding":"ON_THRESHOLD_LIVE_STATE_MULTIPLICATIVE_SURPLUS_IS_NONNEGATIVE",
 "rejected_candidate":"affine carry A versus multiplicative deficit: no deficit exists while q>=qmin",
 "hard_source_states":[x for x in source_summary if x["n"] in records],
 "next_separator_target":"must use transition/carry evolution, not a static affine inequality",
 "global_collatz":"UNKNOWN"}
print(json.dumps(out,indent=2))
