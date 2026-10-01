//! Bounded nonrecursive Type records, validated in their actual telescope.
//! No authority is installed until field universes and every rule contract hold.
use super::*;

pub(super) fn candidate(export: &ResolvedExport, block: &InductiveBlock) -> bool {
    let ([i],[c],[r])=(block.types.as_slice(),block.constructors.as_slice(),block.recursors.as_slice()) else { return false; };
    let Some((_,result))=pi_spine(export,i.ty,i.num_params as usize) else { return false; };
    (1..=4).contains(&i.num_params) && c.num_fields<=3 && i.level_params.len()<=3
        && i.num_indices==0 && i.num_nested==0 && !i.is_recursive && !i.is_reflexive
        && !i.is_unsafe && !c.is_unsafe && !r.is_unsafe
        && c.num_params==i.num_params && c.level_params==i.level_params
        && !has_duplicate_parameter(&i.level_params) && !has_duplicate_parameter(&r.level_params)
        && matches!(export.exprs.get(result),Some(Expr::Sort(l))
            if exported_level_is_definitely_nonzero(export,*l,128))
}

pub(super) fn check(export: &ResolvedExport, prior: &Environment, block: &InductiveBlock,
    limits: Limits, delta_policy: DeltaPolicy) -> Result<Environment,Verdict> {
    if !candidate(export,block) { return Err(Verdict::Unknown); }
    let i=&block.types[0];let c=&block.constructors[0];let r=&block.recursors[0];
    let p=i.num_params as usize;let f=c.num_fields as usize;
    if !inductive_arity_metadata_is_well_formed(export,i) || i.all!=[i.name]
        || i.constructors!=[c.name] || c.index!=0 || c.inductive!=i.name
        || generic_nonrecursive_constructor_result_is_definitely_malformed(export,i,c)
        || !recursor_metadata_admissible(export,i,&block.constructors,r,false,
            r.level_params.len()==i.level_params.len()+1
                && r.level_params.get(1..)==Some(i.level_params.as_slice()))
    { return Err(Verdict::Unknown); }
    let Some((params,result))=pi_spine(export,i.ty,p) else { return Err(Verdict::Unknown); };
    let Some((domains,_))=pi_spine(export,c.ty,p+f) else { return Err(Verdict::Unknown); };
    let Some(Expr::Sort(result_level))=export.exprs.get(result) else { return Err(Verdict::Unknown); };
    let substitution=parameter_substitution(&r.level_params);
    let result_universe=crate::level::instantiate_level(&export.levels,*result_level,&substitution,limits.judgment_steps)
        .map_err(|_|Verdict::Unknown)?;
    let checker=TypeChecker::with_level_substitution(&export.exprs,&export.levels,prior,substitution)
        .with_delta_policy(delta_policy);
    let equal=|a,b,context: &[TypeValue],frame: &EnvFrame| {
        matches!(crate::convert::convert_with_policy_in_context(&checker,
            &TypeValue::Term(checker.closure(a,frame.clone())),
            &TypeValue::Term(checker.closure(b,frame.clone())),limits.judgment_steps,
            delta_policy,context.len(),context),Judgment::Proven { .. })
    };
    let mut context=Vec::new();let mut frame=EnvFrame::empty();let mut prefixes=Vec::new();
    for (k,ty) in params.iter().copied().enumerate() {
        if expression_contains_constant(export,ty,i.name)
            || !matches!(checker.infer_sort_in_context(ty,&context,&frame,limits.judgment_steps),Judgment::Proven { .. })
            || !equal(ty,domains[k],&context,&frame) { return Err(Verdict::Unknown); }
        prefixes.push((context.clone(),frame.clone()));
        context.push(TypeValue::Term(checker.closure(ty,frame.clone())));
        frame=frame.extend_free(FreeId(k as u64));
    }
    for ty in domains[p..].iter().copied() {
        if expression_contains_constant(export,ty,i.name) { return Err(Verdict::Unknown); }
        let Judgment::Proven { value:field_universe,.. }=checker.infer_sort_in_context(ty,&context,&frame,limits.judgment_steps)
            else { return Err(Verdict::Unknown); };
        if !matches!(crate::level::level_equal(crate::level::max(field_universe,result_universe.clone()),
            result_universe.clone(),limits.judgment_steps),Judgment::Proven { .. }) { return Err(Verdict::Unknown); }
        let depth=context.len();
        context.push(TypeValue::Term(checker.closure(ty,frame.clone())));
        frame=frame.extend_free(FreeId(depth as u64));
    }
    if !generic_nonrecursive_recursor_shape_with_checks(export,i,&block.constructors,r,
        |k,a,b|equal(a,b,&prefixes[k].0,&prefixes[k].1),
        |_,k,a,b|expr_eq_with_bvar_shift(export,a,b,k as u64,1)) { return Err(Verdict::Unknown); }
    let Some((rec_domains,_))=pi_spine(export,r.ty,p+3) else { return Err(Verdict::Unknown); };
    let Some((annotations,_))=lam_spine(export,r.rules[0].rhs,p+2+f) else { return Err(Verdict::Unknown); };
    if !(0..p).all(|k|equal(rec_domains[k],annotations[k],&prefixes[k].0,&prefixes[k].1))
        || !(p..p+2).all(|k|expr_eq_with_bvar_shift(export,rec_domains[k],annotations[k],0,0))
        || !domains[p..].iter().zip(&annotations[p+2..]).enumerate().all(|(k,(a,b))|
            expr_eq_with_bvar_shift(export,*a,*b,k as u64,2)) { return Err(Verdict::Unknown); }
    let mut d=ClosedNonrecursiveDerivation::begin(prior);
    d.promote(export,derived_polymorphic_type(i.name,&i.level_params,i.ty),limits.judgment_steps,delta_policy)?;
    d.promote(export,derived_constructor(c),limits.judgment_steps,delta_policy)?;
    d.promote(export,derived_recursor(r),limits.judgment_steps,delta_policy)?;
    let environment=d.finish().install_projection_spec(i.name,ProjectionSpec {
        constructor:c.name,num_params:p,
        field_types:domains[p..].iter().copied().map(ProjectionFieldType::Derived).collect(),
    }).map_err(|_|Verdict::Unknown)?;
    install_certified_recursor_reduction(environment,&block.constructors,r)
}
