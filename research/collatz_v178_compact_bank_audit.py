"""V178 compact, all-offset candidate-least-bad sieve: independent exact audit.

The V177 Lean theorem universally lifts every genuine two-clock source
meeting to an infinite affine progression of honest source meetings.
A least nonconvergent source cannot belong to any such progression if
the lifted companion is smaller and positive.

This script independently reconstructs and validates the source/clock
bank, compacts it by a greedy NONOVERLAPPING-SOURCE-RESIDUE contribution
count, then counts its exact residue-union in common period M=2^12*3^6.

The bank excludes positions ONLY AS THE HYPOTHETICAL LEAST BAD SOURCE.
It does NOT certify every excluded positive integer as terminating.
Remaining residue classes are grammar-relative candidate positions,
not Collatz counterexamples. No analytic asymptotic mass contraction
and no QED are asserted.

The selected 205 base records are individually supplied as typed Lean
proof terms in CompactLeastBadCandidateSieve.lean; the 3-million residue
population is EXACT_EXECUTABLE, not a separately compiled Lean theorem.
"""
from __future__ import annotations
from collections import Counter, defaultdict
from hashlib import sha256
from pathlib import Path
import json
import random


def T(n: int) -> int:
    assert n >= 0
    return n//2 if n%2==0 else (3*n+1)//2


def G7(n: int) -> int:
    assert n >= 0
    return n//2 if n%2==0 else (3*n+7)//2


def orbit(n: int, maxclock: int, step=T):
    values=[n]
    odd_counts=[0]
    for _ in range(maxclock):
        odd_counts.append(odd_counts[-1]+values[-1]%2)
        values.append(step(values[-1]))
    return values,odd_counts


def generate_candidate_rules(N: int, I: int, J: int):
    by_endpoint=defaultdict(list)
    for p in range(1,N+1):
        endpoints,odds=orbit(p,J)
        for j,y in enumerate(endpoints):
            by_endpoint[y].append((p,j,odds[j]))

    rows={}
    possible_meetings=0
    for n in range(2,N+1):
        endpoints,odds=orbit(n,I)
        for i,y in enumerate(endpoints):
            best=None
            for p,j,b in by_endpoint.get(y,()):
                if p>=n:
                    continue
                a=odds[i]
                source_slope=(1<<i)*(3**b)
                earlier_slope=(1<<j)*(3**a)
                if earlier_slope>source_slope:
                    continue
                assert p>0 and p<n
                assert endpoints[i]==y
                possible_meetings+=1
                entry=(source_slope,n%source_slope,n,p,i,j,a,b,earlier_slope)
                if best is None or entry<best:
                    best=entry
            if best is not None:
                key=(best[0],best[1])
                if key not in rows or best<rows[key]:
                    rows[key]=best
    return sorted(rows.values()),possible_meetings


def selected_cover(rules, M):
    mask=bytearray(M)
    selected=[]
    for rule in rules:
        stride,residue,*_=rule
        size=(M-1-residue)//stride+1
        gained=mask[residue::stride].count(0)
        if gained:
            mask[residue::stride]=b'\x01'*size
            selected.append(tuple(rule)+(gained,))
    assert sum(r[-1] for r in selected)==sum(mask)
    return selected,mask


def actual_qualified_rule(rule):
    L,r,n,p,i,j,a,b,R = rule[:9]
    assert 0<p<n
    y,oddsn=orbit(n,i)
    z,oddsp=orbit(p,j)
    assert y[-1]==z[-1]
    assert a==oddsn[-1] and b==oddsp[-1]
    assert L==(1<<i)*(3**b)
    assert R==(1<<j)*(3**a)
    assert R<=L and n%L==r


def negative_control():
    # The same *general* two-clock proof rule is sound for G7,
    # but it does not prove that its 5-cycle belongs to the 7-cycle.
    assert [G7(z) for z in (7,14)]==[14,7]
    assert [G7(z) for z in (5,11,20,10)]==[11,20,10,5]
    assert {7,14}.isdisjoint({5,11,20,10})
    # A source (5) excluded as a possible least *T*-bad source
    # is still nonterminal relative to G7's protected seed,
    # illustrating why the literal odd +1 dynamics is essential.
    return {
      "synthetic_3n_plus7_second_basin_exists":True,
      "true_T_exclusions_do_not_transfer_to_G7":True,
      "least_bad_candidate_exclusion_is_not_terminal_certification":True
    }


