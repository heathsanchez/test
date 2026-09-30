#!/usr/bin/env python3
"""V56: pull V35's arbitrary expanding-owner shadows back to exact V23 sources.

V35 constructs, for every r, one 2-adic owner cylinder whose first r returns
at V34 chamber state 514835 all use the expanding map
    F(m)=(19683*m+18403)/2048.
V36 proves one such expanding return is source-admitted from the sole V23
source cell after an exact common 73-step prefix.

This gate composes those two facts.  Because every source in the same 73-bit
prefix has
    n = n0 + 2^73*s
and V23 requires s=3^8*u,
the V34 owner parameter at depth 73 is
    t_owner = t_owner0 + 3^47*u.
Hence for V35's r-return guard R_r (mod 2^(11r)) there is a unique source
extension
    u_r = (R_r-t_owner0)*(3^47)^(-1) mod 2^(11r),
    T_r = T0 + 2^14*u_r,
    n_r = N0 + 2^59*3^8*T_r.

We verify exact actual-source execution, no D/S/M1 exit through the r-return
shadow, and where the shadow lies relative to source-tail exhaustion.

This is a causal/source-admission theorem-discovery gate.  It does not prove
arbitrary-r in Lean and does not prove Collatz.
"""
from __future__ import annotations
from contextlib import redirect_stdout
import hashlib, io, json

with redirect_stdout(io.StringIO()):
    import collatz_crystal_parameter_quotient_v25 as v25
    import collatz_crystal_k_return_separator_v34 as v34
    import collatz_crystal_expanding_shadow_v35 as v35
    import collatz_crystal_source_admitted_return_v36 as v36

CHECK_R=64
PREFIX_DEPTH=v36.EXPECTED_BASE_DEPTH
BASE=v34.BASE
MOD=v34.MOD

def shortcut(x:int)->int:
    return (3*x+1)//2 if x&1 else x//2

# Reconstruct V36's exact common-prefix affine coefficient.
n0=v25.N0+v25.NC*v36.T_PARAM
y=n0
q=0
prefix_bits=[]
for _ in range(PREFIX_DEPTH):
    prefix_bits.append(y&1)
    q += y&1
    y=shortcut(y)
assert y==v36.base_y
assert q==51
assert v25.NC==(1<<59)*(3**8)
assert PREFIX_DEPTH-59==14

Sbase,Cbase,_=v34.best[BASE]
assert Sbase==13
owner_t0=v36.owner_t
assert v36.base_owner==v35.owner(owner_t0)
assert owner_t0%v35.B==v35.R_ONE

# If source parameter T increases by 2^14*u, source increases by
# 2^73*3^8*u. The shared prefix sends that to endpoint increment 3^(q+8)u.
# Canonical owner division by 3^12 and 2^13 scaling then makes owner
# parameter increase by 3^(q+8-12)=3^47*u.
PULLBACK=3**(q+8-12)
assert PULLBACK==3**47

