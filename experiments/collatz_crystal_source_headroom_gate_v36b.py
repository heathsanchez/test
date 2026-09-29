#!/usr/bin/env python3
"""Crystal V36b: source-headroom regime qualification (corrected)."""
from contextlib import redirect_stdout
from fractions import Fraction
import hashlib, io, json

with redirect_stdout(io.StringIO()):
    import collatz_crystal_k_rewind_v31 as v31
    import collatz_crystal_k_density_tradeoff_v32 as v32
    import collatz_crystal_k_boundary_v33 as v33
    import collatz_crystal_k_return_separator_v34 as v34
    import collatz_crystal_expanding_shadow_v35 as v35

N0=38_911_100_780_481_085_467
MOD=3**12

def ceil_div(a,b): return -(-a//b)
def ceil_frac(x): return -(-x.numerator//x.denominator)
def least_ge(r,m,n): return r if r>=n else r+ceil_div(n-r,m)*m

# Exact K source-floor gates.
lower=[]
for row in v31.lower_rows:
    d=row["cost_drop"]; E=row["E"]
    lower.append((d,E,(1<<d)*N0-E))
same=[(row["delta"],N0+row["delta"]) for row in v31.same_rows]
assert len(lower)==3832 and len(same)==450
assert min(x for d,E,x in lower if d==1)==2*N0-7
assert max(x for d,E,x in lower if d==1)==2*N0+13
assert min(x for d,E,x in lower if d==5)==32*N0+33

# Exact B gate: every B edge is bit-0 and cost exactly 20.
b=[]
for u,(_S,_C,w) in sorted(v32.best.items()):
    for bit in (0,1):
        nw=v32.next_window(w,bit)
        cls,_=v32.classify_word(nw)
        if cls!="B": continue
        S=sum(nw); C=v32.cocycle(nw)
        assert bit==0 and S==20
        xmin=ceil_div((1<<20)*N0-C,MOD)
        b.append((u,C,xmin))
assert len(b)==15947
bmin=min(x for _,_,x in b); bmax=max(x for _,_,x in b)
assert bmax-bmin==21

# Retain V33 only for the graph-side zero-slack classification.
assert len(v33.recurrent)==66
assert all(len(cc)==19 and len(ee)==19 and
           sum(e[2] for e in ee)==12 and
           sum(e[4] for e in ee)==0 and
           {e[3] for e in ee}=={"I"}
           for cc,ee in v33.recurrent)
g=Fraction(3**12,2**19)
assert g>1

# Same chamber state, opposite guarded returns.
Ae,Be=v34.Ae,v34.Be
Ac,Bc=v34.Ac,v34.Bc
cth=ceil_frac((Fraction(N0)-Bc)/Ac)
assert cth==86_371_586_335_064_384_399
me=least_ge(v34.eg,v34.emod,N0)
mc=least_ge(v34.cg,v34.cmod,N0)
ye=Ae*me+Be; yc=Ac*mc+Bc
assert ye.denominator==yc.denominator==1
assert ye>N0 and yc<N0

# Tail-zero proxy falsifier from the exact V26 natural witness.
T26=685408643048678703309842726690675779814441196540003599299583389096836936979689649632335566636234945811040497388265518
NC=3_782_158_995_862_761_504_768
n26=N0+NC*T26
assert n26.bit_length()==460
def T(x): return (3*x+1)//2 if x&1 else x//2
y=n26; first=None
for depth in range(700):
    if 0<y<n26: first=("D",depth); break
    if y%8==5 and y<=4*n26: first=("S",depth); break
    if y%3==2:
        p=(2*y-1)//3
        if 0<p<n26:
            assert T(p)==y
            first=("M1",depth); break
    y=T(y)
assert first==("M1",518)

# Source-headroom alone still does not close V35's finite expanding shadows.
R=v35.R_ONE; M=v35.B
shadow=[]; first_above=None
for reps in range(1,v35.CHECK_R+1):
    start=v35.owner(R); cur=start; mink=None; minowner=start
    for _ in range(reps):
        for e in v34.expanding:
            a,c=v34.owner_map(e[0],e[1],e[2])
            z=a*cur+c
            assert z.denominator==1
            cur=z.numerator; minowner=min(minowner,cur)
            if e[3]=="K": mink=cur if mink is None else min(mink,cur)
    above=start>N0
    if above and first_above is None: first_above=reps
    if above:
        assert minowner>=N0 and mink is not None and mink>=N0
    shadow.append({
        "repeats":reps,
        "start_owner":str(start),
        "above_floor":above,
        "min_owner":str(minowner),
        "min_K_target":str(mink),
        "passes_source_gate":bool(above and mink>=N0),
    })
    R,M=v35.next_shadow_residue(R,M)
assert first_above==5
assert all(r["passes_source_gate"] for r in shadow if r["above_floor"])

byd={}
for d in range(1,6):
    rows=[(E,x) for dd,E,x in lower if dd==d]
    byd[str(d)]={
        "count":len(rows),
        "E_values":sorted({E for E,_ in rows}),
        "xmin":min(x for _,x in rows),
        "xmax":max(x for _,x in rows),
    }

result={
 "schema":"COLLATZ_CRYSTAL_SOURCE_HEADROOM_GATE_V36B",
 "parent":"collatz-crystal-expanding-shadow-v35@ed2d430005a4db5abd0939050f0438e82733b385",
 "chess_transfer":"promote the engine-native regime coordinate when intervention consequence changes sign; do not average regimes",
 "K_gate":{
   "law":"lower-cost K: 2^d*p=x+E, so p<n iff x+E<2^d*n",
   "lower_count":len(lower),"same_count":len(same),"by_drop":byd,
   "same_xmin":min(x for _,x in same),"same_xmax":max(x for _,x in same),
 },
 "B_gate":{
   "count":len(b),"cost":20,"xmin":bmin,"xmax":bmax,
   "width":bmax-bmin,
   "ratio_num":bmin,"ratio_den":N0,
 },
 "zero_slack":{
   "recurrent_components":66,
   "shape":"pure-I 19-step / 12-odd / D=0",
   "multiplier_num":g.numerator,"multiplier_den":g.denominator,
   "gap":g.numerator-g.denominator,
 },
 "same_state_regime":{
   "base":v34.BASE,
   "contracting_no_exit_threshold":cth,
   "exp_guard_start":me,"exp_after":ye.numerator,
   "con_guard_start":mc,"con_after":yc.numerator,
 },
 "tail_zero_falsifier":{"source_bits":460,"first_simple_exit_kind":first[0],"first_simple_exit_depth":first[1]},
 "v35_falsifier":{"checked":v35.CHECK_R,"first_above":first_above,"all_above_pass":True,
                   "first_rows":shadow[:8],"last":shadow[-1]},
 "scientific_verdict":"SOURCE_HEADROOM_CONSEQUENTIAL; TAIL_ZERO_REJECTED; HEADROOM_GATE_ALONE_REJECTED",
 "next_residual":{
   "name":"HEADROOM_GATED_APERIODIC_RETURN_LANGUAGE",
   "statement":"Compile zero-slack 19/12 identity recurrence plus the first source-headroom-admissible B/lower-K reset, preserving the fixed-source carry guard. Exclude a recurrent natural-compatible guarded macro SCC.",
 },
 "universal_status":"UNKNOWN","global_collatz":"UNKNOWN",
}
result["certificate_sha256"]=hashlib.sha256(json.dumps(result,sort_keys=True,separators=(",",":")).encode()).hexdigest()
print(json.dumps(result,indent=2,sort_keys=True))
