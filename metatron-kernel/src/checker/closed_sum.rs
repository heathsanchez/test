//! Bounded closed sums: no parameters, dependencies, indices or recursion.
//! Every field is checked in the prior environment with an empty local frame.
//! Only after the full telescope and rule contracts hold is iota installed.
use super::*;

pub(super) fn candidate(export: &ResolvedExport, block: &InductiveBlock) -> bool {
    let ([i], [r]) = (block.types.as_slice(), block.recursors.as_slice()) else {
        return false;
    };
    (2..=3).contains(&block.constructors.len())
        && i.num_params == 0 && i.num_indices == 0 && i.num_nested == 0
        && i.level_params.is_empty() && !i.is_recursive && !i.is_reflexive && !i.is_unsafe
        && !r.is_unsafe
        && block.constructors.iter().all(|c| !c.is_unsafe && c.num_params == 0
            && c.num_fields <= 4 && c.level_params.is_empty())
        && matches!(export.exprs.get(i.ty), Some(Expr::Sort(l))
            if exported_level_is_definitely_nonzero(export, *l, 128))
}

pub(super) fn check(
    export: &ResolvedExport, prior: &Environment, block: &InductiveBlock,
    limits: Limits, delta_policy: DeltaPolicy,
) -> Result<Environment, Verdict> {
    if !candidate(export, block) { return Err(Verdict::Unknown); }
    let i=&block.types[0];
    let r=&block.recursors[0];
    if !inductive_arity_metadata_is_well_formed(export, i)
        || i.all != [i.name]
        || i.constructors != block.constructors.iter().map(|c| c.name).collect::<Vec<_>>()
        || !recursor_metadata_admissible(export, i, &block.constructors, r, false,
            r.level_params.len() == 1)
        || !block.constructors.iter().enumerate().all(|(j,c)|
            c.index == j as u64 && c.inductive == i.name
            && !generic_nonrecursive_constructor_result_is_definitely_malformed(export,i,c))
    { return Err(Verdict::Unknown); }

    // No new inductive/constructor/recursor authority is available here.
    // Checking each annotation at the same nonzero universe also establishes
    // that it is a closed type, so conversion needs no invented local context.
    let checker=TypeChecker::new(&export.exprs,&export.levels,prior)
        .with_delta_policy(delta_policy);
    let universe=TypeValue::Term(checker.closure(i.ty,EnvFrame::empty()));
    let closed_field=|field: ExprId| {
        !expression_contains_constant(export,field,i.name)
            && matches!(checker.check(field,&universe,limits.judgment_steps),Judgment::Proven { .. })
    };
    let field_equal=|a: ExprId,b: ExprId| {
        closed_field(a) && closed_field(b)
            && (expr_eq_with_bvar_shift(export,a,b,0,0)
                || matches!(checker.convert(
                    &TypeValue::Term(checker.closure(a,EnvFrame::empty())),
                    &TypeValue::Term(checker.closure(b,EnvFrame::empty())),
                    limits.judgment_steps),Judgment::Proven { .. }))
    };
    if !generic_nonrecursive_recursor_shape_with_fields(export,i,&block.constructors,r,
        |_,_,a,b| field_equal(a,b))
    { return Err(Verdict::Unknown); }

    let c=block.constructors.len();
    let Some((rec_domains,_))=pi_spine(export,r.ty,c+2) else { return Err(Verdict::Unknown); };
    for (ctor,rule) in block.constructors.iter().zip(&r.rules) {
        let f=ctor.num_fields as usize; // bounded above by candidate
        let Some((fields,_))=pi_spine(export,ctor.ty,f) else { return Err(Verdict::Unknown); };
        let Some((annotations,_))=lam_spine(export,rule.rhs,1+c+f) else { return Err(Verdict::Unknown); };
        if !rec_domains[..1+c].iter().zip(&annotations[..1+c]).all(|(a,b)|
            expr_eq_with_bvar_shift(export,*a,*b,0,0))
            || !fields.iter().zip(&annotations[1+c..]).all(|(a,b)|field_equal(*a,*b))
        { return Err(Verdict::Unknown); }
    }

    let mut d=ClosedNonrecursiveDerivation::begin(prior);
    d.promote(export,derived_type(i.name,i.ty),limits.judgment_steps,delta_policy)?;
    for ctor in &block.constructors {
        d.promote(export,derived_constructor(ctor),limits.judgment_steps,delta_policy)?;
    }
    d.promote(export,derived_recursor(r),limits.judgment_steps,delta_policy)?;
    // A sum has no structure projection or structure eta authority.
    install_certified_recursor_reduction(d.finish(),&block.constructors,r)
}