def first_simple_exit(n:int,depth:int):
    y=n
    for k in range(depth+1):
        if 0<y<n:
            return {"kind":"D","depth":k,"endpoint":str(y)}
        if y%8==5 and y<=4*n:
            return {"kind":"S","depth":k,"endpoint":str(y),
                    "owner":str((y-1)//4)}
        if y%3==2:
            p=(2*y-1)//3
            if 0<p<n:
                assert shortcut(p)==y
                return {"kind":"M1","depth":k,"endpoint":str(y),
                        "lower_source":str(p)}
        if k<depth:
            y=shortcut(y)
    return None

R=v35.R_ONE
M=v35.B
rows=[]
min_tail_margin=None
for r in range(1,CHECK_R+1):
    inv=pow(PULLBACK,-1,M)
    u=((R-owner_t0)*inv)%M
    T=v36.T_PARAM+(1<<14)*u
    n=v25.N0+v25.NC*T

    # Exact V23-cell and shared-prefix checks.
    assert n==n0+(1<<PREFIX_DEPTH)*(3**8)*u
    yy=n
    bits=[]
    for _ in range(PREFIX_DEPTH):
        bits.append(yy&1)
        yy=shortcut(yy)
    assert bits==prefix_bits
    assert yy==v36.base_y+(3**(q+8))*u

    num=(1<<Sbase)*yy-Cbase
    assert num%MOD==0
    m=num//MOD
    assert (m-v35.BASE_RESIDUE)%v35.BASE_SCALE==0
    owner_t=(m-v35.BASE_RESIDUE)//v35.BASE_SCALE
    assert owner_t==owner_t0+PULLBACK*u
    assert owner_t%M==R

    # Replay every V34 expanding return on the actual orbit.
    target=PREFIX_DEPTH+len(v34.expanding)*r
    ycur=yy
    ocur=owner_t
    return_rows=[]
    for i in range(r):
        assert ocur%v35.B==v35.R_ONE
        for e in v34.expanding:
            assert ycur%MOD==e[0]
            assert ycur&1==e[2]
            ycur=shortcut(ycur)
            assert ycur%MOD==e[1]
        ocur=v35.E(ocur)
        num=(1<<Sbase)*ycur-Cbase
        assert num%MOD==0
        mcur=num//MOD
        assert mcur==v35.owner(ocur)
        return_rows.append({
            "return":i+1,
            "depth":PREFIX_DEPTH+len(v34.expanding)*(i+1),
            "owner_parameter":str(ocur),
            "owner":str(mcur),
        })

    ex=first_simple_exit(n,target)
    assert ex is None

    # SourceProduct tail is provably zero only after depth > log2(source).
    # If target < bit_length(n), this shadow is explicitly still funded by
    # a nonzero source tail and therefore does not contradict post-zero V53.
    bitlen=n.bit_length()
    tail_margin=bitlen-target
    if min_tail_margin is None or tail_margin<min_tail_margin:
        min_tail_margin=tail_margin

    rows.append({
      "repeats":r,
      "shadow_guard_residue":str(R),
      "shadow_guard_modulus":str(M),
      "source_pullback_u":str(u),
      "v23_parameter_T":str(T),
      "source":str(n),
      "source_bits":bitlen,
      "shadow_end_depth":target,
      "source_bits_minus_shadow_end":tail_margin,
      "shadow_finishes_before_zero_tail":target<bitlen,
      "no_simple_exit_through_shadow":True,
      "base_owner_ge_source":m>=n,
      "first_return":return_rows[0],
      "last_return":return_rows[-1],
    })

    R,M=v35.next_shadow_residue(R,M)

all_pre_zero=all(z["shadow_finishes_before_zero_tail"] for z in rows)
all_owner_ge=all(z["base_owner_ge_source"] for z in rows)

result={
 "schema":"COLLATZ_CRYSTAL_V23_SOURCE_SHADOW_V56",
 "parents":{
   "V35":"collatz-crystal-expanding-shadow-v35@ed2d430005a4db5abd0939050f0438e82733b385",
   "V36":"collatz-crystal-source-admitted-return-v36@2bc7f481eb0a2ea2130f545d0ba4cd4d5718360d",
 },
 "derived_source_pullback":{
   "prefix_depth":PREFIX_DEPTH,
   "prefix_odd_count":q,
   "v23_step":"T=T0+2^14*u",
   "owner_parameter_step":"t_owner=t_owner0+3^47*u",
   "guard_solution":"u=(R_r-t_owner0)*(3^47)^(-1) mod 2^(11r)",
 },
 "checked_repeats":CHECK_R,
 "all_exact_v23_sources":True,
 "all_execute_declared_expanding_returns":True,
 "all_no_simple_exit_through_shadow":True,
 "all_base_owners_ge_original_source":all_owner_ge,
 "all_shadows_finish_before_source_tail_zero":all_pre_zero,
 "minimum_source_bit_margin_over_shadow_end":min_tail_margin,
 "first_rows":rows[:12],
 "last_row":rows[-1],
 "verdict":(
   "V35_SHADOWS_LIFT_TO_EXACT_V23_SOURCES_BUT_REMAIN_PRE_ZERO_ON_CHECKED_FAMILY"
   if all_pre_zero and all_owner_ge
   else "SOURCE_PULLBACK_SEPARATOR"
 ),
 "interpretation":(
   "Arbitrarily deep owner shadows are not merely free-owner artifacts: the "
   "V35 guard pulls back exactly through V36 to V23 natural-source cylinders. "
   "On the checked recurrence, however, every expanding shadow ends before "
   "source-tail exhaustion, so this family does not itself refute the V53 "
   "post-zero residual DAG. The next theorem target is the arbitrary-r version "
   "of that pre-zero-tail separation, or a genuinely post-zero aperiodic family."
 ),
 "promotion_boundary":(
   "The recurrence formula is exact, but the arbitrary-r source-tail inequality "
   "is not yet proved here. Global Collatz remains dependent on post-zero "
   "all-depth residual exclusion."
 ),
 "global_collatz":"UNKNOWN",
}
result["certificate_sha256"]=hashlib.sha256(
 json.dumps(result,sort_keys=True,separators=(",",":")).encode()
).hexdigest()
print(json.dumps(result,indent=2,sort_keys=True))
