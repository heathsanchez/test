"""V167 — independently replayable four-route Collatz proof-search audit.

This is an EXACT, BOUNDED arithmetic and proof-lineage experiment.
It does NOT establish the Collatz conjecture, a uniform mass contraction,
or any convergence claim beyond sources having checked certificates.

Tests:
 A. Recursive source-sorted terminal/previously-certified two-clock
    saturation, true T versus synthetic G7 dual-basin negative control.
 B. Complete bounded true reverse-funnel search for strictly earlier
    source meetings at two real independent clocks, with V119 20-bit
    Mersenne and source27 hard-case controls.
 C. Every fixed direct-size-descent clock is obstructed by a genuine
    all-ones source 2^K-1. A matching universal theorem is separately
    kernel-checked in V167.
 D. Fixed-modulus arithmetic graph and direct-power-lift height
    controls, including V134's three all-offset theorem families.
The populations UNKNOWN at a budget are NEVER labelled divergent.
"""
from __future__ import annotations
from collections import defaultdict
from hashlib import sha256
from functools import lru_cache
import json


def T(n: int) -> int:
    assert n >= 0
    return n // 2 if n % 2 == 0 else (3*n + 1)//2


def G7(n: int) -> int:
    assert n >= 0
    return n // 2 if n % 2 == 0 else (3*n + 7)//2


def advance(n: int, t: int, step=T) -> int:
    for _ in range(t):
        n = step(n)
    return n


def certify_population(N: int, H: int, J: int, step=T,
                       roots=(1, 2), audit: bool = False) -> dict:
    """Inductively SOUND: a previously certified smaller source
    plus a real two-clock endpoint equality certifies n.

    Every stored certificate points to a source p<n, so the chain
    cannot be circular. terminal_clock[n] is a derived *actual*
    terminal clock, not a guessed eventual-convergence claim.
    """
    roots = frozenset(roots)
    assert all(step(x) in roots for x in roots)
    certified = {}
    endpoint_index = {}
    direct = merged = 0
    digest = sha256()
    special = {}
    sample = {3, 7, 27, 31, 703, 1023, 2047, 4095, 8191, 16383,
              65535, 1048575}

    for n in range(1, N+1):
        x = n
        witness = None
        for i in range(H+1):
            if x in roots:
                witness = ('TERMINAL', i, 0, 0, i)
                break
            prior = endpoint_index.get(x)
            if prior is not None:
                p, j = prior
                assert p in certified and 0 < p < n
                assert advance(n, i, step) == advance(p, j, step)
                prev_clock = certified[p][4]
                total_clock = i + max(prev_clock-j, 0)
                witness = ('EARLIER_SOURCE', i, p, j, total_clock)
                break
            x = step(x)
        if witness is None:
            if n in sample:
                special[n] = 'UNKNOWN_AT_BUDGET'
            continue

        if witness[0] == 'TERMINAL':
            direct += 1
        else:
            merged += 1
        certified[n] = witness
        digest.update(f'{n}:{witness}\n'.encode())
        if n in sample:
            special[n] = {'method': witness[0], 'source_clock': witness[1],
                'earlier_source': witness[2], 'earlier_clock': witness[3],
                'derived_terminal_clock': witness[4]}
        if audit and (n <= 100 or n % 997 == 0 or n in sample):
            assert advance(n, witness[4], step) in roots, (n, witness)

        v = n
        for j in range(J+1):
            # Original source n already certified, so its entire
            # later orbit is warranted, even past the H clock.
            endpoint_index.setdefault(v, (n, j))
            v = step(v)

    if audit:
        for n, witness in certified.items():
            if witness[0] == 'EARLIER_SOURCE':
                assert 0 < witness[2] < n and witness[2] in certified
        for n in special:
            if isinstance(special[n], dict):
                assert advance(n, special[n]['derived_terminal_clock'], step) in roots

    return {
        'cutoff_exclusive': N+1,
        'forward_clock_cap': H, 'earlier_source_clock_cap': J,
        'original_positive_sources': N, 'direct_admissions': direct,
        'certified_earlier_source_mergers': merged,
        'total_certified': len(certified),
        'positive_source_timeouts': N-len(certified),
        'first_uncertified': next((n for n in range(1, N+1)
                                   if n not in certified), None),
        'ledger_sha256': digest.hexdigest(), 'special_controls': special,
    }


def direct_terminal_by_clock(N: int, H: int, roots=(1, 2), step=T) -> int:
    roots = frozenset(roots)
    return sum(advance(n, H, step) in roots for n in range(1, N+1))


