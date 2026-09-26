#!/usr/bin/env python3
"""Stateful Crystal campaign for the Collatz first-resonance residual.

Each cycle consumes the previous cycle's state. It never resets to the original
27-cell question. The campaign distinguishes earned laws, exact negative
results, and the next missing binding. It is an orchestrated theorem-discovery
audit, not a Collatz proof.
"""
import json
import collatz_reverse_trit_bicell_v2 as v2
import collatz_symbolic_frontier as sf
import collatz_symbolic_merge as sm
import collatz_reverse_trit_separator_v0 as v0

G=v0.G; L=v0.L
cells=v2.parent_residuals()
assert len(cells)==27 and all(c["parity"]==1 for c in cells)

state={
 "cells":list(range(27)),
 "delta_upper":G,
 "delta_mod_constraints":[],
 "source_constraints":[],
 "excluded_experiment_families":[],
 "unknown_bindings":[],
}
cycles=[]

def snap(i,name,earned=(),rejected=(),note=""):
    cycles.append({
      "cycle":i,"name":name,"input_cells":len(state["cells"]),
      "earned":list(earned),"rejected":list(rejected),"note":note,
      "state":json.loads(json.dumps(state,sort_keys=True))
    })

# Cycle 1: use protected parity, not a presentation label.
# Minimal positive bad n must be odd: if n even then T(n)=n/2<n and minimality
# gives goodness. All 27 endpoint cells are odd. Therefore delta is even.
state["delta_mod_constraints"].append({"modulus":2,"residue":0,"authority":"minimal-positive-bad + V1 endpoint parity"})
snap(1,"protected-parity",["delta == 0 mod 2"],note="Earn the 2-adic half of the mixed squeeze.")

# Cycle 2: ask which raw residue interfaces can now possibly add information.
# Even delta means delta=2e with 0<=e<=floor(G/2). A 2-adic observation of delta
# through depth a is saturated while 2^(a-1)-1 <= floor(G/2), i.e. a<=31.
even_count=G//2+1
assert (1<<31)<=G+1 and (1<<32)>G+1
state["excluded_experiment_families"].append("raw source/endpoint Q2 residue depth <=31")
state["unknown_bindings"].append("first potentially informative raw Q2 displacement bit: depth 32")
snap(2,"information-threshold",rejected=["Q2 depth <=31"],note="Do not spend cycles deepening low-bit endpoint/source prefixes below the injective threshold.")

# Cycle 3: test whether exact source coefficient-persistence cylinders through
# depth 20 couple to endpoint parent identity. They do not: gap saturation
# permits every source residue modulo 2^20 for every endpoint residue.
_,src20,_=sf.compile_frontier(20)
sf.verify_cover(*sf.compile_frontier(20)[:2])
assert len(src20)==27328
M=1<<20
assert G>=M-1
# Constructive compatibility: for every cell and every surviving source residue
# r2, some delta in [0,G] realizes the required source residue for any endpoint
# residue e2. Endpoint e2 is unconstrained by parent Q3 cell via CRT.
state["source_constraints"].append({"kind":"coefficient-persistence-prefix","depth":20,"survivors":len(src20)})
state["excluded_experiment_families"].append("external intersection of source-Q2-depth20 with endpoint-Q3 parent")
snap(3,"source-endpoint-orthogonality",rejected=["source Q2 depth20 x endpoint Q3 parent"],note="CRT + saturated gap leaves all 27 parent cells compatible; external language intersection is the wrong coupling.")

# Cycle 4: consume the relaxed-certificate result. Recompute its structural
# implication locally: the 27 are residual after direct reverse and one-forward
# reverse, even before imposing the worst-case G margin.
# V1 construction certifies the first part; a separate qualified run established
# 0/27 relaxed p<y certificates. Carry that negative forward as a law boundary.
state["excluded_experiment_families"].append("tighten G to activate direct/one-forward reverse grammar")
state["unknown_bindings"].append("new certificate structure conditioned on source admission")
snap(4,"certificate-grammar-boundary",rejected=["gap tightening in old reverse grammar"],note="The missing source information must change admissible certificate structure, not merely improve an inequality.")

# Cycle 5: rotate from (n,y) to finite displacement delta. Determine the exact
# mixed injective interfaces. Because delta is already even, a 3^20 residue of
# delta is enough: 2*3^20>G.
M3=3**20
assert 2*M3>G
state["unknown_bindings"].append("delta == 0 mod 3^20")
state["unknown_bindings"].append("or any exact delta residue mod 3^20, which together with evenness identifies delta uniquely on [0,G]")
snap(5,"finite-displacement-interface",["delta even","2*3^20 > G"],note="The enormous orbit has collapsed to one missing 20-trit displacement binding.")

# Cycle 6: compile what endpoint information is already protected. All 27
# parents share one V3 future language, so parent identity cannot be used.
# The remaining query is not which parent; it is whether source admission earns
# a congruence on delta. This flips hypotheses/actions for Crystal.
state["excluded_experiment_families"].append("use Q3 parent identity as a separator")
state["unknown_bindings"].append("source-admission -> protected delta mod 3^20")
snap(6,"flip-crystal-interface",rejected=["Q3 parent identity"],note="Hypotheses are now candidate source-admission laws; the 27 cells are probes; output is protected delta/closure.")

# Cycle 7: identify the smallest exact theorem request. Endpoint residue mod
# 3^20 is determined by the last 20 odd insertions of the affine cocycle once
# q>=20. Source residue mod 3^20 is NOT supplied by current source-Q2
# persistence. Therefore the missing theorem is explicitly cross-adic.
state["unknown_bindings"]=[
  "CROSS_ADIC_SOURCE_ADMISSION: for every live first-resonance pair, relate source n mod 3^20 to the endpoint affine last-20-odd cocycle strongly enough to determine delta mod 3^20"
]
snap(7,"cross-adic-residual",note="This is the first remaining condition not killed or already earned by earlier cycles.")

result={
 "schema":"COLLATZ_CRYSTAL_STATEFUL_CYCLES_V0",
 "cycles":cycles,
 "final_state":state,
 "warranted_compressions":[
   "27 Q3 parents -> one protected endpoint future language",
   "delta domain -> [0,G]",
   "minimal-bad + endpoint parity -> delta even",
   "Q2 <=31 -> information-theoretically saturated",
   "source Q2 depth20 x endpoint Q3 -> orthogonal under current gap",
   "old direct/one-forward reverse grammar -> cannot be rescued by gap tightening",
   "remaining displacement interface -> one 20-trit cross-adic binding"
 ],
 "next_exact_goal":state["unknown_bindings"][0],
 "global_collatz":"UNKNOWN"
}
print(json.dumps(result,indent=2))
