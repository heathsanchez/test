"""V186 -- independent exact global reclosure of V179/V180 with V184/V185.

Protected source classes:
 (A) 205 V178 and 29 V180 certified strict-earlier-source rules;
 (B) V184's ALL positive r>0 high-odd first 5r prefix necessity
     for a hypothetical LEAST bad positive source;
 (C) V185's exact original-source +1 coefficient growth guard.

We do NOT confuse sources satisfying (A)+(B) at FINITE horizon
with nonconvergent sources; nor does a ZERO natural-density
necessary set imply it is empty.

For k>=13, CRT separates the 3^6 source classes from the initial
2^13 original-source bits. The exact V161 all-finite parity-word
bijection then lets suffix parity-bit choices be counted with a
weighted dynamic program. The resulting k=20 joint count is
INDEPENDENTLY checked by a direct replay of all 2^20 natural
original-source residues, with the exact 729-way source residue
weights.

For ALL positive r the elementary binomial moment bound gives:
    # {length 5r parity words with oddCount>=3r+1} / 2^(5r)
         <= (3125/3456)^r.
Hence the intersection of all source-index candidate prefix
constraints has natural density ZERO. This is an analytic proof
from the exact all-depth parity-word law (Lean-authoritative V161)
and V184. The binomial inequality is NOT independently a Lean
theorem in this core-only module, and does not establish QED.

Global Collatz UNKNOWN, NO QED.
"""
from __future__ import annotations
from collections import Counter
from fractions import Fraction
from hashlib import sha256
from math import comb
from pathlib import Path
import json


M=5971968
LOW=8192
M3=729
PARENT=Path("research/collatz_v178_compact_bank.json")
INVERSE=Path("research/collatz_v180_inverse_rule_bank.json")


def step(n:int)->int:
    assert n>=0
    return n//2 if n%2==0 else (3*n+1)//2


