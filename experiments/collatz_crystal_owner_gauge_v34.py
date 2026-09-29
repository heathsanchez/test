#!/usr/bin/env python3
"""Crystal V34: corrected canonical-owner map and gauge audit.

Parents:
  V31 complete K rewind alphabet
  V32 K-density tradeoff
  V33 zero-slack K boundary (graph result retained; owner-map arithmetic superseded)

V33's odd-edge owner map omitted division by 3^12 on the +1 shortcut term.
This audit reconstructs the complete no-B chamber and checks the corrected map
against literal integer predecessor arithmetic on every edge.

For a chamber state s=(S,C,r) and endpoint y congruent r mod 3^12,
  m = (2^S*y-C)/3^12.
After one shortcut bit b to y', the canonical target owner is
  p = (2^S'*y'-C')/3^12.

Correct maps:
  b=0: p = 2^(S'-S-1)m + (...)
  b=1: p = 3*2^(S'-S-1)m
             + 2^(S'-1)/3^12 + (...).

The state-dependent gauge
  z_s(m) = m/2^S + C/(3^12*2^S)
is exactly y/3^12.  Hence every corrected owner edge is conjugate to ordinary
shortcut dynamics:
  z' = z/2                         (bit 0)
  z' = (3*z + 1/3^12)/2           (bit 1).

So owner-map switching alone is presentation.  Any universal closeout must
retain the original-source/carry constraint, not fit a chamber-only owner rank.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from contextlib import redirect_stdout
from fractions import Fraction
import hashlib
import io
import json
import sys

with redirect_stdout(io.StringIO()):
    import collatz_crystal_k_density_tradeoff_v32 as v32

best = v32.best
edges0 = v32.edges
dist = v32.dist
MOD = v32.MOD
N0 = 38_911_100_780_481_085_467

assert MOD == 3**12
assert len(best) == 27_469
assert len(edges0) == 38_991

def shortcut(x: int) -> int:
    return (3*x+1)//2 if x & 1 else x//2

def corrected_map(u: int, v: int, bit: int):
    S,C,_ = best[u]
    Sp,Cp,_ = best[v]
    if bit == 0:
        a = Fraction(2**Sp, 2**(S+1))
        b = a*Fraction(C,MOD) - Fraction(Cp,MOD)
    else:
        a = Fraction(3*2**Sp, 2**(S+1))
        b = (
            Fraction(2**(Sp-1), MOD)
            + a*Fraction(C,MOD)
            - Fraction(Cp,MOD)
        )
    return a,b

corrected = []
literal_checks = 0
gauge_checks = 0

for u,v,bit,cls,drop in edges0:
    S,C,_ = best[u]
    Sp,Cp,_ = best[v]
    a,b = corrected_map(u,v,bit)

    # Pick the least nonnegative representative with the required parity.
    y = u if (u & 1) == bit else u + MOD
    assert y % MOD == u
    assert (y & 1) == bit

    m_num = (2**S)*y - C
    assert m_num % MOD == 0
    m = m_num // MOD

    yp = shortcut(y)
    assert yp % MOD == v
    p_num = (2**Sp)*yp - Cp
    assert p_num % MOD == 0
    p = p_num // MOD

    assert Fraction(p) == a*m+b
    literal_checks += 1

    # Exact gauge conjugacy.
    cu = Fraction(C, MOD*(2**S))
    cv = Fraction(Cp, MOD*(2**Sp))
    gauge_slope = a*Fraction(2**S,2**Sp)
    gauge_const = b/Fraction(2**Sp) + cv - gauge_slope*cu
    if bit == 0:
        assert gauge_slope == Fraction(1,2)
        assert gauge_const == 0
    else:
        assert gauge_slope == Fraction(3,2)
        assert gauge_const == Fraction(1,2*MOD)

    # Also check z_s(m)=y/M literally.
    assert Fraction(m,2**S) + cu == Fraction(y,MOD)
    assert Fraction(p,2**Sp) + cv == Fraction(yp,MOD)
    gauge_checks += 1

    corrected.append((u,v,bit,cls,drop,a,b,S,Sp))

assert literal_checks == 38_991
assert gauge_checks == 38_991

# Complete corrected K-map classification.
k_rows = [e for e in corrected if e[3] == "K"]
assert len(k_rows) == 4_282

k_shape = Counter()
contracting_fixed_points = []
expanding_b = Counter()
for e in k_rows:
    _u,_v,_bit,_cls,_drop,a,b,_S,_Sp = e
    if a < 1:
        k_shape["slope_lt_1"] += 1
        contracting_fixed_points.append(b/(1-a))
    elif a == 1:
        assert b < 0
        k_shape["slope_eq_1_negative_shift"] += 1
    else:
        assert a == Fraction(3,2)
        k_shape["slope_gt_1"] += 1
        expanding_b[b] += 1

assert k_shape == Counter({
    "slope_lt_1": 3838,
    "slope_eq_1_negative_shift": 42,
    "slope_gt_1": 402,
})
assert max(contracting_fixed_points) == 15
assert min(contracting_fixed_points) == -21
assert expanding_b == Counter({
    Fraction(-3,2):342,
    Fraction(-7,2):52,
    Fraction(-15,2):8,
})

# Every corrected K map except the 402 same-cost odd expanders strictly lowers
# every owner m >= 16.
for e in k_rows:
    _u,_v,_bit,_cls,_drop,a,b,_S,_Sp=e
    if a <= 1:
        assert a*16+b < 16

# V33 zero-slack graph conclusion is independent of the bad owner intercept.
zero = []
adj = defaultdict(list)
for u,v,bit,cls,drop in edges0:
    w = 19*bit - 12 + 19*drop
    rc = w + dist[u] - dist[v]
    assert rc >= 0
    if rc == 0:
        row=(u,v,bit,cls,drop)
        zero.append(row)
        adj[u].append(row)

sys.setrecursionlimit(200_000)
index={}; low={}; stack=[]; on=set(); comps=[]
counter=0

def strong(v):
    global counter
    index[v]=low[v]=counter
    counter += 1
    stack.append(v); on.add(v)
    for _u,w,_bit,_cls,_drop in adj.get(v,()):
        if w not in index:
            strong(w); low[v]=min(low[v],low[w])
        elif w in on:
            low[v]=min(low[v],index[w])
    if low[v]==index[v]:
        cc=[]
        while True:
            w=stack.pop(); on.remove(w); cc.append(w)
            if w==v: break
        comps.append(cc)

for v in best:
    if v not in index:
        strong(v)

recurrent=[]
for cc in comps:
    s=set(cc)
    ee=[e for e in zero if e[0] in s and e[1] in s]
    cyc=len(cc)>1 or any(e[0]==e[1] for e in ee)
    if cyc:
        recurrent.append((cc,ee))

assert len(recurrent)==66
for cc,ee in recurrent:
    assert len(cc)==19 and len(ee)==19
    assert sum(e[2] for e in ee)==12
    assert sum(e[4] for e in ee)==0
    assert Counter(e[3] for e in ee)==Counter({"I":19})


# Source-anchor control: a cost-20/B transition can be a strict local block
# contraction while remaining far above the original source.  Therefore V30
# does not license deleting B from the minimal-bad graph.
r0 = 233
S0,C0,w0 = best[r0]
assert S0 == 16 and C0 == 920981
y0_num = MOD*N0 + C0
assert y0_num % (2**S0) == 0
y = y0_num // (2**S0)
assert y == 315535801847528816873
m = N0
r = r0
first_B = None
for depth in range(16, 80):
    bit = y & 1
    S,C,w = best[r]
    nw = v32.next_window(w, bit)
    cls,v = v32.classify_word(nw)
    if cls == "B":
        yp = shortcut(y)
        first_B = {
            "depth": depth,
            "window_owner": m,
            "endpoint_before": y,
            "endpoint_after": yp,
        }
        break
    opts=[e for e in corrected if e[0]==r and e[1]==v and e[2]==bit and e[3]==cls]
    assert len(opts)==1
    _u,_v,_bit,_cls,_drop,a,b,_S,_Sp=opts[0]
    mp=a*m+b
    assert mp.denominator==1
    m=int(mp)
    y=shortcut(y)
    r=v

assert first_B is not None
assert first_B["depth"] == 54
assert first_B["endpoint_after"] < first_B["window_owner"]
assert first_B["endpoint_after"] > N0

# Correct the V33 sharp K cycle.
cycle=[
169775,254663,381995,41552,328049,492074,246037,369056,184528,
92264,46132,23066,300320,184760,92380,46190,335006,236789,384115,
44732,332819,499229,217403,374422,187211,359326,179663,269495,
404243,74924,378107,35720,17860,8930,279116,139558,475058,237529,
356294,178147,267221,399331,67556,33778,316388,158194,503012,
488798,467477,169775
]
lookup=defaultdict(list)
for e in corrected:
    lookup[(e[0],e[1])].append(e)

A=Fraction(1)
B=Fraction(0)
qsum=Dsum=w18=0
for u,v in zip(cycle[:-1],cycle[1:]):
    opts=lookup[(u,v)]
    assert opts
    e=min(opts,key=lambda z:19*z[2]-12+18*z[4])
    _u,_v,bit,_cls,drop,a,b,_S,_Sp=e
    B=a*B+b
    A=a*A
    qsum += bit
    Dsum += drop
    w18 += 19*bit-12+18*drop

assert len(cycle)-1 == 49
assert qsum==29 and Dsum==2 and w18==-1
assert A == Fraction(3**29,2**49)
assert B == Fraction(1596699704000581,562949953421312)
fixed=B/(1-A)
assert fixed == Fraction(1596699704000581,494319576056429)
assert fixed < 4
assert A*N0+B < N0

payload={
  "schema":"COLLATZ_CRYSTAL_OWNER_GAUGE_V34",
  "parents":{
    "V31":"collatz-crystal-k-rewind-v31@dcc994ab36741ac1bc42edb29001631530f70835",
    "V32":"collatz-crystal-k-density-tradeoff-v32@c3d0cee0c5793fd1cb15e46b5e2429f47da35b17",
    "V33":"collatz-crystal-k-boundary-v33@8ed63c9d6c1312e656c181a89d1073173c22dcec"
  },
  "owner_map_correction":{
    "literal_edges_checked":literal_checks,
    "odd_edge_bug":"V33 omitted division by 3^12 on the +1 term",
    "correct_odd_constant":"2^(S'-1)/3^12 + a*C/3^12 - C'/3^12",
    "V33_graph_conclusions_preserved":True,
    "V33_owner_fixed_point_superseded":True,
  },
  "gauge_certificate":{
    "edges_checked":gauge_checks,
    "coordinate":"z_s(m)=m/2^S + C/(3^12*2^S)=y/3^12",
    "bit0":"z'=z/2",
    "bit1":"z'=(3*z+1/3^12)/2",
    "consequence":"canonical owner switching is a finite-state gauge of endpoint shortcut dynamics; chamber-only owner Lyapunov claims require source/carry evidence"
  },
  "corrected_K_maps":{
    "total":len(k_rows),
    "slope_lt_1":k_shape["slope_lt_1"],
    "slope_eq_1_negative_shift":k_shape["slope_eq_1_negative_shift"],
    "slope_gt_1":k_shape["slope_gt_1"],
    "contracting_fixed_point_min":str(min(contracting_fixed_points)),
    "contracting_fixed_point_max":str(max(contracting_fixed_points)),
    "only_expanding_maps":{
      "(3m-3)/2":expanding_b[Fraction(-3,2)],
      "(3m-7)/2":expanding_b[Fraction(-7,2)],
      "(3m-15)/2":expanding_b[Fraction(-15,2)],
    }
  },
  "B_source_anchor_control":{
    "first_B_transition_on_V23_representative":first_B,
    "local_descent":True,
    "direct_source_descent":False,
    "consequence":"V30 proves local 12-odd block contraction, not OrdinaryExit; B cannot be deleted from the live minimal-bad graph without source-margin evidence"
  },
  "zero_slack_boundary":{
    "recurrent_components":len(recurrent),
    "shape":"66 pure-I cycles, each length 19 with 12 odd steps and no K-drop",
    "conditional_boundary":"valid on the V32 no-B graph only",
    "unchanged_from_V33":True
  },
  "corrected_sharp_K_cycle":{
    "length":49,
    "odd_steps":qsum,
    "K_drop":Dsum,
    "slope_num":A.numerator,
    "slope_den":A.denominator,
    "intercept_num":B.numerator,
    "intercept_den":B.denominator,
    "fixed_point_num":fixed.numerator,
    "fixed_point_den":fixed.denominator,
    "fixed_point_lt_4":True,
    "contracts_V23_source_floor":True
  },
  "scientific_verdict":"V33_OWNER_MAP_ARITHMETIC_CORRECTED; V32_V33_GRAPH_RESULTS_RETAINED_ONLY_CONDITIONALLY_ON_NO_B; OWNER_ONLY_CLOSEOUT_REJECTED_AS_PRESENTATION_GAUGE",
  "next_residual":{
    "name":"SOURCE_ANCHORED_B_K_MARGIN",
    "statement":"Return to V27's exact residual: carry the fixed original source n and canonical source-relative margin through both B and K events. V30 B contraction is local only; the finite owner coordinate is gauge-equivalent to endpoint dynamics.",
    "forbidden_shortcuts":["reuse V33 owner fixed point","fit chamber-only owner rank","larger 3-adic chamber"]
  },
  "universal_status":"UNKNOWN",
  "global_collatz":"UNKNOWN"
}
payload["certificate_sha256"]=hashlib.sha256(
    json.dumps(payload,sort_keys=True,separators=(",",":")).encode()
).hexdigest()
print(json.dumps(payload,indent=2,sort_keys=True))
