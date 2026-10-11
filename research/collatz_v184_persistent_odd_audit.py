"""V184 — protected least-bad FUTURE yields high odd bias at every clock.

This audit independently checks source-exact arithmetic:
  every TRUE +1 shortcut source trajectory entirely >=8 until time k
  obeys 2^k*8^a*T^k(n) <= n*25^a;
  if it also never falls below initial n, then 2^k*8^a<=25^a
  and oddCount(n,5r)>=3r+1 for every tested positive r.

Lean proves the ALL-n ALL-k conditional statements independent of
numerical audits. A hypothetical least bad n is subject to them at
EVERY positive r, without the source-height guard in V181.

Protected countercontrols:
  * Mersenne numbers 2^K-1 match extremely long high-odd prefixes
  * the G5 nonterminal 187-cycle has 17 odd steps in 27 and obeys
    the same 3/5 necessary restriction FOREVER; such a restriction
    does not itself prove convergence even for another exact system
  * the G5 map fails the SOURCE-specific +1 odd-step inequality at 9
  * original n=27 eventually violates the high-odd restriction only
    after leaving the protected no-descent future.

Global Collatz UNKNOWN, NO QED.
"""
from __future__ import annotations
from math import comb
from pathlib import Path
import json


def T(n:int,c:int=1)->int:
    assert n>0 and c>0 and c%2==1
    return n//2 if n%2==0 else (3*n+c)//2


