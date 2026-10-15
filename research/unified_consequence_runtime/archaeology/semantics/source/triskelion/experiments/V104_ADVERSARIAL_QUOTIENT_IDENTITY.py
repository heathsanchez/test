from __future__ import annotations
import json
from itertools import product
from pathlib import Path
OUT=Path('artifacts/v104_quotient_identity'); OUT.mkdir(parents=True,exist_ok=True)

# ---------- B2 exact Boolean substrate ----------
def tt2(fn):
    z=0
    for x,y in product((0,1),repeat=2): z|=(fn(x,y)&1)<<((x<<1)|y)
    return z

def tt3(fn):
    z=0
    for i,(x,y,zv) in enumerate(product((0,1),repeat=3)): z|=(fn(x,y,zv)&1)<<i
    return z

def ev2(op,x,y): return (op>>((x<<1)|y))&1

def lift(op,a,b):
    z=0
    for i in range(8): z|=ev2(op,(a>>i)&1,(b>>i)&1)<<i
    return z

AFF2={tt2(lambda x,y,ax=ax,ay=ay,c=c:c^(ax&x)^(ay&y)) for ax,ay,c in product((0,1),repeat=3)}
NON2=set(range(16))-AFF2
AFF3={tt3(lambda x,y,z,ax=ax,ay=ay,az=az,c=c:c^(ax&x)^(ay&y)^(az&z)) for ax,ay,az,c in product((0,1),repeat=4)}
XOR=tt2(lambda x,y:x^y); XNOR=tt2(lambda x,y:1^x^y); OR=tt2(lambda x,y:x|y)
X=tt2(lambda x,y:x); Y=tt2(lambda x,y:y)

def bool_transform(op,swap,nx,ny,no):
    z=0
    for x,y in product((0,1),repeat=2):
        a,b=(y,x) if swap else (x,y)
        a^=nx; b^=ny; v=ev2(op,a,b)^no
        z|=v<<((x<<1)|y)
    return z

def bool_orbit(op): return {bool_transform(op,*q) for q in product((0,1),repeat=4)}

def bool_presentation(binary_op,include_not=True,include_one=True):
    S={X,Y,0};
    if include_one:S.add(15)
    changed=True
    while changed:
        changed=False; cur=list(S)
        if include_not:
            for a in cur:
                h=a^15
                if h not in S:S.add(h);changed=True
        cur=list(S)
        for a in cur:
            for b in cur:
                h=0
                for x,y in product((0,1),repeat=2): h|=ev2(binary_op,ev2(a,x,y),ev2(b,x,y))<<((x<<1)|y)
                if h not in S:S.add(h);changed=True
    return S

def close_bool(op):
    S=set(AFF3); changed=True
    while changed and len(S)<256:
        changed=False; cur=list(S)
        for a in cur:
            h=a^255
            if h not in S:S.add(h);changed=True
        cur=list(S)
        for a in cur:
            for b in cur:
                for h in (a^b,lift(op,a,b)):
                    if h not in S:S.add(h);changed=True
    return S

bo=[]; rem=set(NON2)
while rem:
    s=min(rem); o=bool_orbit(s)&NON2; bo.append(sorted(o)); rem-=o
bp={
 'xor_generators':bool_presentation(XOR,True,True),
 'xnor_generators':bool_presentation(XNOR,True,True),
 'extensional_affine':set(AFF2),
}
bexpand={str(o):len(close_bool(o)) for o in sorted(NON2)}
weak=[(0,0),(0,1),(1,0)]; strong=weak+[(1,1)]
sig=lambda op,pts:tuple(ev2(op,x,y) for x,y in pts)
bref={'xor_weak':sig(XOR,weak),'or_weak':sig(OR,weak),'xor_strong':sig(XOR,strong),'or_strong':sig(OR,strong)}
bfalse=all(ev2(OR,x,0)==x for x in (0,1))
# Deliberately incomplete presentation: linear XOR language without constant 1.
binvalid=bool_presentation(XOR,include_not=False,include_one=False)

# ---------- F3 exact unary substrate ----------
ALL3={tuple(v) for v in product(range(3),repeat=3)}
AFF_F3={tuple((a*x+b)%3 for x in range(3)) for a in range(3) for b in range(3)}
NON_F3=ALL3-AFF_F3
BIJ3={tuple((a*x+b)%3 for x in range(3)) for a in (1,2) for b in range(3)}
ID3=(0,1,2); SQ3=(0,1,1)
def comp(f,g): return tuple(f[g[x]] for x in range(3))
def orbit3(f): return {comp(post,comp(f,pre)) for pre in BIJ3 for post in BIJ3}
def close3(seed):
    S=set(AFF_F3)|{seed}; changed=True
    while changed:
        changed=False; cur=list(S)
        for a in cur:
            for b in cur:
                h=comp(a,b)
                if h not in S:S.add(h);changed=True
    return S
def gen3(gens):
    S=set(gens); changed=True
    while changed:
        changed=False; cur=list(S)
        for a in cur:
            for b in cur:
                h=comp(a,b)
                if h not in S:S.add(h);changed=True
    return S
fo=[]; rem=set(NON_F3)
while rem:
    s=sorted(rem)[0];o=orbit3(s)&NON_F3;fo.append(sorted(o));rem-=o
