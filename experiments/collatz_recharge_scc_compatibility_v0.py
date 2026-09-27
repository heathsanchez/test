#!/usr/bin/env python3
"""Exact symbolic compatibility audit for the only prospective recharge SCC."""
import json
import collatz_q0_rigid_recharge_audit as r

# The SCC centres are q=7/23 and q=-1 at anchor r=2.
# Recover concrete certificates by enumerating the small return words appearing
# in the qualified audit: q=7/23 is word ((2,3,2),), q=-1 is ((2,1,2),).
a=r.certificate(((2,3,2),))
b=r.certificate(((2,1,2),))
assert a["q"]==(7,23) and b["q"]==(-1,1)
ab=r.separation(a,b); ba=r.separation(b,a)
# Domain cylinders modulo 2^(D+1); simultaneous admissibility iff residues
# agree modulo the smaller modulus.
bits=min(a["D"]+1,b["D"]+1)
mask=(1<<bits)-1
compatible=((a["rho"]-b["rho"])&mask)==0
print(json.dumps({
 "schema":"COLLATZ_RECHARGE_SCC_COMPATIBILITY_V0",
 "a":{k:a[k] for k in ("q","D","rho","modulus","A","B","C")},
 "b":{k:b[k] for k in ("q","D","rho","modulus","A","B","C")},
 "separation_ab":ab,"separation_ba":ba,
 "common_domain_bits":bits,"simultaneously_admissible":compatible,
 "interpretation":"same state cannot lie in both return cylinders" if not compatible else "overlap requires deeper audit",
 "global_collatz":"UNKNOWN"},indent=2,default=list))
assert not compatible