def main():
    path=Path("research/collatz_v178_compact_bank.json")
    stated=json.loads(path.read_text())
    N,I,J,M=16384,12,6,(1<<12)*(3**6)
    assert (stated["N"],stated["I"],stated["J"],stated["M"]) == (N,I,J,M)
    rules,possible=generate_candidate_rules(N,I,J)
    selected,mask=selected_cover(rules,M)
    assert len(rules)==15123
    assert len(selected)==205
    assert len(stated["selected"])==len(selected)
    assert [list(r) for r in selected]==stated["selected"]
    assert sum(mask)==2915346
    assert M-sum(mask)==70638
    assert M==2985984

    direct_mask=bytearray(M)
    for L,r,n,p,i,j,a,b,R in rules:
        if j==0:
            direct_mask[r::L]=b'\x01'*((M-1-r)//L+1)
    direct_count=sum(direct_mask)
    assert 0<direct_count<sum(mask)

    # Independently replay every selected original-source meeting and
    # multiple unbounded family offsets, without a future-class oracle.
    replayed=0
    for entry in selected:
        actual_qualified_rule(entry)
        L,res,n,p,i,j,a,b,R,_gain=entry
        for offset in (0,1,2,7,1000,100000):
            x=n+L*offset
            y=p+R*offset
            assert y<x and y>0
            assert orbit(x,i)[0][-1] == orbit(y,j)[0][-1],entry
            replayed+=1

    # M is common multiple of every source stride; EVERY selected
    # position above N has an actual nonnegative family offset.
    assert all(M%r[0]==0 for r in selected)
    rng=random.Random(178)
    threshold_control=0
    for _ in range(20000):
        r=rng.randrange(M)
        n=N+M*rng.randrange(1,25)+r
        if mask[n%M]:
            chosen=next((entry for entry in selected
                if n%entry[0] == entry[1]),None)
            assert chosen is not None
            L,res,base,p,i,j,a,b,R,_gain=chosen
            assert n>=base
            offset=(n-base)//L
            assert n==base+L*offset
            assert p+R*offset<n
            # Exact affine lift certifies every such n as a
            # NON-minimal-bad position, not as terminal-good.
            threshold_control+=1

    # Check the strongest finite-period classes and the actual
    # grammar-relative survivor residue signature.
    survivors=[r for r in range(M) if mask[r]==0]
    by12=Counter(r%12 for r in survivors)
    assert by12=={3:43284,7:27354}
    thresholds={}
    cumulative=0
    for i,entry in enumerate(selected,1):
        cumulative+=entry[-1]
        if i in (1,3,6,14,19,40,205):
            thresholds[str(i)]={
              'selected_rules':i,'certified_residue_union':cumulative,
              'fraction':cumulative/M
            }
    assert thresholds['205']['certified_residue_union']==2915346

    out={
      'schema':'COLLATZ_V178_COMPACT_LEAST_BAD_RESIDUE_ELIMINATION',
      'source_head_N':N,'maximum_forward_clock':I,
      'maximum_earlier_clock':J,'common_period':M,
      'candidate_meetings_examined':possible,
      'distinct_progressions_before_compaction':len(rules),
      'kernel_base_rule_entries':len(selected),
      'exact_residue_positions_excluded_as_LEAST_bad':sum(mask),
      'exact_residue_positions_UNRESOLVED_in_grammar':len(survivors),
      'excluded_fraction':sum(mask)/M,
      'direct_only_source_residue_exclusions':direct_count,
      'extra_exclusions_from_two_clock_merger_candidates':sum(mask)-direct_count,
      'selected_base_plus_offset_real_meetings_replayed':replayed,
      'sample_sources_above_activation_checked':threshold_control,
      'zero_count_of_mod3_equals2_survivors':
        sum(1 for r in survivors if r%3==2),
      'survivor_residue_mod12_counts':dict(sorted(by12.items())),
      'selected_prefix_rule_coverage':thresholds,
      'residue_mask_sha256':sha256(mask).hexdigest(),
      'reconstructed_exact_bank_sha256':sha256(
          json.dumps(stated,sort_keys=True).encode()).hexdigest(),
      'negative_controls':negative_control(),
      'each_rule_has_genuine_original_source_and_two_clocks':True,
      'V177_unbounded_lift_is_a_separate_kernel_warrant':True,
      'finite_bank_rule_soundness_being_qualified_in_Lean':True,
      'asymptotic_mask_is_not_terminal_good_mass':True,
      'survivors_are_not_collatz_counterexamples':True,
      'all_scale_complete_elimination_proved':False,
      'global_collatz':'UNKNOWN','qed':False
    }
    Path("evidence").mkdir(exist_ok=True)
    Path("evidence/v178-audit.json").write_text(
      json.dumps(out,sort_keys=True,indent=2)+'\n')
    print(json.dumps({
      'schema':out['schema'],'selected_bank':out['kernel_base_rule_entries'],
      'coverage':f"{sum(mask)}/{M}",'survivors':len(survivors),
      'replayed':replayed,'global_collatz':out['global_collatz']
    },sort_keys=True))

if __name__=="__main__":
    main()
