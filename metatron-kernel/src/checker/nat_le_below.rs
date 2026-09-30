//! Exact Prop-valued course-of-values family for the already certified Nat.le.
//! No general indexed positivity, K, or large elimination is inferred here.
use super::*;

// Named binders describe the mathematical schema only; exported binder names
// are ignored. Matching resolves each schema variable to its de Bruijn index.
#[derive(Clone)]
enum Shape {
    Var(&'static str),
    Const(NameId),
    Prop,
    App(Box<Shape>, Box<Shape>),
    Pi(&'static str, Box<Shape>, Box<Shape>),
    Lam(&'static str, Box<Shape>, Box<Shape>),
}
use Shape::{Const as c, Prop, Var as v};
fn ap(mut head: Shape, args: impl IntoIterator<Item = Shape>) -> Shape {
    for arg in args {
        head = Shape::App(Box::new(head), Box::new(arg));
    }
    head
}
fn bind(fields: Vec<(&'static str, Shape)>, mut body: Shape, lambda: bool) -> Shape {
    for (name, domain) in fields.into_iter().rev() {
        body = if lambda {
            Shape::Lam(name, Box::new(domain), Box::new(body))
        } else {
            Shape::Pi(name, Box::new(domain), Box::new(body))
        };
    }
    body
}
fn pi(fields: Vec<(&'static str, Shape)>, body: Shape) -> Shape {
    bind(fields, body, false)
}
fn lam(fields: Vec<(&'static str, Shape)>, body: Shape) -> Shape {
    bind(fields, body, true)
}
fn matches(
    export: &ResolvedExport,
    expr: ExprId,
    shape: &Shape,
    scope: &mut Vec<&'static str>,
) -> bool {
    match (export.exprs.get(expr), shape) {
        (Some(Expr::BVar(i)), Shape::Var(name)) => scope
            .iter()
            .rev()
            .position(|s| s == name)
            .is_some_and(|index| u64::try_from(index) == Ok(*i)),
        (Some(Expr::Const { name, levels }), Shape::Const(expected)) => {
            name == expected && levels.is_empty()
        }
        (Some(Expr::Sort(l)), Shape::Prop) => matches!(export.levels.get(*l), Some(Level::Zero)),
        (Some(Expr::App { fun, arg }), Shape::App(f, a)) => {
            matches(export, *fun, f, scope) && matches(export, *arg, a, scope)
        }
        (Some(Expr::Pi { domain, body }), Shape::Pi(name, d, b))
        | (Some(Expr::Lam { domain, body }), Shape::Lam(name, d, b)) => {
            if !matches(export, *domain, d, scope) {
                return false;
            }
            scope.push(name);
            let result = matches(export, *body, b, scope);
            scope.pop();
            result
        }
        _ => false,
    }
}

pub(super) fn check(
    export: &ResolvedExport,
    environment: &Environment,
    block: &InductiveBlock,
    limits: Limits,
    delta_policy: DeltaPolicy,
) -> Result<Environment, Verdict> {
    let ([ind], [refl, step], [rec]) = (
        block.types.as_slice(),
        block.constructors.as_slice(),
        block.recursors.as_slice(),
    ) else {
        return Err(Verdict::Unknown);
    };
    let Some(nat) = environment.nat_primitives() else {
        return Err(Verdict::Unknown);
    };
    let Some(Name::Str { prefix: le, value }) = export.names.get(ind.name) else {
        return Err(Verdict::Unknown);
    };
    if value != "below" || !name_is_child_str(export, *le, nat.type_name, "le") {
        return Err(Verdict::Unknown);
    }
    let Some(le_refl) = quotient_child(export, *le, "refl") else {
        return Err(Verdict::Unknown);
    };
    let Some(le_step) = quotient_child(export, *le, "step") else {
        return Err(Verdict::Unknown);
    };
    let Some(le_rec) = quotient_child(export, *le, "rec") else {
        return Err(Verdict::Unknown);
    };
    let reductions = environment.recursor_reductions();
    let Some(prior) = reductions.get(&le_rec) else {
        return Err(Verdict::Unknown);
    };
    // A matching name or an axiom with the right type cannot stand in for the
    // previously checked inductive and its certified recursive computation.
    if prior.eq_k
        || prior.num_params != 1
        || prior.num_indices != 1
        || prior.rules.len() != 2
        || prior.rules[0].constructor != le_refl
        || prior.rules[1].constructor != le_step
        || !environment
            .get(*le)
            .is_some_and(|d| nat_le_type(export, d.ty, nat.type_name))
        || !environment
            .get(le_refl)
            .is_some_and(|d| nat_le_refl_type(export, d.ty, nat.type_name, *le))
        || !environment
            .get(le_step)
            .is_some_and(|d| nat_le_step_type(export, d.ty, nat.type_name, nat.succ, *le))
    {
        return Err(Verdict::Unknown);
    }
    if ind.num_params != 2
        || ind.num_indices != 2
        || ind.num_nested != 0
        || !ind.is_recursive
        || ind.is_reflexive
        || ind.is_unsafe
        || !ind.level_params.is_empty()
        || ind.all != [ind.name]
        || ind.constructors != [refl.name, step.name]
        || refl.is_unsafe
        || step.is_unsafe
        || rec.is_unsafe
        || !refl.level_params.is_empty()
        || !step.level_params.is_empty()
        || !rec.level_params.is_empty()
        || refl.index != 0
        || step.index != 1
        || refl.inductive != ind.name
        || step.inductive != ind.name
        || refl.num_params != 2
        || step.num_params != 2
        || refl.num_fields != 0
        || step.num_fields != 4
        || !name_is_child_str(export, refl.name, ind.name, "refl")
        || !name_is_child_str(export, step.name, ind.name, "step")
        || !recursor_metadata_admissible(export, ind, &block.constructors, rec, false, true)
    {
        return Err(Verdict::Unknown);
    }

    let le_at = |n, m| ap(c(*le), [n, m]);
    let below = |m, h| ap(c(ind.name), [v("n"), v("P"), m, h]);
    let motive = pi(
        vec![("m", c(nat.type_name)), ("h", le_at(v("n"), v("m")))],
        Prop,
    );
    let params = vec![("n", c(nat.type_name)), ("P", motive)];
    let indices = vec![("m", c(nat.type_name)), ("h", le_at(v("n"), v("m")))];
    let refl_proof = ap(c(le_refl), [v("n")]);
    let step_proof = ap(c(le_step), [v("n"), v("m"), v("h")]);
    let succ = ap(c(nat.succ), [v("m")]);
    let refl_term = ap(c(refl.name), [v("n"), v("P")]);
    let step_fields = vec![
        ("m", c(nat.type_name)),
        ("h", le_at(v("n"), v("m"))),
        ("b", below(v("m"), v("h"))),
        ("p", ap(v("P"), [v("m"), v("h")])),
    ];
    let step_term = ap(
        c(step.name),
        [v("n"), v("P"), v("m"), v("h"), v("b"), v("p")],
    );
    let q = pi(
        [indices.clone(), vec![("t", below(v("m"), v("h")))]].concat(),
        Prop,
    );
    let refl_minor = ap(v("Q"), [v("n"), refl_proof.clone(), refl_term]);
    let step_minor = pi(
        [
            step_fields.clone(),
            vec![("ih", ap(v("Q"), [v("m"), v("h"), v("b")]))],
        ]
        .concat(),
        ap(v("Q"), [succ.clone(), step_proof.clone(), step_term]),
    );
    let prefix = [
        params.clone(),
        vec![("Q", q), ("r", refl_minor), ("s", step_minor)],
    ]
    .concat();
    let call = ap(
        c(rec.name),
        [
            v("n"),
            v("P"),
            v("Q"),
            v("r"),
            v("s"),
            v("m"),
            v("h"),
            v("b"),
        ],
    );
    let obligations = [
        (ind.ty, pi([params.clone(), indices.clone()].concat(), Prop)),
        (refl.ty, pi(params.clone(), below(v("n"), refl_proof))),
        (
            step.ty,
            pi(
                [params, step_fields.clone()].concat(),
                below(succ, step_proof),
            ),
        ),
        (
            rec.ty,
            pi(
                [prefix.clone(), indices, vec![("t", below(v("m"), v("h")))]].concat(),
                ap(v("Q"), [v("m"), v("h"), v("t")]),
            ),
        ),
        (rec.rules[0].rhs, lam(prefix.clone(), v("r"))),
        (
            rec.rules[1].rhs,
            lam(
                [prefix, step_fields].concat(),
                ap(v("s"), [v("m"), v("h"), v("b"), v("p"), call]),
            ),
        ),
    ];
    if !obligations
        .iter()
        .all(|(expr, shape)| matches(export, *expr, shape, &mut Vec::new()))
    {
        return Err(Verdict::Unknown);
    }
    let mut d = ClosedNonrecursiveDerivation::begin(environment);
    d.promote_all(
        export,
        [
            derived_type(ind.name, ind.ty),
            derived_constructor(refl),
            derived_constructor(step),
            derived_recursor(rec),
        ],
        limits.judgment_steps,
        delta_policy,
    )?;
    install_certified_recursor_reduction(d.finish(), &block.constructors, rec)
}