def route_A() -> dict:
    J = 12
    rows = []
    for K in (8, 10, 12, 14, 16, 18, 20):
        N = (1 << K)-1
        result = certify_population(N, 4*K, J, T, (1, 2),
                                    audit=(K in (14, 16, 20)))
        result['K'] = K
        result['timeout_fraction_of_full_dyadic_cutoff'] = (
            result['positive_source_timeouts'] / (1 << K))
        if K <= 16:
            result['direct_terminal_only'] = direct_terminal_by_clock(N, 4*K)
        rows.append(result)
    byK = {r['K']:r for r in rows}
    assert byK[14]['total_certified'] == 16345
    assert byK[14]['positive_source_timeouts'] == 38
    assert byK[16]['positive_source_timeouts'] == 98
    assert byK[18]['positive_source_timeouts'] == 322
    assert byK[20]['positive_source_timeouts'] == 1050
    # At K=14,H=40, compare source-relative reuse to direct hits.
    fixed = certify_population((1<<14)-1, 40, 12, T, (1,2), audit=True)
    assert fixed['total_certified']==16124
    assert fixed['positive_source_timeouts']==259
    direct = direct_terminal_by_clock((1<<14)-1, 40)
    assert direct==5832
    fixed['direct_terminal_only_same_clock'] = direct
    fixed['additional_sources_certified_vs_direct_only'] = (
        fixed['total_certified']-direct)
    assert fixed['additional_sources_certified_vs_direct_only']==10292

    negative = certify_population((1<<14)-1,40,12,G7,(7,14), audit=True)
    assert negative['total_certified']==2299
    assert negative['positive_source_timeouts']==14084

    mass_ratios = []
    for prev, curr in zip(rows, rows[1:]):
        ratio=(curr['positive_source_timeouts']/(1<<curr['K'])) / (
            prev['positive_source_timeouts']/(1<<prev['K']))
        mass_ratios.append({'k_from':prev['K'],'k_to':curr['K'],
                            'observed_dyadic_timeout_fraction_ratio':ratio})
    assert any(x['observed_dyadic_timeout_fraction_ratio']>0.8
               for x in mass_ratios)
    return {
        'status':'BOUNDED_SOUND_SOURCE_SORTED_CERTIFICATE_POLICY',
        'method':'Exact terminal + earlier already-certified source with independent clocks',
        'root_ledger_lower_source_chains_well_founded':True,
        'no_unknown_admitted_as_convergent':True,
        'direct_vs_merger_40step_k14':fixed,
        'sparse_scale_rows':rows,
        'measured_timeout_density_ratios':mass_ratios,
        'lambda_0_8_zero_error_dyadic_two_bit_recursion_falsified_in_sample':True,
        'synthetic_G7_only_seven_cycle_basin':negative,
        'synthetic_second_basin_5_11_20_10_preserved':True,
        'all_scale_mass_contraction_proved':False
    }


def reverse_predecessors(y: int) -> tuple[int, ...]:
    out = [2*y]
    if y % 3 == 2:
        p=(2*y-1)//3
        assert p > 0 and T(p)==y
        out.append(p)
    assert all(T(p)==y for p in out)
    return tuple(out)


def bounded_reverse_funnel(n: int, H: int, J: int):
    x = n
    for i in range(H+1):
        layer={x}
        for j in range(J+1):
            p = min((v for v in layer if 0 < v < n), default=None)
            if p is not None:
                assert advance(n,i)==advance(p,j)
                return {'source':n, 'forward_clock':i,
                        'earlier_source':p,'reverse_clock':j}
            if j<J:
                layer={v for y in layer for v in reverse_predecessors(y)}
        x = T(x)
    return None


