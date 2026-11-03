"""Two-owner carrier experiment on the previously qualified canonical K stack.

This only routes a source-identified inductive family through Nucleus's
existing generic derived signature checker, with an additional independent
source-field and recursor obligation. All previous controls rerun fresh.
"""

import difflib
import importlib.util
import json
from pathlib import Path
import subprocess


ROOT = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location(
    'max_one_qualification', ROOT.parent / 'nucleus-ac-max1-20261104/qualify.py')
MAX1 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(MAX1)
C, Q = MAX1.C, MAX1.Q
OUT = Path('/tmp/nucleus-two-universe-qualified')
SOURCE_SHA = 'f37e9434b2cee5f9623a2218fb6418c58d43dbe5ac3582cadd9cc844dfa215b4'
PRIOR_BINARY_SHA = 'e05ddf3ef929955396ff484864a4270a2b3ed8f363d824c047bd6ecb4ab9dacd'
PRIOR_PATCH_SHA = '3fddbcc9fc323e737a51eea5d5f287b6e92f649db362cd2ddc147815128c1437'


def extend_two_universe_source(kernel, arm):
    """Exact structural `max(max(1,u),v)` rule, never a name exception."""
    path = kernel/'src/checker.rs'
    before = path.read_text()
    helper = '''// The two owners are independently scoped; this matches a source
// universe form, not a declaration name or a trusted proof-result cache.
fn is_two_owner_record_carrier(export:&ResolvedExport,expression:ExprId,u:NameId,v:NameId)->bool {
    let Some(Expr::Sort(l))=export.exprs.get(expression) else {return false;};
    let Some(Level::Max(left,right))=export.levels.get(*l) else {return false;};
    let Some(Level::Max(one,first))=export.levels.get(*left) else {return false;};
    matches!(export.levels.get(*one),Some(Level::Succ(zero)) if matches!(export.levels.get(*zero),Some(Level::Zero)))
        && matches!(export.levels.get(*first),Some(Level::Param(n)) if *n==u)
        && matches!(export.levels.get(*right),Some(Level::Param(n)) if *n==v)
}

fn two_owner_record_candidate(export:&ResolvedExport,block:&InductiveBlock)->bool {
    let ([inductive],[constructor],[recursor])=(block.types.as_slice(),block.constructors.as_slice(),block.recursors.as_slice()) else {return false;};
    let [u,v]=inductive.level_params.as_slice() else {return false;};
    if inductive.num_params!=2 || constructor.num_params!=2 || !(2..=16).contains(&constructor.num_fields)
        || inductive.num_indices!=0 || inductive.num_nested!=0 || inductive.is_recursive
        || inductive.is_reflexive || inductive.is_unsafe || constructor.is_unsafe || recursor.is_unsafe
        || recursor.k || recursor.num_params!=2 || recursor.num_indices!=0
        || recursor.num_minors!=1 || recursor.num_motives!=1 || recursor.level_params.len()!=3
        || recursor.rules.len()!=1 {return false;}
    let Some((params,result))=pi_spine(export,inductive.ty,2) else {return false;};
    if !is_sort_parameter(export,params[0],*u) || !is_sort_parameter(export,params[1],*v)
        || !is_two_owner_record_carrier(export,result,*u,*v) {return false;}
    let Some((domains,_))=pi_spine(export,constructor.ty,2+constructor.num_fields as usize) else {return false;};
    params.iter().zip(&domains[..2]).all(|(p,c)|expr_eq_with_bvar_shift(export,*p,*c,0,0))
        && domains[2..].iter().all(|field|!expression_contains_constant(export,*field,inductive.name))
}

fn two_owner_record_obligations(export:&ResolvedExport,environment:&Environment,block:&InductiveBlock,limits:Limits,policy:DeltaPolicy)->bool {
    let ([inductive],[constructor],[recursor])=(block.types.as_slice(),block.constructors.as_slice(),block.recursors.as_slice()) else {return false;};
    let p=2usize; let count=constructor.num_fields as usize;
    let Some((_,result))=pi_spine(export,inductive.ty,p) else {return false;};
    let Some(Expr::Sort(level))=export.exprs.get(result) else {return false;};
    let substitution=parameter_substitution(&inductive.level_params);
    let Ok(carrier)=crate::level::instantiate_level(&export.levels,*level,&substitution,limits.judgment_steps) else {return false;};
    let checker=TypeChecker::with_level_substitution(&export.exprs,&export.levels,environment,substitution).with_delta_policy(policy);
    let Some((domains,_))=pi_spine(export,constructor.ty,p+count) else {return false;};
    let mut frame=EnvFrame::empty(); let mut context=Vec::new();
    for (i,domain) in domains.iter().enumerate() {
        let Judgment::Proven{value:field_sort,..}=checker.infer_sort_in_context(*domain,&context,&frame,limits.judgment_steps) else {return false;};
        if i>=p && !crate::level::level_equal(crate::level::max(field_sort,carrier.clone()),carrier.clone(),limits.judgment_steps).is_proven() {return false;}
        context.push(TypeValue::Term(checker.closure(*domain,frame.clone())));
        frame=frame.extend_free(FreeId(i as u64));
    }
    let prefix=p+2;
    let Some((rec_domains,_))=pi_spine(export,recursor.ty,prefix+1) else {return false;};
    let [rule]=recursor.rules.as_slice() else {return false;};
    let Some((annotations,_))=lam_spine(export,rule.rhs,prefix+count) else {return false;};
    rec_domains[..prefix].iter().zip(&annotations[..prefix]).all(|(a,b)|expr_eq_with_bvar_shift(export,*a,*b,0,0))
        && domains[p..].iter().zip(&annotations[prefix..]).enumerate().all(|(k,(a,b))|
            expr_eq_with_bvar_shift(export,*a,*b,k as u64,2)
                || expr_eq_with_bvar_shift(export,checked_erased_closed_field(export,environment,*a),*b,k as u64,2))
}

'''
    candidate_start='fn generic_nonrecursive_type_candidate(export: &ResolvedExport, block: &InductiveBlock) -> bool {'
    assert before.count(candidate_start)==1
    changed=before.replace(candidate_start,helper+candidate_start,1)
    unary='    let unary_type_constructor_operations =\n        unary_type_constructor_operation_record_candidate(export, block);'
    assert changed.count(unary)==1
    changed=changed.replace(unary,unary+'\n    let two_owner_record = two_owner_record_candidate(export,block);',1)
    guard='        && !unary_type_constructor_operations\n'
    assert changed.count(guard)==1
    changed=changed.replace(guard,guard+'        && !two_owner_record\n',1)
    # Canonical-K's source hardening routes the obligation through the
    # separately checked `scope` predicate. Anchor the actual qualified tree.
    obligation='    if parameter_record_scope(export,block) && !parameter_record_obligations(export,environment,block,limits,delta_policy) {return Err(Verdict::Unknown);}'
    assert changed.count(obligation)==1
    changed=changed.replace(obligation,obligation+'\n    if two_owner_record_candidate(export,block) && !two_owner_record_obligations(export,environment,block,limits,delta_policy) {return Err(Verdict::Unknown);}',1)
    assert changed!=before
    path.write_text(changed)
    diff=''.join(difflib.unified_diff(before.splitlines(True),changed.splitlines(True),
        fromfile='a/metatron-kernel/src/checker.rs',tofile='b/metatron-kernel/src/checker.rs'))
    (arm/'two-owner-source.patch').write_text(diff)
    with (arm/'source.patch').open('a') as stream:stream.write(diff)


