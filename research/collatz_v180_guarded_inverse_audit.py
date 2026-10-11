"""V180 guarded inverse source-rule compounding — independent exact audit.

Qualification boundaries:
* Regenerates each of the 29 SOURCE-ATTACHED positive guarded
  odd inverse rules from the 205 V178 original-source proof records.
* Independently recomputes every base equality and odd source clock.
* Checks each new ALL-OFFSET identity at finite adversarial offsets.
  The unbounded family is separately proved by Lean V160/V180.
* Counts the EXACT old/new periodic *positions of a possible least
  positive bad source*, never the natural density of good integers.
* Preserves G7 as a genuinely disjoint-future-class countermodel.

GLOBAL COLLATZ UNKNOWN — NO QED.
"""
from __future__ import annotations
from collections import Counter
from fractions import Fraction
from hashlib import sha256
from pathlib import Path
import json


ROOT=Path("research")
PARENT=ROOT/"collatz_v178_compact_bank.json"
SEEDS=ROOT/"collatz_v180_inverse_rule_bank.json"


def T(n: int, c:int=1)->int:
    assert n>0 and c>0 and c%2==1
    return n//2 if n%2==0 else (3*n+c)//2


def advance(n:int,t:int,c:int=1)->tuple[int,int]:
    odd=0
    for _ in range(t):
        odd+=n%2
        n=T(n,c)
    return n,odd


def qualified_inverse(r:list[int], idx:int)->dict|None:
    L,res,s,p,i,j,a,b,R,*_=r
    assert j>=0 and 0<p<s and res==s%L
    if j!=0:
        return None
    m=1 if L%3==0 else 3
    w0=next((w for w in range(m) if (s+L*w)%3==2),None)
    if w0 is None:
        return None
    previous=s+L*w0
    earlier=p+R*w0
    x=(2*previous-1)//3
    assert 3*x+1==2*previous and x%2==1 and x>0
    stride=2*L*m//3
    companion_stride=R*m
    assert (2*L*m)%3==0
    if stride<=companion_stride:
        return None
    tmin=max(0,(earlier-x)//(stride-companion_stride)+1)
    n=x+stride*tmin
    previous+=L*m*tmin
    earlier+=companion_stride*tmin
    assert 0<earlier<n
    assert advance(n,1)[0]==previous
    assert advance(previous,i)[0]==earlier
    assert stride==2**(i+1)
    assert companion_stride==3**advance(n,i+1)[1]
    return {
        "original_bank_index":idx,"source":n,"prior_source":previous,
        "earlier":earlier,"prior_clock":i,"source_clock":i+1,
        "source_stride":stride,"earlier_stride":companion_stride,
        "original_source":s,"original_earlier":p,
        "original_stride":L,"original_earlier_stride":R,
        "offset_start":w0+m*tmin
    }


def mask_original(rules:list[list[int]],M:int)->bytearray:
    mask=bytearray(M)
    for L,res,*_ in rules:
        assert M%L==0
        mask[res::L]=bytes([1])*((M-1-res)//L+1)
    return mask


def mask_inverse(rules:list[dict],M:int)->bytearray:
    mask=bytearray(M)
    for r in rules:
        L=r["source_stride"]
        res=r["source"]%L
        assert M%L==0
        mask[res::L]=bytes([1])*((M-1-res)//L+1)
    return mask


def same_map_negative_control()->dict:
    assert [T(z,7) for z in (7,14)]==[14,7]
    assert [T(z,7) for z in (5,11,20,10)]==[11,20,10,5]
    assert {7,14}.isdisjoint({5,11,20,10})
    assert advance(255,13,7)[0]!=205
    return {
      "G7_distinct_true_positive_basins":True,
      "V180_plus_one_source_meeting_is_false_under_G7":True,
      "general_odd_predecessor_compounding_not_global_convergence":True
    }


def main()->None:
    original=json.loads(PARENT.read_text())
    declared=json.loads(SEEDS.read_text())
    bank=original["selected"]
    M=original["M"]*2
    assert original["M"]==2985984 and len(bank)==205
    regenerated=[
       entry for idx,r in enumerate(bank)
       if (entry:=qualified_inverse(r,idx)) is not None
    ]
    assert regenerated==declared["rules"]
    assert len(regenerated)==29
    assert all(r["source"]<original["N"] for r in regenerated)
    assert all(r["prior_clock"]+1==r["source_clock"] for r in regenerated)
    replayed=0
    for r in regenerated:
        n,p=r["source"],r["earlier"]
        i=r["source_clock"]
        N,R=r["source_stride"],r["earlier_stride"]
        assert 0<p<n and 0<R<=N
        for w in (0,1,2,7,10_000,1_000_000):
            nn=n+N*w
            pp=p+R*w
            assert 0<pp<nn
            assert advance(nn,i)[0]==pp
            replayed+=1
    assert replayed==174
    baseline=mask_original(bank,M)
    generated=mask_inverse(regenerated,M)
    old_count=sum(baseline)
    generated_count=sum(generated)
    fresh=sum(1 for a,b in zip(baseline,generated) if b and not a)
    both=sum(1 for a,b in zip(baseline,generated) if a and b)
    survivor_by12=Counter(
        idx%12 for idx,(a,b) in enumerate(zip(baseline,generated))
        if not(a or b))
    assert (old_count,fresh,old_count+fresh)==(5830692,9126,5839818)
    assert M-old_count-fresh==132150
    assert dict(survivor_by12)=={3:81003,7:51147}
    assert generated_count==both+fresh
    assert all(M%r["source_stride"]==0 for r in regenerated)
    # Synthetic direct first-successor inverse/canonical-normal-form
    # shortcuts do not prove an all-source exit theorem.
    exact_255=next(z for z in regenerated if z["source"]==255)
    assert (exact_255["prior_source"],exact_255["earlier"],
            exact_255["source_stride"],exact_255["earlier_stride"],
            exact_255["source_clock"])==(383,205,8192,6561,13)
    old=Fraction(old_count,M)
    new=Fraction(old_count+fresh,M)
    assert old==Fraction(2915346,2985984)
    assert new==Fraction(5839818,5971968)
    output={
      "schema":"COLLATZ_V180_GUARDED_INVERSE_NEW_SOURCE_RULES",
      "old_qualified_rules":len(bank),
      "new_source_seed_count":len(regenerated),
      "new_seed_sha256":sha256(SEEDS.read_bytes()).hexdigest(),
      "new_period":M,
      "old_period_coverage":old_count,
      "new_inverse_seed_mask_coverage":generated_count,
      "new_previously_uncovered_least_bad_source_positions":fresh,
      "updated_combined_excluded_least_bad_positions":old_count+fresh,
      "updated_unresolved_least_bad_positions":M-old_count-fresh,
      "original_excluded_fraction":f"{old.numerator}/{old.denominator}",
      "updated_excluded_fraction":f"{new.numerator}/{new.denominator}",
      "source_height_threshold_for_periodic_membership":original["N"],
      "residual_mod12":dict(sorted(survivor_by12.items())),
      "all_174_finite_offset_base_replays_passed":replayed==174,
      "smallest_new_true_mersenne_corridor_seed":exact_255,
      "negative_control":same_map_negative_control(),
      "new_kernel_qualifier_is_separate_from_finite_mask_count":True,
      "excluded_positions_are_NOT_independently_terminal_certified":True,
      "complete_all_source_least_bad_elimination_proved":False,
      "global_collatz":"UNKNOWN","qed":False
    }
    print(json.dumps(output,indent=2,sort_keys=True))


if __name__=="__main__":
    main()
