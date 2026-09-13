from __future__ import annotations
import ast, hashlib, json, re
from pathlib import Path

HERE=Path(__file__).resolve().parent
from kernel import Kernel
from challenge_pack import AXES,VARIANTS,INCOMPLETE,expected,dep_banks

SCIENTIFIC_FREEZE_COMMIT='b5116b228beab50958d29b2bafa4a161dd358abc'

def safe(x):
    if hasattr(x,'data'): return safe(x.data())
    if isinstance(x,dict): return {str(k):safe(v) for k,v in x.items() if not str(k).startswith('_')}
    if isinstance(x,(list,tuple)): return [safe(v) for v in x]
    return x

def git_blob_sha(path: Path) -> str:
    data=path.read_bytes()
    return hashlib.sha1(f'blob {len(data)}\0'.encode()+data).hexdigest()

def main() -> int:
    freeze=json.loads((HERE/'FREEZE.json').read_text())
    observed={name:git_blob_sha(HERE/name) for name in freeze['scientific_core_paths']}
    frozen_ok=observed==freeze['git_blob_sha']

    all_results={}
    all_checks={}
    for variant,cases in VARIANTS.items():
        k=Kernel(max_nand_cost=5)
        vr={}; vc={}
        for case in cases:
            r=k.solve(case.world)
            vr[case.axis]=safe(r)
            vc[case.axis]=expected(case,r,variant)
        all_results[str(variant)]=vr
        all_checks[str(variant)]=vc

    v0={c.axis:c for c in VARIANTS[0]}
    # Constructor ablation: anonymous atoms remain, NAND composition is unavailable.
    abk=Kernel(max_nand_cost=0)
    ablation={axis:safe(abk.solve(v0[axis].world)) for axis in AXES}

    incomplete=Kernel().solve(INCOMPLETE)
    no_verifier=Kernel().solve(v0['context'].world,verification_enabled=False)

    evidence={
        'experiment':'minimal_anonymous_nand_substrate_v33',
        'scientific_freeze_commit':SCIENTIFIC_FREEZE_COMMIT,
        'freeze_manifest':freeze,
        'observed_git_blob_sha':observed,
        'results':all_results,
        'checks':all_checks,
        'nand_ablation':ablation,
        'incomplete':safe(incomplete),
        'no_verifier':safe(no_verifier),
        'gates':{},
    }
    G=evidence['gates']
    G['N1_frozen_core_hashes_match_exactly']=frozen_ok
    G['N2_one_kernel_recovers_all_families_in_three_relabellings']=all(all(vc.values()) for vc in all_checks.values())

    for v in ('0','1','2'):
        R=all_results[v]
        G.setdefault('N3_no_change_uses_zero_roots',True)
        G['N3_no_change_uses_zero_roots'] &= R['no_change']['root_count']==0 and R['no_change']['nand_cost']==0

        G.setdefault('N4_present_and_history_are_distinct_zero_nand_atoms',True)
        pb=dep_banks(R['present']); mb=dep_banks(R['memory'])
        G['N4_present_and_history_are_distinct_zero_nand_atoms'] &= (
            R['present']['root_count']==R['memory']['root_count']==1
            and R['present']['nand_cost']==R['memory']['nand_cost']==0
            and pb==[{0}] and mb==[{1}]
        )

        G.setdefault('N5_four_class_code_earns_two_roots_without_pair_constructor',True)
        G['N5_four_class_code_earns_two_roots_without_pair_constructor'] &= R['relation']['root_count']==2 and R['relation']['nand_cost']==0

        G.setdefault('N6_eight_class_code_earns_three_roots_without_tuple_constructor',True)
        G['N6_eight_class_code_earns_three_roots_without_tuple_constructor'] &= R['arity']['root_count']==3 and R['arity']['nand_cost']==0

        G.setdefault('N7_composed_case_requires_nonzero_nand_program',True)
        G['N7_composed_case_requires_nonzero_nand_program'] &= R['composition']['root_count']==1 and R['composition']['nand_cost']==3 and R['composition']['depth']==3

        G.setdefault('N8_context_and_intervention_require_composed_programs_on_distinct_banks',True)
        G['N8_context_and_intervention_require_composed_programs_on_distinct_banks'] &= (
            R['context']['nand_cost']==4 and R['context']['depth']==4 and dep_banks(R['context'])==[{0,2}]
            and R['intervention']['nand_cost']==4 and R['intervention']['depth']==4 and dep_banks(R['intervention'])==[{0,3}]
        )

        G.setdefault('N9_joint_code_spans_two_anonymous_banks_without_joint_constructor',True)
        jb=dep_banks(R['joint'])
        G['N9_joint_code_spans_two_anonymous_banks_without_joint_constructor'] &= (
            R['joint']['root_count']==2 and R['joint']['nand_cost']==0 and {frozenset(x) for x in jb}=={frozenset({0}),frozenset({4})}
        )

        G.setdefault('N10_contraction_selects_strictly_coarser_consequence_quotient',True)
        case=next(c for c in VARIANTS[int(v)] if c.axis=='contraction')
        raw=len({r.banks for r in case.world.rows}); target=len({r.consequence for r in case.world.rows})
        G['N10_contraction_selects_strictly_coarser_consequence_quotient'] &= raw>target==2 and R['contraction']['root_count']==1

        G.setdefault('N11_active_probe_collapses_noncanonical_minimum',True)
        G['N11_active_probe_collapses_noncanonical_minimum'] &= (
            R['probe']['frontier_size_before_probe']>=2
            and R['probe']['frontier_size_after_probe']==1
            and R['probe']['probe'] is not None
        )

    computed=('composition','context','intervention')
    raw=('no_change','present','memory','relation','arity','joint','contraction','probe')
    G['N12_nand_ablation_preserves_raw_cases_but_blocks_computed_cases']=(
        all(ablation[a].get('status')=='VERIFIED' for a in raw)
        and all(ablation[a].get('status')=='CERTIFIED_SUBSTRATE_INADEQUACY' for a in computed)
    )
    G['N13_incomplete_authority_stays_unknown']=incomplete.get('status')=='UNKNOWN_AUTHORITY'
    G['N14_verifier_ablation_authorizes_no_development']=no_verifier.get('status')=='UNKNOWN_NO_VERIFIER' and no_verifier.get('searched_terms')==0

    basis_text=(HERE/'basis.py').read_text()
    kernel_text=(HERE/'kernel.py').read_text()
    executable=(basis_text+'\n'+kernel_text).lower()
    forbidden=('read','pair','tuple3','switch','apply','present_split','higher_arity','joint_carrier','context_conditioned','intervention_conditioned')
    G['N15_named_developmental_catalogue_absent_from_frozen_kernel']=all(re.search(r'\b'+re.escape(tok)+r'\b',executable) is None for tok in forbidden)

    tree=ast.parse(basis_text+'\n'+kernel_text)
    term_ops={
        n.args[0].value
        for n in ast.walk(tree)
        if isinstance(n,ast.Call)
        and isinstance(n.func,ast.Name)
        and n.func.id=='Term'
        and n.args
        and isinstance(n.args[0],ast.Constant)
        and isinstance(n.args[0].value,str)
    }
    G['N16_only_term_constructors_are_atom_and_nand']=term_ops=={'ATOM','NAND'}

    evidence['full_pass']=all(G.values())
    evidence['verdict']='VERIFIED_MINIMAL_ANONYMOUS_ATOM_NAND_DEVELOPMENTAL_SUBSTRATE' if evidence['full_pass'] else 'MINIMAL_NAND_V33_GAPS_EXPOSED'
    (HERE/'evidence.json').write_text(json.dumps(evidence,indent=2,sort_keys=True,default=str)+'\n')
    print(json.dumps(evidence,indent=2,sort_keys=True,default=str))
    return 0 if evidence['full_pass'] else 1

if __name__=='__main__':
    raise SystemExit(main())