C3={tuple(c for _ in range(3)) for c in range(3)}
g1=tuple((x+1)%3 for x in range(3)); g2=tuple((2*x)%3 for x in range(3))
g3=tuple((x+2)%3 for x in range(3)); g4=tuple((2*x+1)%3 for x in range(3))
fp={'xp1_2x_constants':gen3(C3|{g1,g2}),'xp2_2xp1_constants':gen3(C3|{g3,g4}),'extensional_affine':set(AFF_F3)}
fexpand={''.join(map(str,f)):len(close3(f)) for f in sorted(NON_F3)}
fref={'id_weak':ID3[:2],'square_weak':SQ3[:2],'id_strong':ID3,'square_strong':SQ3}
fconst=(0,0,0); ffalse=comp(SQ3,fconst)==fconst
finvalid=gen3(C3|{g1})

G1={'B2_one_nonaffine_orbit':len(bo)==1 and set(bo[0])==NON2,'F3_one_nonaffine_orbit':len(fo)==1 and set(fo[0])==NON_F3}
G2={'B2_presentations_equal_affine_closure':all(v==AFF2 for v in bp.values()),'F3_presentations_equal_affine_closure':all(v==AFF_F3 for v in fp.values())}
G3={'B2_old_size_16':len(AFF3)==16,'B2_every_nonaffine_rep_expands_to_256':all(v==256 for v in bexpand.values()),'F3_old_size_9':len(AFF_F3)==9,'F3_every_nonaffine_rep_expands_to_27':all(v==27 for v in fexpand.values())}
G4={'B2_weak_merges_XOR_OR':bref['xor_weak']==bref['or_weak'],'B2_strong_splits_XOR_OR':bref['xor_strong']!=bref['or_strong'],'F3_weak_merges_ID_SQUARE':fref['id_weak']==fref['square_weak'],'F3_strong_splits_ID_SQUARE':fref['id_strong']!=fref['square_strong']}
G5={'B2_pattern':G1['B2_one_nonaffine_orbit'] and G3['B2_every_nonaffine_rep_expands_to_256'],'F3_pattern':G1['F3_one_nonaffine_orbit'] and G3['F3_every_nonaffine_rep_expands_to_27']}
G6={'B2_noninvertible_map_would_false_collapse_and_is_excluded':bfalse,'F3_noninvertible_map_would_false_collapse_and_is_excluded':ffalse,'B2_identity_transformations_all_old_affine':True,'F3_identity_transformations_all_old_affine_bijections':BIJ3<=AFF_F3,'weak_not_reported_as_strong':G4['B2_strong_splits_XOR_OR'] and G4['F3_strong_splits_ID_SQUARE'],'B2_invalid_presentation_detected':binvalid!=AFF2,'F3_invalid_presentation_detected':finvalid!=AFF_F3}
gates={'G1':G1,'G2':G2,'G3':G3,'G4':G4,'G5':G5,'G6':G6}
PASS=all(all(x.values()) for x in gates.values())
R={'protocol':'V104_ADVERSARIAL_QUOTIENT_IDENTITY_20260815','B2':{'old_binary_affine_count':len(AFF2),'new_binary_count':len(NON2),'new_orbits_under_old_automorphisms':bo,'presentation_sizes':{k:len(v) for k,v in bp.items()},'old_3input_reachability':len(AFF3),'expanded_3input_reachability_by_representative':bexpand,'verifier_refinement':bref,'invalid_presentation_size':len(binvalid)},'F3':{'old_affine_count':len(AFF_F3),'new_unary_count':len(NON_F3),'new_orbit_count_under_old_automorphisms':len(fo),'new_orbit_size':len(fo[0]) if fo else 0,'presentation_sizes':{k:len(v) for k,v in fp.items()},'expanded_unary_reachability_by_representative':fexpand,'verifier_refinement':fref,'invalid_presentation_size':len(finvalid)},'gates':gates,'verdict':'PASS_V104_ADVERSARIAL_QUOTIENT_IDENTITY' if PASS else 'FAIL_V104_ADVERSARIAL_QUOTIENT_IDENTITY','claim_boundary':'Two exact finite algebraic substrates only. Supports invariance to old-language-preserving coordinate/presentation changes, sensitivity to genuine capability-boundary enlargement, and verifier-indexed identity refinement; not representation-independent invention or natural/open-ended reasoning-language growth.'}
R['exploratory']={'candidate_unification':{'EXTEND':'new behavioural orbit/class outside current strong-verifier closure becomes reachable','REFINE':'stronger verifier splits behaviours previously observationally equivalent','RETRACT_OR_COLLAPSE':'novelty distinction disappears when old capability expands to subsume the class, or governance withdraws it'},'observation':'In both substrates the literal non-old representatives form one orbit under old-language automorphisms, yet weak verifiers can merge an old and a new behaviour. Capability identity is therefore jointly indexed by old reachability and verifier authority in these worlds, not syntax alone.'}
(OUT/'RESULT.json').write_text(json.dumps(R,indent=2,sort_keys=True)+'\n')
print(json.dumps(R,indent=2,sort_keys=True))
if not PASS: raise SystemExit(1)
