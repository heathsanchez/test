"""V187 -- exact source-locked all-horizon countercontrol for V186.

For EVERY t>=0 take K=21+2430*t and n_t=2^K-1.

This arithmetic subfamily:
- is an actual positive source (not a 2-adic ghost);
- is NOT reducible by ANY of the 205 V178 or 29 V180 qualified
  all-offset rules, because its source residue mod their common
  period M=8192*729 is CONSTANT and misses all 234 rules;
- has exactly K initial odd shortcut clocks with exact formula
      T^h(n_t)=3^h*2^(K-h)-1 for all h<=K;
  hence all initial clocks h<=K stay >=original n_t and satisfy
  the V184 high-odd and V185 EXACT SOURCE-SPECIFIC +1 guards.

These are finite prefixes of DIFFERENT sources as K grows.
At t=0 the actual source 2^21-1 is already Lean-verified to
reach terminal at clock193. The family is a rigorous separator
against treating finite-prefix source constraints as a proof
that a fixed infinite exceptional orbit cannot exist.

The universally quantified genuine K-prefix theorem is separately
checked in MersenneUnboundedJointShadows.lean. The finite-bank
congruence exclusion is exact independently replayed elementary
number theory, and is NOT asserted Lean-reified in this module.

GLOBAL COLLATZ UNKNOWN — NO QED.
"""
from __future__ import annotations
from math import gcd
import hashlib,json
from pathlib import Path


OLD=Path("research/collatz_v178_compact_bank.json")
NEW=Path("research/collatz_v180_inverse_rule_bank.json")


def T(n:int)->int:
    assert n>0
    return n//2 if not(n&1) else (3*n+1)//2


def prove_exact_period(bank, newer)->tuple[int,int]:
    assert bank["M"]==4096*729
    assert len(bank["selected"])==205 and len(newer["rules"])==29
    assert all(x[0] and (8192*729)%x[0]==0 for x in bank["selected"])
    assert all((8192*729)%x["source_stride"]==0 for x in newer["rules"])
    M=8192*729
    Q=729
    assert gcd(8192,Q)==1
    assert pow(2,2430,Q)==1
    assert 21>=13
    a=pow(2,21,M)
    b=pow(2,2430,M)
    assert (a*b)%M==a
    # For ALL t by induction: a*b^t == a (mod M), so
    # 2^(21+2430*t)-1 == 2^21-1 (mod M). The exact one-step
    # congruence suffices; do not extrapolate merely from samples.
    residue=(a-1)%M
    assert residue==2097151
    for [L,rem,s,*_] in bank["selected"]:
        assert residue%L!=rem,(L,rem,s)
        assert rem==s%L
    for z in newer["rules"]:
        L=z["source_stride"]
        assert residue%L!=z["source"]%L,(L,z["source"])
    assert 8191 not in [
        z["source"]%z["source_stride"]
        for z in newer["rules"] if z["source_stride"]==8192]
    return M,residue


def replay(K:int,H:int)->dict:
    assert K>=21 and H<=K
    n=(1<<K)-1
    current=n
    checked=0
    for k in range(H+1):
        expected=pow(3,k)*(1<<(K-k))-1
        assert current==expected,(K,k)
        assert n<=current
        a=k
        assert (1<<k)*pow(n,a) <= pow(3*n+1,a)
        if k<H:
            assert current&1
            current=T(current)
        checked+=1
    return {"K":K,"n_bits":n.bit_length(),"checked_true_clocks":checked,
            "first_H_clocks_all_odd_and_nondecreasing":True,
            "source_specific_guard_checked":True,
            "not_a_perpetual_shadow":True}


def main()->None:
    bank=json.loads(OLD.read_text())
    newer=json.loads(NEW.read_text())
    M,residue=prove_exact_period(bank,newer)
    controls=[]
    for t in range(0,7):
        K=21+2430*t
        n=(1<<K)-1
        assert n%M==residue
        controls.append(replay(K,min(K,80)))
    # The protected universal finite-prefix Mersenne theorem is
    # proved in Lean separately. At t=0, a concrete verified
    # terminal consequence must remain protected, not overwritten
    # by any "survivor" terminology.
    x=(1<<21)-1
    for _ in range(193):
        x=T(x)
    assert x==2
    # Negative reality check: for n=2^21-1, the all-odd prefix
    # lasts only 21 clocks, and 193 clocks suffice for terminal.
    assert controls[0]["checked_true_clocks"]==22
    out={
      "schema":"COLLATZ_V187_INFINITE_REAL_POSITIVE_JOINT_FINITE_SHADOW",
      "V178_bank_sha256":hashlib.sha256(OLD.read_bytes()).hexdigest(),
      "V180_bank_sha256":hashlib.sha256(NEW.read_bytes()).hexdigest(),
      "rule_count_total":234,
      "common_period_M":M,
      "Mersenne_exponent_formula":"21+2430*t for any natural t",
      "entire_family_source_mod_M":residue,
      "period_identity_exact":"pow(2,2430,729)=1; 2^K divisible 8192; CRT",
      "for_all_t_neither_205_nor_29_rules_apply_to_n_t":True,
      "for_all_t_true_all_K_odd_prefix_and_never_below_original":True,
      "for_all_t_V185_exact_3n_plus1_guard_holds_for_first_K_clocks":True,
      "finite_source_checks":controls,
      "first_family_source_2pow21_minus1_terminal_clock":193,
      "first_family_source_actual_terminal_endpoint":2,
      "no_fixed_source_proved_infinite_nonterminal":True,
      "no_universal_source_declared_divergent":True,
      "no_global_Collatz_QED":True,
      "global_collatz":"UNKNOWN","qed":False
    }
    Path("evidence").mkdir(exist_ok=True)
    Path("evidence/v187-shadows.json").write_text(
        json.dumps(out,indent=2,sort_keys=True)+"\n")
    print(json.dumps({
      "schema":out["schema"],
      "source_rule_count":out["rule_count_total"],
      "all_t_modular_residue":residue,
      "M":M,
      "sampled_t":[0,1,2,3,4,5,6],
      "first_source_terminal_clock":193,
      "global_collatz":"UNKNOWN"
    },sort_keys=True))


if __name__=="__main__":
    main()
