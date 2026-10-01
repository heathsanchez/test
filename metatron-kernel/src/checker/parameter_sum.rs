//! Two-constructor sums of one or two Type parameters. Each constructor has
//! at most one field, whose type is exactly one of those parameters.
use super::*;

pub(super) fn candidate(block: &InductiveBlock) -> bool {
    let ([i],[r])=(block.types.as_slice(),block.recursors.as_slice()) else { return false; };
    block.constructors.len()==2 && (1..=2).contains(&i.num_params)
        && i.level_params.len()==i.num_params as usize
        && !has_duplicate_parameter(&i.level_params)
        && i.num_indices==0 && i.num_nested==0
        && !i.is_recursive && !i.is_reflexive && !i.is_unsafe && !r.is_unsafe
        && block.constructors.iter().all(|c| !c.is_unsafe && c.num_fields<=1
            && c.num_params==i.num_params && c.level_params==i.level_params)
}

pub(super) fn check(
    export: &ResolvedExport, prior: &Environment, block: &InductiveBlock,
    limits: Limits, delta_policy: DeltaPolicy,
) -> Result<Environment,Verdict> {
    if !candidate(block) { return Err(Verdict::Unknown); }
    let i=&block.types[0];let r=&block.recursors[0];let p=i.num_params as usize;
    let Some((params,result))=pi_spine(export,i.ty,p) else { return Err(Verdict::Unknown); };
    if !params.iter().zip(&i.level_params).all(|(ty,u)|is_sort_succ_parameter(export,*ty,*u)) {
        return Err(Verdict::Unknown);
    }
    let result_ok=if p==1 {
        is_sort_succ_parameter(export,result,i.level_params[0])
    } else {
        BinaryProductSortLaw::Prod { first:i.level_params[0],second:i.level_params[1] }
            .result_sort(export,result)
    };
    if !result_ok || !inductive_arity_metadata_is_well_formed(export,i)
        || i.all != [i.name]
        || i.constructors != block.constructors.iter().map(|c|c.name).collect::<Vec<_>>()
        || !recursor_metadata_admissible(export,i,&block.constructors,r,false,
            r.level_params.len()==p+1 && r.level_params.get(1..)==Some(i.level_params.as_slice()))
    { return Err(Verdict::Unknown); }

    for (j,c) in block.constructors.iter().enumerate() {
        let f=c.num_fields as usize;
        let Some((domains,_))=pi_spine(export,c.ty,p+f) else { return Err(Verdict::Unknown); };
        if c.index!=j as u64 || c.inductive!=i.name
            || domains[..p]!=params[..]
            || generic_nonrecursive_constructor_result_is_definitely_malformed(export,i,c)
            || !domains[p..].iter().all(|ty|
                matches!(export.exprs.get(*ty),Some(Expr::BVar(k)) if *k < p as u64))
        { return Err(Verdict::Unknown); }
    }
    if !generic_nonrecursive_recursor_shape(export,i,&block.constructors,r) {
        return Err(Verdict::Unknown);
    }
    let outer=p+1+block.constructors.len();
    let Some((rec_domains,_))=pi_spine(export,r.ty,outer+1) else { return Err(Verdict::Unknown); };
    for (c,rule) in block.constructors.iter().zip(&r.rules) {
        let f=c.num_fields as usize;
        let Some((ctor_domains,_))=pi_spine(export,c.ty,p+f) else { return Err(Verdict::Unknown); };
        let Some((annotations,_))=lam_spine(export,rule.rhs,outer+f) else { return Err(Verdict::Unknown); };
        if !rec_domains[..outer].iter().zip(&annotations[..outer]).all(|(a,b)|
            expr_eq_with_bvar_shift(export,*a,*b,0,0))
            || !ctor_domains[p..].iter().zip(&annotations[outer..]).enumerate().all(|(k,(a,b))|
                expr_eq_with_bvar_shift(export,*a,*b,k as u64,3))
        { return Err(Verdict::Unknown); }
    }
    let mut d=ClosedNonrecursiveDerivation::begin(prior);
    d.promote(export,derived_polymorphic_type(i.name,&i.level_params,i.ty),limits.judgment_steps,delta_policy)?;
    for c in &block.constructors {
        d.promote(export,derived_constructor(c),limits.judgment_steps,delta_policy)?;
    }
    d.promote(export,derived_recursor(r),limits.judgment_steps,delta_policy)?;
    install_certified_recursor_reduction(d.finish(),&block.constructors,r)
}
