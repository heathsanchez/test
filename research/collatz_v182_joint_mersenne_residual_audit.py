"""V182: a certified INFINITE arithmetic family survives BOTH V178
205-rule source-index reductions AND every applicable V181 high-odd
least-counterexample necessary condition.

Let n_m=2^(10m+1)-1 for m>=2.

The original n_m has exactly the first (10m+1) true shortcut
transitions odd. Thus for every positive q<=m, n_m>=2^(10q)
and oddCount(n_m,5q)=5q>=3q+1.

The V178 selected 205 rules have strides L dividing
M=2^12*3^6=2,985,984. The positive sources n_m have a
residue modulo M periodic in m with period 243:
  n_m=-1 (mod 2^12), because 10m+1>=21;
  2^2430=1 (mod 3^6), because 2430=5*486 and
    2^486=1 (mod 3^6).
CRT yields n_(m+243)=n_m (mod M).
Exactly 153 of the 243 m-classes are excluded by NONE
of the selected rules. Explicit infinite subfamily:
  m = 2 + 243*t, t>=0;
  n_m mod M = 2^21-1=2,097,151.

These are GENUINE POSITIVE INTEGER SOURCES, not nonconvergent
or even candidates known to be bad. Example n_2=2,097,151
is directly replayed to terminal2 in 193 clocks.
The result is an exact INSUFFICIENCY/SEPARATOR for the two
finite/parametric NECESSARY source filters, not a Collatz QED.

The Mersenne all-odd / applicable-height theorem is separately
being checked in Lean V182. The 205-rule bank was source-pinned
kernel-qualified in V178, but the all-205 residue population
certificate and CRT check here are exact arithmetic executable
evidence plus elementary number theory, not a separately
kernel-compiled 205-way residue mask theorem.
"""
from __future__ import annotations
import json
from math import gcd
from pathlib import Path
from hashlib import sha256


def T(n:int)->int:
    assert n>0
    return n//2 if n%2==0 else (3*n+1)//2


def first_terminal(n:int,cap:int=1000)->tuple[int,int]:
    for t in range(cap+1):
        if n in (1,2):
            return t,n
        n=T(n)
    raise AssertionError("finite_trajectory_cap_exceeded")


def mres(m:int,M:int)->int:
    assert m>=2
    return (pow(2,10*m+1,M)-1)%M


def main()->None:
    path=Path("research/collatz_v178_compact_bank.json")
    bank=json.loads(path.read_text())
    M=(1<<12)*(3**6)
    assert bank["M"]==M and len(bank["selected"])==205
    rules=bank["selected"]
    assert all(M%r[0]==0 for r in rules)
    assert all(r[2]<=bank["N"] for r in rules)
    assert gcd(1<<12,3**6)==1
    assert pow(2,486,3**6)==1
    assert pow(2,2430,3**6)==1
    assert 2430==5*486
    assert pow(2,243,3**6)!=1
    assert (1<<21)-1 <M

    def rule_hit(rem:int)->bool:
        return any(rem%r[0] == r[1] for r in rules)

    survivors=[]
    excluded=[]
    for m in range(2,245):
        # 243 consecutive m classes, each represented exactly once.
        assert mres(m+243,M)==mres(m,M)
        assert mres(m,M)%(1<<12)==(1<<12)-1
        assert mres(m,M)%(3**6)==(pow(2,10*m+1,3**6)-1)%(3**6)
        rem=mres(m,M)
        (excluded if rule_hit(rem) else survivors).append(
            {"representative_m":m,"source_residue_mod_M":rem})
    assert len(survivors)+len(excluded)==243
    assert len(survivors)==153 and len(excluded)==90
    assert survivors[0]=={
       "representative_m":2,"source_residue_mod_M":(1<<21)-1
    }
    r0=2097151
    assert not rule_hit(r0)
    assert all(r0%r[0]!=r[1] for r in rules)

    # Infinite subfamily via periodic congruence for arbitrary t,
    # WITHOUT computing a huge 2^(10m+1) as a Python integer.
    periodic_t=(0,1,2,3,4,7,11,53,1000,1000000)
    for t in periodic_t:
        m=2+243*t
        assert mres(m,M)==r0
        assert not rule_hit(mres(m,M))

    # Protect the distinction 'irreducible by this bank' ≠
    # 'divergent'. The smallest represented source actually reaches 2.
    n2=(1<<21)-1
    assert first_terminal(n2,500)==(193,2)

    odd_prefix_checks=[]
    for m in (2,3,5,8,16,32,64,128):
        K=10*m+1
        n=(1<<K)-1
        assert n>=1<<(10*m)
        for q in sorted({1,max(1,m//2),m}):
            assert 1<=q<=m
            clock=5*q
            x=n
            for j in range(clock):
                assert x%2==1,(m,q,j)
                x=T(x)
            assert x == 3**clock*(1<<(K-clock))-1
            assert clock>=3*q+1
            assert n>=1<<(10*q)
        odd_prefix_checks.append({
            "m":m,"bit_depth":K,
            "applicable_scales_checked":sorted({1,max(1,m//2),m}),
            "all_prefix_odd_steps_checked":True
        })

    # The irreducible family n_(2+243t) has distinct unbounded
    # positive values, but is NOT a Collatz counterexample.
    output={
        "schema":"COLLATZ_V182_JOINT_RULE_BANK_AND_HIGH_ODD_MERSENNE_RESIDUAL",
        "v178_rule_bank_sha256":sha256(path.read_bytes()).hexdigest(),
        "rule_count_kernel_qualified_in_upstream_v178":len(rules),
        "common_residue_period_M":M,
        "source_m_exponent_10m_plus_one":"10*m+1",
        "m_period":243,
        "power_mod_729_period_486":True,
        "m_period_exponent_increment":2430,
        "m_classes_with_no_v178_rule":len(survivors),
        "m_classes_with_any_v178_rule":len(excluded),
        "all_m_classes":[{"m":a["representative_m"],
                          "residue":a["source_residue_mod_M"],
                          "bank_irreducible":a in survivors}
                          for a in survivors+excluded],
        "infinite_joint_survivor_m":"m=2+243*t, t>=0",
        "infinite_joint_survivor_n":"n_m=2^(10*m+1)-1",
        "joint_survivor_source_residue_mod_M":r0,
        "exact_all_205_rules_exclude_no_joint_family_member":True,
        "all_applicable_v181_high_odd_barriers_passed_math":True,
        "odd_prefix_sample_replays":odd_prefix_checks,
        "least_example_m":2,
        "least_example_source":n2,
        "least_example_direct_terminal_clock":193,
        "least_example_actual_terminal_endpoint":2,
        "integer_rule_residue_periodicity_math_not_lean_formalized":True,
        "not_a_nonconvergence_result":True,
        "unbounded_candidate_family_still_may_converge":True,
        "global_collatz":"UNKNOWN","qed":False
    }
    Path("evidence").mkdir(exist_ok=True)
    Path("evidence/v182-joint-residual.json").write_text(
        json.dumps(output,indent=2,sort_keys=True)+"\n")
    print(json.dumps({
        "schema":output["schema"],
        "number_of_m_period_classes":243,
        "irreducible_m_period_classes":len(survivors),
        "explicit_irreducible_m_class":"2 mod243",
        "example_first_terminal_clock":193,
        "global_collatz":"UNKNOWN"
    },sort_keys=True))


if __name__=="__main__":
    main()