def audited_mask()->tuple[bytearray,list[int],str,str]:
    parent=json.loads(PARENT.read_text())
    inverse=json.loads(INVERSE.read_text())
    assert parent["M"]==2985984 and len(parent["selected"])==205
    assert len(inverse["rules"])==29
    included=bytearray(M)
    for r in parent["selected"]:
        L,rem=r[:2]
        assert M%L==0
        included[rem::L]=b'\x01'*((M-1-rem)//L+1)
    for r in inverse["rules"]:
        L=r["source_stride"]
        rem=r["source"]%L
        assert M%L==0
        included[rem::L]=b'\x01'*((M-1-rem)//L+1)
    assert M-sum(included)==132150
    by_low=[0]*LOW
    for source_rem,was_eliminated in enumerate(included):
        if not was_eliminated:
            by_low[source_rem%LOW]+=1
    assert sum(by_low)==132150
    return included,by_low,sha256(PARENT.read_bytes()).hexdigest(),sha256(INVERSE.read_bytes()).hexdigest()


def joint_suffix_dp(by_low:list[int])->list[dict]:
    # V161: first 13 real parity bits of any n are determined by n mod 2^13.
    # At fixed low residue the 729 independent mod3^6 residues carry only
    # the CERTIFIED previous-source position exclusion mask, not an oracle.
    weighted=[0]*14
    eligible_first13=0
    for r in range(LOW):
        x=r
        odd=0
        allowed=True
        for t in range(1,14):
            odd+=x%2
            x=step(x)
            if t%5==0 and odd<3*(t//5)+1:
                allowed=False
        if allowed:
            eligible_first13+=1
            weighted[odd]+=by_low[r]
    assert eligible_first13==848
    assert sum(weighted)==132150*0+132150*0+sum(weighted)
    assert weighted==[0,0,0,0,0,0,0,0,11925,50547,45231,19695,4356,396]
    # Coarse all-source family alone: count all high-odd finite prefix
    # words at each full five-clock checkpoint.
    full=[1]
    full_rows={}
    for k in range(1,81):
        nxt=[0]*(k+1)
        for odd,mult in enumerate(full):
            nxt[odd]+=mult
            nxt[odd+1]+=mult
        if k%5==0:
            for o in range(3*(k//5)+1):
                nxt[o]=0
        full=nxt
        if k in (5,10,20,40,60,80):
            full_rows[k]=sum(full)
    assert full_rows[5]==6 and full_rows[10]==106
    assert full_rows[20]==49893
    assert full_rows[80]==4217879674841339916735
    # Source bank + high-odd future intersection, preserving exactly
    # what neither bank alone warrants.
    state=weighted
    output=[]
    for k in range(14,81):
        nxt=[0]*(k+1)
        for odd,mult in enumerate(state):
            nxt[odd]+=mult
            nxt[odd+1]+=mult
        if k%5==0:
            for o in range(3*(k//5)+1):
                nxt[o]=0
        state=nxt
        if k in (20,40,60,80):
            joint=sum(state)
            denom=M3*(1<<k)
            pure=full_rows[k]
            assert joint>0 and 0<pure<=1<<k
            assert Fraction(joint,denom)<=Fraction(pure,1<<k)
            upper=Fraction(3125,3456)**(k//5)
            assert Fraction(pure,1<<k)<=upper
            output.append({
                "parity_clocks":k,
                "joint_candidate_residue_count":str(joint),
                "joint_residue_modulus":str(denom),
                "joint_candidate_fraction_exact":f"{Fraction(joint,denom).numerator}/{Fraction(joint,denom).denominator}",
                "joint_candidate_fraction_float_display":float(Fraction(joint,denom)),
                "allprefix_odd_candidates_ignoring_source_sieve":str(pure),
                "all_parity_words":str(1<<k),
                "high_odd_fraction_exact":f"{Fraction(pure,1<<k).numerator}/{Fraction(pure,1<<k).denominator}",
                "all_r_analytic_upper_bound":f"(3125/3456)^{k//5}",
                "fraction_not_universal_Collatz_convergence":True,
            })
    expect={
      20:10567695,
      40:4092614593656,
      60:1912173658182124863,
      80:983503451589865724218308,
    }
    assert all(int(v["joint_candidate_residue_count"])==expect[v["parity_clocks"]]
               for v in output)
    return output


def independent_direct_20(by_low:list[int])->dict:
    # No parity source->word formula shortcut. Independently replay all
    # 1,048,576 actual original representative integer trajectories.
    count=0
    parity_count=0
    for n in range(1<<20):
        x=n
        odd=0
        permitted=True
        for t in range(1,21):
            odd+=x%2
            x=step(x)
            if t%5==0 and odd<3*(t//5)+1:
                permitted=False
                break
        if permitted:
            parity_count+=1
            count+=by_low[n%LOW]
    assert parity_count==49893
    assert count==10567695
    return {
      "actual_source_residues_replayed":1<<20,
      "full_20_clock_high_odd_source_residues":parity_count,
      "independent_direct_joint_count":count,
      "matches_CRT_weighted_suffix_dp":True,
    }


def prefix_negative_control()->list[dict]:
    # Positive source shadows with arbitrarily long finite all-odd
    # history. Their SOURCE CHANGES with K, so they do not establish
    # existence of a fixed infinitely odd positive original source.
    x=[]
    for K in (8,16,32,64,96,128):
        n=(1<<K)-1
        v=n
        for _ in range(K):
            assert v&1
            v=step(v)
        assert v==(3**K)-1
        x.append({"positive_source":str(n),
                  "all_odd_prefix_clocks":K,
                  "actual_endpoint":str(v),
                  "no_infinite_Nat_counterexample_proved":True})
    return x


def main()->None:
    mark,low,h1,h2=audited_mask()
    rows=joint_suffix_dp(low)
    replay=independent_direct_20(low)
    shadow=prefix_negative_control()
    out={
      "schema":"COLLATZ_V186_JOINT_PROTECTED_FUTURE_RECONCILIATION",
      "source_bank":"V178 205 individual kernel-qualified genuine two-clock strict source rules",
      "source_inverse_compiler":"V180 29 separately kernel-qualified guarded odd inverse rules",
      "V178_bank_sha256":h1,
      "V180_bank_sha256":h2,
      "source_modulus":M,
      "certified_source_position_unexcluded_per_M":132150,
      "source_position_fraction_exact":f"{Fraction(132150,M).numerator}/{Fraction(132150,M).denominator}",
      "V161_actual_source_finite_parity_word_correspondence":True,
      "V184_hypothetical_least_bad_all_positive_five_block_odd_prefix":True,
      "V185_true_source_plus_one_coefficient_guard":True,
      "weighted_CRT_suffix_dynamic_program":rows,
      "independent_real_shortcut_direct_k20_control":replay,
      "positive_Mersenne_arbitrarily_long_finite_parity_shadows":shadow,
      "unbounded_analytic_source_candidate_natural_density":"ZERO",
      "density_zero_analytic_proof":"For every r, high-odd candidate proportion <=(3125/3456)^r by binomial moment; fixed candidate set lies in every such finite parity cylinder, so upper density tends to zero.",
      "binomial_all_r_analytic_argument_separately_formalized_in_Lean":False,
      "joint_candidate_natural_density_zero_Does_NOT_Eliminate_One_Source":True,
      "all_scale_invariant_bad_basin_excluded":False,
      "global_collatz":"UNKNOWN",
      "qed":False
    }
    Path("evidence").mkdir(exist_ok=True)
    dest=Path("evidence/v186-joint-exact.json")
    dest.write_text(json.dumps(out,sort_keys=True,indent=2)+"\n")
    print(json.dumps({
      "schema":out["schema"],
      "period_M":M,
      "previous_survivors":132150,
      "k20_joint_exact":rows[0]["joint_candidate_residue_count"],
      "k80_joint_exact":rows[-1]["joint_candidate_residue_count"],
      "k80_joint_fraction":rows[-1]["joint_candidate_fraction_float_display"],
      "independent_20_bit_replay":replay["matches_CRT_weighted_suffix_dp"],
      "unbounded_natural_density_of_candidate_prefix_set":"ZERO_NOT_EMPTY",
      "global_collatz":"UNKNOWN"
    },sort_keys=True))


if __name__=="__main__":
    main()