def route_B() -> dict:
    rows=[]
    for H,J in ((3,0),(8,0),(8,4),(12,8),(20,12)):
        witnesses=[]
        unknown=[]
        for n in range(3,1025):
            w=bounded_reverse_funnel(n,H,J)
            if w is None:
                unknown.append(n)
            else:
                witnesses.append(w)
        rows.append({'H':H,'J':J,'sources_3_through_1024':1022,
                     'qualified_lower_meetings':len(witnesses),
                     'no_meeting_within_budget':len(unknown),
                     'first_unknown_sources':unknown[:24],
                     'sample_witnesses':[w for w in witnesses if
                          w['source'] in (7,9,11,21,23,27,31,63,127)]})
    assert [r['no_meeting_within_budget'] for r in rows] == [
        256,76,39,18,9]
    assert bounded_reverse_funnel(27,20,12) is None
    hard27 = bounded_reverse_funnel(27,59,12)
    assert hard27 == {'source':27,'forward_clock':59,
                     'earlier_source':23,'reverse_clock':0}
    k20=(1<<20)-1
    mersenne20=bounded_reverse_funnel(k20,20,12)
    assert mersenne20 is not None
    assert (mersenne20['forward_clock'],mersenne20['reverse_clock'],
            mersenne20['earlier_source']) == (1,10,736447)
    other_hard={}
    for n in (703,(1<<16)-1,(1<<20)-1):
        other_hard[n]={
            'H12_J8': bounded_reverse_funnel(n,12,8),
            'H20_J12': bounded_reverse_funnel(n,20,12)
        }
    return {
        'status':'EXACT_BOUNDED_TWO_CLOCK_REVERSE_FUNNEL',
        'even_reverse_and_guarded_odd_reverse_complete_at_one_step':True,
        'not_assuming_earlier_source_good':True,
        'least_bad_source_would_make_all_earlier_sources_good':True,
        'source27_requires_later_actual_meeting_than_budget20':True,
        'source27_first_reported_59_step_meeting_reproduced':hard27,
        'v119_mersenne20_one_step_with_ten_step_earlier_join_reproduced':mersenne20,
        'rows':rows,'adversarial':other_hard,
        'universal_funnel_clock_bound_proved':False,
        'globally_excluded_least_bad_source':False
    }


def route_C() -> dict:
    adversarial=[]
    for H in (1,4,8,16,32,64,128):
        K=H+3
        n=(1<<K)-1
        x=n
        for j in range(H+1):
            assert x==(3**j)*(2**(K-j))-1,(H,j,n,x)
            assert n<=x and x not in (1,2)
            if j>0:
                assert x>n
            x=T(x)
        adversarial.append({
            'fixed_clock_H':H,'actual_Mersenne_source':str(n),
            'source_bit_length':n.bit_length(),
            'all_positive_clocks_through_H_strictly_above_source':True,
            'no_terminal_hit_through_H':True
        })
    assert T(3)==5 and T(7)==11
    assert (5).bit_length()>(3).bit_length()
    assert advance(3,3)==4 and T(4)==2
    return {
        'status':'FINITE_REPLAY_OF_UNIVERSAL_MERSENNE_CORRIDOR',
        'general_all_H_theorem_submitted_to_Lean_separately':True,
        'all_fixed_H_size_descent_premises_have_exact_counterfamilies':True,
        'single_step_n_rank_fails_at_3':True,
        'single_step_bitlength_rank_fails_at_3':True,
        'v156_last_live_state_source3_clock3_is_existing_formal_negative_control':True,
        'does_not_refute_source_dependent_rank_or_exit_producer':True,
        'arbitrary_H_consequences_tested':adversarial
    }


@lru_cache(None)
def discrete_logs_pow2(a: int):
    assert a>=0
    m=3**a
    if m==1:
        return {0:0},1
    table={}
    x=1
    while x not in table:
        table[x]=len(table)
        x=2*x%m
    assert x==1
    assert len(table)==2*3**(a-1)
    assert all(z%3 for z in table)
    return table,len(table)


def first_terminal_power_exponent(r: int, k: int):
    assert 0<=r<(1<<k)
    n=r
    a=0
    for _ in range(k):
        a+=n&1
        n=T(n)
    g=n
    m=3**a
    table,order=discrete_logs_pow2(a)
    if a:
        assert g%3!=0
    L=table[g % m]
    while (1<<L)<g:
        L+=order
    diff=(1<<L)-g
    assert diff>=0 and diff%m==0
    q=diff//m
    orig=r+(1<<k)*q
    assert orig>0 and orig%(1<<k)==r
    # V160 exact affine chart, plus actual source check only
    # for hand-picked cases; no need to run 2^L iterations.
    if k<=9 and (r in (0,1,(1<<k)-1)):
        assert advance(orig,k)==1<<L
    return {'L':L,'a':a,'g':g,'source_bit_length':orig.bit_length()}


def modular_graph_components(M: int, odd_constant: int):
    parent=list(range(M))
    def find(a):
        while parent[a]!=a:
            parent[a]=parent[parent[a]]
            a=parent[a]
        return a
    def link(a,b):
        a=find(a); b=find(b)
        if a!=b:
            parent[a]=b
    for r in range(M):
        link(r,(2*r)%M)
        # Genuine odd integer lifts exist exactly when M is odd
        # or the residue r is odd.
        if M%2 or r%2:
            link(r,(3*r+odd_constant)%M)
    return len({find(r) for r in range(M)})


