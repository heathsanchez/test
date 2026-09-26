// Included by checker.rs; uses the existing transactional signature checker.
// This is the exact nonrecursive heterogeneous identity family, not a generic
// indexed inductive rule. Neutral-major K reduction is intentionally absent.
fn heq_application(
    export: &ResolvedExport,
    expression: ExprId,
    name: NameId,
    universe: NameId,
    binders: &[u64],
) -> bool {
    let (head, args) = application_spine(export, expression);
    args.len() == binders.len()
        && is_unary_polymorphic_constant(export, head, name, universe)
        && are_bvars(export, &args, binders)
}

fn check_exact_heq(
    export: &ResolvedExport,
    environment: &Environment,
    block: &InductiveBlock,
    limits: Limits,
    delta_policy: DeltaPolicy,
) -> Result<Environment, Verdict> {
    let ([inductive], [constructor], [recursor]) = (
        block.types.as_slice(),
        block.constructors.as_slice(),
        block.recursors.as_slice(),
    ) else {
        return Err(Verdict::Unknown);
    };
    if inductive.is_unsafe
        || constructor.is_unsafe
        || recursor.is_unsafe
        || inductive.is_recursive
        || inductive.is_reflexive
        || inductive.num_nested != 0
    {
        return Err(Verdict::Unknown);
    }
    let [u] = inductive.level_params.as_slice() else {
        return Err(Verdict::Unknown);
    };
    let [v, rec_u] = recursor.level_params.as_slice() else {
        return Err(Verdict::Unknown);
    };
    if u != rec_u
        || u == v
        || inductive.num_params != 2
        || inductive.num_indices != 2
        || inductive.all != [inductive.name]
        || inductive.constructors != [constructor.name]
        || constructor.inductive != inductive.name
        || constructor.index != 0
        || constructor.num_params != 2
        || constructor.num_fields != 0
        || constructor.level_params != inductive.level_params
        || !name_is_child_str(export, constructor.name, inductive.name, "refl")
        || !recursor_metadata_admissible(
            export,
            inductive,
            &block.constructors,
            recursor,
            true,
            true,
        )
    {
        return Err(Verdict::Reject);
    }
    let Some((type_domains, type_result)) = pi_spine(export, inductive.ty, 4) else {
        return Err(Verdict::Reject);
    };
    if !is_sort_parameter(export, type_domains[0], *u)
        || !is_bvar(export, type_domains[1], 0)
        || !is_sort_parameter(export, type_domains[2], *u)
        || !is_bvar(export, type_domains[3], 0)
        || !is_prop_sort(export, type_result)
    {
        return Err(Verdict::Reject);
    }
    let Some((ctor_domains, ctor_result)) = pi_spine(export, constructor.ty, 2) else {
        return Err(Verdict::Reject);
    };
    if !is_sort_parameter(export, ctor_domains[0], *u)
        || !is_bvar(export, ctor_domains[1], 0)
        || !heq_application(export, ctor_result, inductive.name, *u, &[1, 0, 1, 0])
    {
        return Err(Verdict::Reject);
    }
    let Some((rec_domains, rec_result)) = pi_spine(export, recursor.ty, 7) else {
        return Err(Verdict::Reject);
    };
    if !is_sort_parameter(export, rec_domains[0], *u)
        || !is_bvar(export, rec_domains[1], 0)
        || !is_sort_parameter(export, rec_domains[4], *u)
        || !is_bvar(export, rec_domains[5], 0)
        || !heq_application(export, rec_domains[6], inductive.name, *u, &[5, 4, 1, 0])
    {
        return Err(Verdict::Reject);
    }
    let Some((motive_domains, motive_result)) = pi_spine(export, rec_domains[2], 3) else {
        return Err(Verdict::Reject);
    };
    if !is_sort_parameter(export, motive_domains[0], *u)
        || !is_bvar(export, motive_domains[1], 0)
        || !heq_application(export, motive_domains[2], inductive.name, *u, &[3, 2, 1, 0])
        || !is_sort_parameter(export, motive_result, *v)
    {
        return Err(Verdict::Reject);
    }
    let (minor_head, minor_args) = application_spine(export, rec_domains[3]);
    if !is_bvar(export, minor_head, 0)
        || minor_args.len() != 3
        || !are_bvars(export, &minor_args[..2], &[2, 1])
        || !heq_application(export, minor_args[2], constructor.name, *u, &[2, 1])
    {
        return Err(Verdict::Reject);
    }
    let (result_head, result_args) = application_spine(export, rec_result);
    if !is_bvar(export, result_head, 4) || !are_bvars(export, &result_args, &[2, 1, 0]) {
        return Err(Verdict::Reject);
    }
    let [rule] = recursor.rules.as_slice() else {
        return Err(Verdict::Reject);
    };
    let Some((rule_domains, rule_result)) = lam_spine(export, rule.rhs, 4) else {
        return Err(Verdict::Reject);
    };
    if rule.constructor != constructor.name
        || rule.num_fields != 0
        || rule_domains.as_slice() != &rec_domains[..4]
        || !is_bvar(export, rule_result, 0)
    {
        return Err(Verdict::Reject);
    }
    let mut derivation = ClosedNonrecursiveDerivation::begin(environment);
    derivation.promote_all(
        export,
        [
            derived_polymorphic_type(inductive.name, &inductive.level_params, inductive.ty),
            derived_constructor(constructor),
            derived_recursor(recursor),
        ],
        limits.judgment_steps,
        delta_policy,
    )?;
    install_certified_recursor_reduction(derivation.finish(), &block.constructors, recursor)
}