def new_gate(binary,env):
    # Re-run the earlier three differential control suites against THIS binary.
    MAX1.new_gate(binary,env)
    source=Path('/tmp/evalinfo-prefix.ndjson')
    assert Q.t.digest(source)==SOURCE_SHA
    old=Path('/tmp/max1-prior/candidate/nucleus')
    assert Q.t.digest(old)==PRIOR_BINARY_SHA
    prior=json.loads(Path('/tmp/max1-prior/max1_qualification.json').read_text())
    assert prior['status']=='WARRANTED_BOUNDED' and prior['candidate_patch_sha']==PRIOR_PATCH_SHA
    old.chmod(0o755)
    red=Q.t.measure(old,source,env,OUT/'red-two',timeout=180,perf=False)
    assert red['rc']==2 and 'Lean.Data.AC.EvalInformation' in (OUT/'red-two/stderr').read_text()
    cases=OUT/'two-inputs'
    subprocess.run(['python3',str(ROOT/'generate.py'),
                    '--source',str(source),'--out',str(cases)],check=True)
    manifest=json.loads((cases/'inputs.json').read_text())
    assert len(manifest)==10
    reference=Path('/tmp/k-reference/bundle/kernel')
    assert Q.t.digest(reference)==C.REF_SHA
    rows=[]
    for case in manifest:
        fixture=cases/case['file']
        assert Q.t.digest(fixture)==case['sha256']
        stem=OUT/'two-differential'/case['case']
        parse=C.captured([str(reference),'--parse-only',str(fixture)],stem/'parse')
        official=C.captured([str(reference),str(fixture)],stem/'reference')
        with fixture.open('rb') as source_file:
            candidate=C.captured([str(binary)],stem/'nucleus',env=env,stdin=source_file)
        passed=parse==0 and official==case['expect_reference'] and (candidate==0 if official==0 else candidate in (1,2))
        rows.append(dict(case,reference_parse_rc=parse,reference_rc=official,
                         nucleus_rc=candidate,pass_=passed))
        Q.t.write_json(OUT/'two_gate.json',{'source_sha':SOURCE_SHA,
                         'candidate_binary':Q.t.digest(binary), 'red':red,'rows':rows})
        print('TWO_SOURCE_CONTROL',json.dumps(rows[-1]),flush=True)
        assert passed,'Two-owner official Lean differential control failed'


def main():
    OUT.mkdir(exist_ok=True)
    C.OUT=OUT
    MAX1.OUT=OUT
    source_patch=ROOT.parent/'nucleus-ac-sort-20261104/sort-carrier.patch'
    C.main(additional_patch=[source_patch,MAX1.extend_max_one_source,extend_two_universe_source],
           additional_gate=new_gate)
    protected=json.loads((OUT/'qualification.json').read_text())['candidate']
    full=json.loads((OUT/'full.json').read_text())
    gate=json.loads((OUT/'two_gate.json').read_text())
    assert protected['qualified'] and full['qualified']
    assert len(gate['rows'])==10 and all(x['pass_'] for x in gate['rows'])
    report={'status':'WARRANTED_BOUNDED','source_sha':SOURCE_SHA,
            'official_two_controls':10,'retained_max_one_controls':9,
            'retained_ac_controls':9,'retained_canonical_k_controls':12,
            'candidate_binary_sha':protected['binary_sha'],
            'candidate_patch_sha':protected['source_patch_sha'],
            'native_nonregression':protected['native_nonregression'],
            'source_controls_unchanged':protected['controls_unchanged'],
            'arena_verdict_changes':protected['verdict_changes'],
            'complete_mathlib_accept':full['complete_mathlib_accept'],
            'terminal':full['terminal'],'next_frontier':full['next_frontier']}
    Q.t.write_json(OUT/'two_qualification.json',report)
    print('TWO_PROTECTED_QUALIFICATION',json.dumps(report),flush=True)


if __name__=='__main__':
    main()