def check_orbit_protection(n:int,H:int)->tuple[int,int,int,bool,bool,int|None]:
    source=n
    current=n
    odd=0
    no_ever_below_eight=True
    no_ever_below_initial=True
    checked=0
    first_failure=None
    for k in range(H+1):
        if current<8:
            no_ever_below_eight=False
        if current<source:
            no_ever_below_initial=False
        if no_ever_below_eight:
            assert (1<<k)*(8**odd)*current <=source*(25**odd),(source,k,odd,current)
            checked+=1
        if no_ever_below_initial and source>=8:
            assert (1<<k)*(8**odd) <=25**odd,(source,k,odd)
            if k>0 and k%5==0:
                assert odd>=3*(k//5)+1,(source,k,odd)
        elif k>0 and k%5==0 and first_failure is None and odd<3*(k//5)+1:
            first_failure=k
        if k<H:
            odd+=current%2
            current=T(current)
    return source,checked,odd,no_ever_below_eight,no_ever_below_initial,first_failure


def g5_cycle_control()->dict:
    x=187
    states=[]
    od=[0]
    for t in range(27):
        assert x>=187
        states.append(x)
        od.append(od[-1]+x%2)
        x=T(x,5)
    assert x==187 and len(set(states))==27
    assert od[-1]==17
    assert min(states)==187
    # r->r+27 increments 5r clocks by 135 = 5 complete cycles,
    # adding 5*17=85 odd clocks, while the threshold rises 3*27=81.
    # Checking r=1..27 proves the inequality for EVERY positive r.
    def odd_for_k(k:int)->int:
        q,t=divmod(k,27)
        return 17*q+od[t]
    rows=[]
    for r in range(1,28):
        a=odd_for_k(5*r)
        assert a>=3*r+1,(r,a)
        rows.append({"r":r,"k":5*r,"odd":a,"excess":a-(3*r+1)})
    assert min(q["excess"] for q in rows)>=0
    assert all(odd_for_k(5*(r+27)) == odd_for_k(5*r)+85 for r in range(1,28))
    assert all(3*(r+27)+1==(3*r+1)+81 for r in range(1,28))
    # This is NOT the genuine Collatz map, since odd increment=5.
    assert T(9,5)==16 and 16*T(9,5)>25*9
    assert 16*T(9,1)<=25*9
    return {
       "synthetic_map":"T5(even)=n/2; T5(odd)=(3n+5)/2",
       "real_nonterminal_cycle_start":187,
       "cycle_length":27,
       "cycle_minimum_source":187,
       "cycle_odd_count":17,
       "cycle_odd_density_exact":"17/27",
       "five_block_inequality_all_positive_r_proved_by_periodic_reduction":True,
       "period_reduction_modulus_r":27,
       "tested_exact_period_residue_cases":len(rows),
       "per_period_odd_increment":85,
       "per_period_needed_odd_increment":81,
       "universal_true_plus_one_step_bound_fails_for_synthetic_at_9":True,
       "not_a_true_Collatz_counterexample":True,
    }


def parity_word_joint_prefixes(R:int)->list[dict]:
    # Count all binary words of k=5r whose block-boundary odd
    # counts satisfy a_(5t)>=3t+1 for every 1<=t<=r.
    # All binary parity words are uniquely realized modulo 2^k
    # for the actual shortcut T; this combinatorial count is NOT
    # a proof that any particular natural source fails infinitely.
    curr={0:1}
    out=[]
    for r in range(1,R+1):
        nxt={}
        for odd_before,multiplicity in curr.items():
            for j in range(6):
                odd=odd_before+j
                if odd<3*r+1:continue
                nxt[odd]=nxt.get(odd,0)+multiplicity*comb(5,j)
        curr=nxt
        k=5*r
        total=sum(curr.values())
        final_tail=sum(comb(k,j) for j in range(3*r+1,k+1))
        bound_ratio_numer=3125**r
        bound_ratio_denom=3456**r
        assert 0<total<=final_tail
        assert total*bound_ratio_denom<=bound_ratio_numer*(1<<k)
        out.append({"r":r,"clock_k":k,
                    "allowed_full_prefix_words":total,
                    "all_parity_words":1<<k,
                    "necessary_final_prefix_only_words":final_tail,
                    "nonempty_rare_language":True,
                    "count_no_finite_k_is_zero":True})
    return out


def main()->None:
    N=120000;H=80
    source_clock_tests=0
    failed_high_after_source_descent=[]
    for n in range(8,N+1):
        _,checked,_,_,_,ff=check_orbit_protection(n,H)
        source_clock_tests+=checked
        if ff is not None and len(failed_high_after_source_descent)<6:
            failed_high_after_source_descent.append({"source":n,"first_failed_five_prefix":ff})
    m=[]
    for K in (8,16,32,64,96,128):
        n=(1<<K)-1
        x=n
        odds=0
        for t in range(K):
            assert x&1
            odds+=1
            x=T(x)
        assert odds==K and x==3**K-1
        m.append({"mersenne_exponent_K":K,
                  "positive_source_bits":K,
                  "initial_odd_steps":K,
                  "source_positive":True,
                  "end_after_K":str(x)})
    rows=parity_word_joint_prefixes(16)
    g5=g5_cycle_control()
    assert any(z["source"]==27 for z in failed_high_after_source_descent)
    # A TRUE convergent example can meet EVERY finite initial
    # requirement yet eventually fall below its initial source.
    cur=27;odd=0;first_bad=None
    for k in range(80):
        if k and k%5==0 and odd<3*(k//5)+1 and first_bad is None:
            first_bad=k
        odd+=cur%2;cur=T(cur)
    assert first_bad==70
    payload={
        "schema":"COLLATZ_V184_PROTECTED_FUTURE_ALL_PREFIX_ODD_BARRIER",
        "true_T_even":"n/2",
        "true_T_odd":"(3n+1)/2",
        "positive_source_test_cutoff":N,
        "max_source_test_clock":H,
        "number_of_source_clock_product_inequalities_replayed":source_clock_tests,
        "true_odd_8_barrier_multiplier":"16*T(x)<=25*x, all odd x>=8",
        "all_clock_product_inequality_formally_requested":True,
        "least_bad_restricted_five_step_all_prefix_theorem_formally_requested":True,
        "candidate_parity_word_joint_prefix_language":rows,
        "Mersenne_finite_prefix_controls":m,
        "G5_real_dual_cycle_negative_control":g5,
        "27_first_failed_five_prefix_after_eventual_descent":first_bad,
        "not_a_global_termination_or_density_proof":True,
        "parity_word_rarity_does_not_eliminate_single_least_bad":True,
        "global_collatz":"UNKNOWN","qed":False
    }
    Path("evidence").mkdir(exist_ok=True)
    Path("evidence/v184-odd-prefix.json").write_text(
        json.dumps(payload,indent=2,sort_keys=True)+"\n")
    print(json.dumps({
        "schema":payload["schema"],
        "sources_replayed":N-7,
        "clock_inequalities":source_clock_tests,
        "joint_parity_prefix_rows":len(rows),
        "G5_unbounded_high_odd_countercontrol":g5["five_block_inequality_all_positive_r_proved_by_periodic_reduction"],
        "global_collatz":payload["global_collatz"]
    },sort_keys=True))


if __name__=="__main__":
    main()