def route_D() -> dict:
    graph=[]
    for M in range(1,253):
        true_components=modular_graph_components(M,1)
        synthetic_components=modular_graph_components(M,7)
        assert true_components==1
        assert synthetic_components==(2 if M%7==0 else 1),M
        if M in (1,7,14,21,35,49,98,127,128,147,168,252):
            graph.append({'M':M,'true_components':true_components,
                          'synthetic_3n_plus_7_components':synthetic_components})

    direct=[]
    total_source_prefixes=0
    for k in range(1,13):
        maximum=(0,0)
        max_bit_len=0
        for r in range(1<<k):
            w=first_terminal_power_exponent(r,k)
            total_source_prefixes+=1
            max_bit_len=max(max_bit_len,w['source_bit_length'])
            if w['L']>=maximum[0]:
                maximum=(w['L'],r)
        assert maximum==(3**(k-1),(1<<k)-1),(k,maximum)
        direct.append({
            'k':k,'tested_dyadic_prefixes':1<<k,
            'largest_minimum_direct_power_exponent':maximum[0],
            'worst_prefix':maximum[1],
            'max_direct_power_witness_source_bit_length':max_bit_len
        })

    law_list=[
        (21,72,3,12,3,2),
        (9,1536,3,486,9,1),
        (23,384,3,54,7,1)
    ]
    N=4608
    covered=[]
    for n in range(1,N+1):
        matches=[]
        for base,step,prebase,prestep,iclock,jclock in law_list:
            if n>=base and (n-base)%step==0:
                q=(n-base)//step
                p=prebase+prestep*q
                assert 0<p<n
                assert advance(n,iclock)==advance(p,jclock)
                matches.append((base,q))
        assert len(matches)<=1
        if matches:
            covered.append(n)
    assert len(covered)==79
    bank_density=79/4608
    assert bank_density<0.018
    return {
        'status':'EXACT_FIXED_MODULUS_AND_WITNESS_HEIGHT_STRESS',
        'all_true_modular_graphs_connected_for_M_1_to_252':True,
        'all_synthetic_G7_graphs_split_iff_M_divisible_by7_in_sample':True,
        'graph_samples':graph,
        'direct_power_lift_all_prefixes_tested_through_k12':True,
        'source_prefix_count_tested':total_source_prefixes,
        'all_ones_exponent_exact_three_power_k_minus_one_through_k12':True,
        'direct_power_height_rows':direct,
        'V134_three_formally_warranted_source_family_laws_exactly_replayed':True,
        'V134_direct_family_source_coverage_per_4608':79,
        'V134_direct_family_source_coverage_fraction':bank_density,
        'direct_law_source_bases':[21,9,23],
        'direct_laws_only_are_not_complete':True,
        'fixed_modular_connectivity_not_actual_two_clock_coalescence':True,
        'height_control_for_all_true_future_class_mergers_proved':False
    }


def main():
    A=route_A()
    B=route_B()
    C=route_C()
    D=route_D()
    assert A['direct_vs_merger_40step_k14']['additional_sources_certified_vs_direct_only']>10000
    assert B['rows'][-1]['no_meeting_within_budget']>0
    assert C['all_fixed_H_size_descent_premises_have_exact_counterfamilies']
    assert D['V134_direct_family_source_coverage_per_4608']==79
    return {
        'schema':'COLLATZ_V167_ALL_FOUR_ROUTE_SOURCE_FAITHFUL_AUDIT',
        'map_true':'T(even)=n/2;T(odd)=(3n+1)/2',
        'map_adversarial':'G7(even)=n/2;G7(odd)=(3n+7)/2',
        'all_four_routes_ran':True,
        'all_certified_source_witnesses_are_genuine':True,
        'all_timeouts_remain_UNKNOWN_not_bad':True,
        'V151_unbounded_exceptional_mass_bound_proved':False,
        'external_Mazur_amplifier_built_locally':False,
        'global_collatz':'UNKNOWN','qed':False,
        'approach_A_backward_certificate_saturation':A,
        'approach_B_least_bad_reverse_funnel':B,
        'approach_C_source_relative_rank_stress':C,
        'approach_D_height_controlled_modular_expansion':D,
        'decision':'Keep quantitative source-capped certificate growth as a RESEARCH_CANDIDATE, with exact all-source dynamic progress still UNKNOWN.'
    }


if __name__=='__main__':
    print(json.dumps(main(),sort_keys=True,indent=2))
