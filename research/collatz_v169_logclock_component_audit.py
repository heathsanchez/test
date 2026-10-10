"""V169 exact timed-target and future-component giant test.

The unconditional lemma is that any *ordinary* Collatz hit on a target
b ≡ 2 mod3 is a genuine *shortcut* hit, with shortcut clock no larger
than the ordinary clock. Other targets are not interchangeable:
C(1)=4, but T^j(1) never equals4.

The external September 2026 logarithmic-hitting-density theorem says
a hypothetical bad target b ≡ 2 mod3 has a positive natural density of
ordinary predecessors with time <=c log(n) for any c>10.43.
Choose c=11: for n<2^k, ordinary clock is bounded by 8*k,
because 11*log2<8. The analytic theorem is NOT re-built here.

We test the largest *unseeded* exact future component from the V168
source-labelled union graph at H=8k. The full graph is expected to
collapse to a single terminal component at each sampled finite
Collatz cutoff; the 3n+7 synthetic control must preserve a
macroscopic unseeded component. This proves NOTHING for all k.
"""
from __future__ import annotations
import hashlib
import json
import math
from pathlib import Path
import subprocess


def C(n: int) -> int:
    assert n >= 0
    return n//2 if n%2 == 0 else 3*n+1


def T(n: int) -> int:
    assert n >= 0
    return n//2 if n%2 == 0 else (3*n+1)//2


def verify_ordinary_shortcut_phase():
    cases=0
    hits=0
    for n in range(1,12001):
        maxclock=96
        shortcut_seen={}
        x=n
        for i in range(maxclock+1):
            shortcut_seen.setdefault(x, i)
            x=T(x)
        x=n
        for t in range(maxclock+1):
            cases+=1
            if x%3==2:
                hits+=1
                assert x in shortcut_seen and shortcut_seen[x]<=t,(n,t,x,shortcut_seen.get(x))
            if t<maxclock:
                x=C(x)
    assert C(1)==4 and all(T(1 if j%2==0 else 2) in (1,2) for j in range(50))
    assert all(x in (1,2) for x in (T(1),T(2)))
    assert 11*math.log(2)<8 and 11>3/math.log(4/3)
    return dict(source_count=12000,source_ordinary_clock_pairs=cases,
                residue_two_hits_checked=hits,
                ordinary_target_4_is_not_shortcut_target_for_source_1=True,
                phase_guard_is_necessary=True,
                logarithmic_clock_to_8k_arithmetic_tested=True)


def compile_graph():
    source=Path("research/collatz_v168_retrospective_quotient.cpp")
    assert source.is_file()
    executable=Path("evidence/v169_graph_runner")
    executable.parent.mkdir(parents=True,exist_ok=True)
    subprocess.run(["g++","-O3","-std=c++17",str(source),"-o",str(executable)],
                   check=True)
    return executable,hashlib.sha256(source.read_bytes()).hexdigest()


def run_graph(executable:Path, k:int, mode:str):
    H=8*k
    result=subprocess.run([str(executable),str(k),str(H),str(H),mode],
                          capture_output=True,text=True,check=True)
    d=json.loads(result.stdout)
    assert d['schema']=="COLLATZ_V168_RETROACTIVE_FUTURE_QUOTIENT"
    assert d['positive_source_cutoff']==(1<<k)-1
    assert d['initial_clock']==d['owner_clock_cap']==8*k
    assert d['initial_unresolved_sources']==d['final_unresolved_sources']
    assert d['initial_unresolved_components']==d['final_unresolved_components']
    assert d['additional_owner_attempts']>=0
    assert d['additional_source_clock_steps']==0
    assert d['finite_certificate_coverage_only']
    assert d['global_collatz']=='UNKNOWN' and d['qed'] is False
    return {
      'k':k,'H':H,'system':'TRUE_3N1' if mode=='T' else 'SYNTHETIC_3N7',
      'source_cutoff':(1<<k)-1,
      'original_sources_checked':(1<<k)-1,
      'observed_clock_pairs':d['initial_checked_source_clock_pairs'],
      'unseeded_source_count':d['initial_unresolved_sources'],
      'unseeded_component_count':d['initial_unresolved_components'],
      'largest_unseeded_component':d['initial_largest_unresolved_component'],
      'largest_unseeded_fraction_upper_denominator':1<<k,
      'largest_unseeded_fraction':d['initial_largest_unresolved_component']/(1<<k),
      'largest_unseeded_sample':d['initial_top_components'][:6],
      'terminal_component_count':d['initial_good_components'],
      'observed_nonterminal_cycle_receipts':d['observed_nonterminal_cycle_receipts'],
      'saw_only_finite_exact_sources':True
    }


def main():
    phase=verify_ordinary_shortcut_phase()
    exe,source_hash=compile_graph()
    true_cases=[]
    for k in (8,10,12,14,16,18,20,22,24):
        true_cases.append(run_graph(exe,k,'T'))
    negative=[]
    for k in (12,16,20):
        negative.append(run_graph(exe,k,'G'))
    assert all(x['largest_unseeded_component']<=x['unseeded_source_count']
               for x in true_cases+negative)
    assert negative[-1]['largest_unseeded_fraction']>0.2
    assert negative[-1]['unseeded_component_count']>0
    output={
      'schema':'COLLATZ_V169_LOGCLOCK_COMPONENT_GIANT_AUDIT',
      'source_cpp_sha256':source_hash,
      'ordinary_to_shortcut_phase_validation':phase,
      'timed_source_clock': 'H(k)=8*k',
      'ordinary_clock_coefficient':'c=11, 11 log 2 < 8',
      'external_timed_density_locally_kernel_built':False,
      'unconditional_exact_phase_bridge_in_Lean_requested':True,
      'full_component_ledger_clock_completeness_in_Lean_proved':False,
      'all_scale_no_giant_component_bound_proved':False,
      'finite_test_results_do_not_imply_global_Collatz':True,
      'true_3n1':true_cases,'adversarial_G7':negative,
      'global_collatz':'UNKNOWN','qed':False
    }
    Path('evidence/v169-summary.json').write_text(json.dumps(output,sort_keys=True,indent=2)+'\n')
    print(json.dumps({
      'schema':output['schema'],
      'source_checked':true_cases[-1]['source_cutoff'],
      'largest_unseeded_component_k24':true_cases[-1]['largest_unseeded_component'],
      'synthetic_g7_largest_unseeded_component_k20':negative[-1]['largest_unseeded_component'],
      'status':'BOUNDED_EXACT_ONLY',
      'global_collatz':output['global_collatz']
    },sort_keys=True))


if __name__=='__main__':
    main()
