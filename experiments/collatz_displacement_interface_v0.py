#!/usr/bin/env python3
"""Exact information-threshold audit for the first-resonance displacement.

The live near-return displacement delta=y-n is an integer in [0,G].
For modulus M<=G+1 every residue class mod M occurs, so a residue observation
cannot constrain delta. For M>G, residues identify delta injectively on [0,G].
This computes the first informative pure 2-adic, pure 3-adic and mixed 2^a3^b
interfaces and Pareto-minimal mixed interfaces.

No Collatz closure is claimed: source/endpoint laws must still earn the
corresponding congruence on delta.
"""
import json
G=4_142_380_787

def first_power(base):
    a=0;m=1
    while m<=G:
        a+=1;m*=base
    return a,m

a2,m2=first_power(2)
a3,m3=first_power(3)
assert (a2,m2)==(32,2**32)
assert (a3,m3)==(21,3**21)

mixed=[]
for a in range(0,33):
    for b in range(0,22):
        M=(2**a)*(3**b)
        if M<=G: continue
        # Pareto minimal: reducing either positive exponent drops to <=G.
        min2=(a==0 or (2**(a-1))*(3**b)<=G)
        min3=(b==0 or (2**a)*(3**(b-1))<=G)
        if min2 and min3:
            mixed.append(dict(a=a,b=b,modulus=M,overshoot=M-G,
                              bit_cost=a+b*1.584962500721156))
mixed.sort(key=lambda z:(z["bit_cost"],z["modulus"]))
assert any(z["a"]==1 and z["b"]==20 for z in mixed)

# Existing protected coordinates reach endpoint Q2 depth 20 and reverse Q3
# depth 20. A same-difference congruence mod 2*3^20 would already be injective.
M=2*3**20
assert M>G

result={
 "schema":"COLLATZ_DISPLACEMENT_INTERFACE_V0",
 "gap":G,
 "delta_domain_size":G+1,
 "binary":{"first_injective_depth":a2,"modulus":m2},
 "ternary":{"first_injective_depth":a3,"modulus":m3},
 "mixed_pareto_minimal":mixed,
 "existing_squeeze_interface":{
   "a":1,"b":20,"modulus":M,"injective_on_delta":True,
   "meaning":"if a live pair earns delta == 0 mod 2*3^20, then delta=0 exactly"
 },
 "critical_missing_binding":
   "earn source/endpoint congruence on delta; endpoint cell membership alone does not imply it",
 "experiment_reorientation":
   "query which warranted source-admission law predicts delta residues modulo Pareto-minimal 2^a3^b interfaces",
 "global_collatz":"UNKNOWN"
}
print(json.dumps(result,indent=2))
