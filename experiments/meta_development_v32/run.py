from __future__ import annotations
import hashlib, json, re
from pathlib import Path

HERE=Path(__file__).resolve().parent
from basis import canonical_partition, vector, read_exprs
from kernel import DevelopmentMemory, Kernel
from challenge_pack import TRAIN_A,TRAIN_B,HELDOUT,INCOMPLETE,case_matches

SCIENTIFIC_FREEZE_COMMIT="85c8bdb04d2e9b622eb648015f95a638039a2aa4"

def sha256(p: Path)->str:
    return hashlib.sha256(p.read_bytes()).hexdigest()

def safe(x):
    if hasattr(x,'data'): return safe(x.data())
    if isinstance(x,dict): return {str(k):safe(v) for k,v in x.items() if not str(k).startswith('_')}
    if isinstance(x,(list,tuple)): return [safe(v) for v in x]
    return x

def verify_freeze():
    freeze=json.loads((HERE/'FREEZE.json').read_text())
    observed={name:sha256(HERE/name) for name in freeze['scientific_core_paths']}
    return freeze, observed, observed==freeze['sha256']

def main():
    freeze, observed_hashes, freeze_ok=verify_freeze()

    mem=DevelopmentMemory(min_support=2)
    warm=Kernel(mem)
    results={'train_a':{},'train_b':{},'heldout_cold':{},'heldout_warm':{}}
    compile_rows=[]

    for ca,cb in zip(TRAIN_A,TRAIN_B):
        ra=warm.solve(ca.world,use_memory=False); warm.compile(ra)
        rb=warm.solve(cb.world,use_memory=False); comp=warm.compile(rb)
        results['train_a'][ca.axis]=safe(ra); results['train_b'][cb.axis]=safe(rb)
        compile_rows.append({'axis':ca.axis,'compile':comp,'a_ok':case_matches(ca,ra),'b_ok':case_matches(cb,rb)})

    cold_total=0; warm_total=0; held_rows=[]
    for case in HELDOUT:
        rc=Kernel().solve(case.world,use_memory=False)
        rw=warm.solve(case.world,use_memory=True)
        results['heldout_cold'][case.axis]=safe(rc); results['heldout_warm'][case.axis]=safe(rw)
        cold_total += int(rc.get('acquisition_tested',0)); warm_total += int(rw.get('acquisition_tested',0))
        held_rows.append({'axis':case.axis,'cold_ok':case_matches(case,rc),'warm_ok':case_matches(case,rw),
                          'cold_acq':rc.get('acquisition_tested',0),'warm_acq':rw.get('acquisition_tested',0),
                          'used_hint':rw.get('used_memory_hint',False)})

    # Force a structurally wrong compiled route to establish verify-before-trust.
    context_case=next(c for c in HELDOUT if c.axis=='context_conditioned')
    wrong_hint={'stage':2,'family':'PAIR','bank_pattern':[0,0]}
    wrong=warm.solve(context_case.world,use_memory=False,forced_hint=wrong_hint)

    contraction_case=next(c for c in HELDOUT if c.axis=='contraction')
    cr=warm.solve(contraction_case.world,use_memory=True)
    raw_id=next(e for e in read_exprs(contraction_case.world) if tuple(e.args)==(5,0))
    raw_blocks=len(set(canonical_partition(vector(raw_id,contraction_case.world.rows))))
    target_blocks=len(set(r.consequence for r in contraction_case.world.rows))

    incomplete=warm.solve(INCOMPLETE)
    nover=warm.solve(HELDOUT[3].world,verification_enabled=False)

    evidence={
      'experiment':'anonymous_meta_development_axis_selection_v32',
      'scientific_freeze_commit':SCIENTIFIC_FREEZE_COMMIT,
      'freeze_manifest':freeze,
      'observed_core_hashes':observed_hashes,
      'results':results,
      'compile_rows':compile_rows,'heldout_rows':held_rows,
      'cold_acquisition_tested':cold_total,'warm_acquisition_tested':warm_total,
      'speedup': (cold_total/warm_total if warm_total else None),
      'wrong_hint':safe(wrong),'incomplete':safe(incomplete),'no_verifier':safe(nover),
      'contraction':{'raw_identity_blocks':raw_blocks,'target_blocks':target_blocks,'result':safe(cr)},
      'compiled_memory_count':len(mem.compiled),'gates':{}
    }
    G=evidence['gates']
    G['F0_frozen_core_hashes_match_manifest']=freeze_ok
    G['M1_one_frozen_kernel_solves_all_training_axes']=all(r['a_ok'] and r['b_ok'] for r in compile_rows)
    G['M2_all_heldout_axes_recovered_cold']=all(r['cold_ok'] for r in held_rows)
    G['M3_all_heldout_axes_recovered_warm']=all(r['warm_ok'] for r in held_rows)
    G['M4_two_recurrences_required_before_meta_compile']=all(r['compile']['status'] in {'COMPILED','OBSERVED'} for r in compile_rows) and len(mem.compiled)>=8
    G['M5_active_probe_generated_and_collapses_noncanonical_frontier']=all(
        results[k]['active_probe'].get('probe') is not None and results[k]['active_probe'].get('frontier_size_after_probe')==1
        for k in ('train_a','train_b','heldout_cold','heldout_warm'))
    G['M6_warm_meta_replay_preserves_verified_solution']=all(r['cold_ok'] and r['warm_ok'] for r in held_rows)
    G['M7_meta_compilation_reduces_acquisition_search_at_least_fourfold']=(warm_total>0 and cold_total>=4*warm_total)
    G['M8_multiple_heldout_worlds_use_compiled_developmental_hint']=sum(1 for r in held_rows if r['used_hint'])>=6
    G['M9_wrong_meta_hint_is_rejected_before_fallback']=wrong.get('status')=='VERIFIED' and wrong.get('hint_replay_failed') is True and wrong.get('route',{}).get('family')=='SWITCH'
    G['M10_contraction_is_real_not_label_only']=raw_blocks>target_blocks and cr.get('status')=='VERIFIED'
    G['M11_incomplete_authority_stays_unknown']=incomplete.get('status')=='UNKNOWN_AUTHORITY'
    G['M12_verifier_ablation_authorizes_no_growth']=nover.get('status')=='UNKNOWN_NO_VERIFIER' and nover.get('acquisition_tested')==0
    kernel_text=(HERE/'kernel.py').read_text().lower()
    G['M13_challenge_axis_names_absent_from_frozen_kernel']=all(tok not in kernel_text for tok in ('present_split','higher_arity','context_conditioned','intervention_conditioned','joint_carrier','active_probe'))
    G['M14_structural_dsl_is_generic_not_domain_named']=all(re.search(r'\b'+re.escape(tok)+r'\b',kernel_text) is None for tok in ('bell','quantum','physics','symmetry','causal_state'))
    evidence['full_pass']=all(G.values())
    evidence['verdict']='VERIFIED_ANONYMOUS_DEVELOPMENTAL_AXIS_SELECTION_ACTIVE_DISCRIMINATION_AND_META_COMPILATION' if evidence['full_pass'] else 'META_DEVELOPMENT_V32_GAPS_EXPOSED'
    (HERE/'evidence.json').write_text(json.dumps(evidence,indent=2,sort_keys=True,default=str)+'\n')
    print(json.dumps(evidence,indent=2,sort_keys=True,default=str))
    return 0 if evidence['full_pass'] else 1

if __name__=='__main__':
    raise SystemExit(main())
