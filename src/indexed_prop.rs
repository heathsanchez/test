//! Conservative reconstruction of single indexed Prop families with direct
//! recursive fields and Prop-only elimination. No exported recursor body is
//! trusted: both its signature and every iota rule are derived independently.
use crate::id::{ExprId, LevelId, NameId};
use crate::parser::ResolvedExport;
use crate::syntax::{Expr, InductiveBlock, Level};

#[derive(Clone, Debug, PartialEq, Eq)]
enum Term {
    Local(usize),
    Bound(u64),
    Sort(LevelId),
    Const(NameId, Vec<LevelId>),
    App(Box<Term>, Box<Term>),
    Pi(Box<Term>, Box<Term>),
    Lam(Box<Term>, Box<Term>),
}

fn read(e: &ResolvedExport, id: ExprId, locals: &[Term], depth: u64, fuel: usize) -> Option<Term> {
    read_bounded(e, id, locals, depth, fuel, &mut 4096)
}

fn read_bounded(
    e: &ResolvedExport,
    id: ExprId,
    locals: &[Term],
    depth: u64,
    fuel: usize,
    nodes: &mut usize,
) -> Option<Term> {
    if fuel == 0 || *nodes == 0 {
        return None;
    }
    *nodes -= 1;
    let next = fuel - 1;
    Some(match e.exprs.get(id)? {
        Expr::BVar(i) if *i < depth => Term::Bound(*i),
        Expr::BVar(i) => locals
            .get(
                locals
                    .len()
                    .checked_sub(usize::try_from(i - depth).ok()?.checked_add(1)?)?,
            )?
            .clone(),
        Expr::Sort(l) => Term::Sort(*l),
        Expr::Const { name, levels } => Term::Const(*name, levels.clone()),
        Expr::App { fun, arg } => app(
            read_bounded(e, *fun, locals, depth, next, nodes)?,
            read_bounded(e, *arg, locals, depth, next, nodes)?,
        ),
        Expr::Pi { domain, body } => Term::Pi(
            Box::new(read_bounded(e, *domain, locals, depth, next, nodes)?),
            Box::new(read_bounded(e, *body, locals, depth + 1, next, nodes)?),
        ),
        Expr::Lam { domain, body } => Term::Lam(
            Box::new(read_bounded(e, *domain, locals, depth, next, nodes)?),
            Box::new(read_bounded(e, *body, locals, depth + 1, next, nodes)?),
        ),
        _ => return None,
    })
}

fn app(f: Term, a: Term) -> Term {
    Term::App(Box::new(f), Box::new(a))
}
fn apps(f: Term, args: impl IntoIterator<Item = Term>) -> Term {
    args.into_iter().fold(f, app)
}

fn abstract_local(t: Term, local: usize, depth: u64) -> Term {
    match t {
        Term::Local(i) if i == local => Term::Bound(depth),
        Term::App(f, a) => app(
            abstract_local(*f, local, depth),
            abstract_local(*a, local, depth),
        ),
        Term::Pi(d, b) => Term::Pi(
            Box::new(abstract_local(*d, local, depth)),
            Box::new(abstract_local(*b, local, depth + 1)),
        ),
        Term::Lam(d, b) => Term::Lam(
            Box::new(abstract_local(*d, local, depth)),
            Box::new(abstract_local(*b, local, depth + 1)),
        ),
        other => other,
    }
}

fn bind(binders: &[(usize, Term)], mut body: Term, lambda: bool) -> Term {
    for (id, domain) in binders.iter().rev() {
        let body_bound = abstract_local(body, *id, 0);
        body = if lambda {
            Term::Lam(Box::new(domain.clone()), Box::new(body_bound))
        } else {
            Term::Pi(Box::new(domain.clone()), Box::new(body_bound))
        };
    }
    body
}

fn spine(t: &Term) -> (&Term, Vec<Term>) {
    let mut head = t;
    let mut args = Vec::new();
    while let Term::App(f, a) = head {
        args.push((**a).clone());
        head = f;
    }
    args.reverse();
    (head, args)
}

fn contains(t: &Term, name: NameId) -> bool {
    match t {
        Term::Const(n, _) => *n == name,
        Term::App(a, b) | Term::Pi(a, b) | Term::Lam(a, b) => {
            contains(a, name) || contains(b, name)
        }
        _ => false,
    }
}

fn fresh(next: &mut usize) -> usize {
    let id = *next;
    *next += 1;
    id
}

fn telescope(
    e: &ResolvedExport,
    mut id: ExprId,
    count: usize,
    locals: &mut Vec<Term>,
    next: &mut usize,
) -> Option<(Vec<(usize, Term)>, ExprId)> {
    let mut binders = Vec::new();
    for _ in 0..count {
        let Expr::Pi { domain, body } = e.exprs.get(id)? else {
            return None;
        };
        let domain = read(e, *domain, locals, 0, 256)?;
        let var = fresh(next);
        binders.push((var, domain));
        locals.push(Term::Local(var));
        id = *body;
    }
    Some((binders, id))
}

/// A successful result only establishes structural contracts. The caller must
/// additionally typecheck all signatures against the preceding environment.
pub(crate) fn contracts(e: &ResolvedExport, b: &InductiveBlock) -> Option<()> {
    let [i] = b.types.as_slice() else {
        return None;
    };
    let [r] = b.recursors.as_slice() else {
        return None;
    };
    let p = usize::try_from(i.num_params).ok()?;
    let n = usize::try_from(i.num_indices).ok()?;
    let c = b.constructors.len();
    if p > 64
        || n == 0
        || n > 64
        || c < 2
        || c > 64
        || i.num_nested != 0
        || !i.is_recursive
        || i.is_reflexive
        || i.is_unsafe
        || r.is_unsafe
        || r.k
        || r.all != [i.name]
        || i.all != [i.name]
        || i.constructors != b.constructors.iter().map(|x| x.name).collect::<Vec<_>>()
        || r.level_params != i.level_params
        || r.num_params != i.num_params
        || r.num_indices != i.num_indices
        || r.num_motives != 1
        || r.num_minors != c as u64
        || r.rules.len() != c
    {
        return None;
    }
    let mut levels = Vec::new();
    for parameter in &i.level_params {
        let (id, _) = e
            .levels
            .iter_raw()
            .find(|(_, l)| matches!(l,Level::Param(name) if name==parameter))?;
        levels.push(LevelId(id));
    }
    let ind = Term::Const(i.name, levels.clone());
    let mut next = 0;
    let mut locals = Vec::new();
    let (parameters, rest) = telescope(e, i.ty, p, &mut locals, &mut next)?;
    if parameters.iter().any(|(_, t)| contains(t, i.name)) {
        return None;
    }
    let params = locals.clone();
    let (indices, result) = telescope(e, rest, n, &mut locals, &mut next)?;
    if indices.iter().any(|(_, t)| contains(t, i.name)) {
        return None;
    }
    let prop = read(e, result, &locals, 0, 256)?;
    let Term::Sort(level) = prop else {
        return None;
    };
    if !matches!(e.levels.get(level), Some(Level::Zero)) {
        return None;
    }
    let prop = Term::Sort(level);
    let index_args = indices
        .iter()
        .map(|(id, _)| Term::Local(*id))
        .collect::<Vec<_>>();
    let major = fresh(&mut next);
    let major_type = apps(
        ind.clone(),
        params.iter().cloned().chain(index_args.clone()),
    );
    let mut motive_binders = indices.clone();
    motive_binders.push((major, major_type.clone()));
    let motive = fresh(&mut next);
    let motive_type = bind(&motive_binders, prop, false);
    let mut rec_binders = parameters.clone();
    rec_binders.push((motive, motive_type));
    let mut rule_prefix = rec_binders.clone();
    let mut minor_vars = Vec::new();
    let mut ctor_data = Vec::new();
    let mut has_recursive = false;
    for (ordinal, ctor) in b.constructors.iter().enumerate() {
        if ctor.is_unsafe
            || ctor.index != ordinal as u64
            || ctor.inductive != i.name
            || ctor.num_params != i.num_params
            || ctor.level_params != i.level_params
            || ctor.num_fields > 64
        {
            return None;
        }
        let mut id = ctor.ty;
        let mut ctx = Vec::new();
        for (var, expected) in &parameters {
            let Expr::Pi { domain, body } = e.exprs.get(id)? else {
                return None;
            };
            if read(e, *domain, &ctx, 0, 256)? != *expected {
                return None;
            }
            ctx.push(Term::Local(*var));
            id = *body;
        }
        let (fields, result) = telescope(e, id, ctor.num_fields as usize, &mut ctx, &mut next)?;
        let result = read(e, result, &ctx, 0, 256)?;
        let (head, args) = spine(&result);
        if head != &ind
            || args.len() != p + n
            || args[..p] != params[..]
            || args[p..].iter().any(|t| contains(t, i.name))
        {
            return None;
        }
        let mut recursive = Vec::new();
        for (field, domain) in &fields {
            let (h, a) = spine(domain);
            if h == &ind {
                if a.len() != p + n
                    || a[..p] != params[..]
                    || a[p..].iter().any(|t| contains(t, i.name))
                {
                    return None;
                }
                recursive.push((*field, a[p..].to_vec()));
                has_recursive = true;
            } else if contains(domain, i.name) {
                return None;
            }
        }
        let field_args = fields
            .iter()
            .map(|(id, _)| Term::Local(*id))
            .collect::<Vec<_>>();
        let ctor_term = apps(
            Term::Const(ctor.name, levels.clone()),
            params.iter().cloned().chain(field_args.clone()),
        );
        let mut minor_fields = fields.clone();
        for (field, args) in &recursive {
            minor_fields.push((
                fresh(&mut next),
                apps(
                    Term::Local(motive),
                    args.iter().cloned().chain([Term::Local(*field)]),
                ),
            ));
        }
        let minor_type = bind(
            &minor_fields,
            apps(
                Term::Local(motive),
                args[p..].iter().cloned().chain([ctor_term]),
            ),
            false,
        );
        let minor = fresh(&mut next);
        minor_vars.push(minor);
        rec_binders.push((minor, minor_type.clone()));
        rule_prefix.push((minor, minor_type));
        ctor_data.push((fields, recursive, field_args));
    }
    if !has_recursive {
        return None;
    }
    rec_binders.extend(indices.clone());
    rec_binders.push((major, major_type));
    let expected = bind(
        &rec_binders,
        apps(
            Term::Local(motive),
            index_args.into_iter().chain([Term::Local(major)]),
        ),
        false,
    );
    if read(e, r.ty, &[], 0, 256)? != expected {
        return None;
    }
    let rec_head = Term::Const(r.name, levels);
    for (ordinal, ((fields, recursive, field_args), rule)) in
        ctor_data.into_iter().zip(&r.rules).enumerate()
    {
        if rule.constructor != b.constructors[ordinal].name
            || rule.num_fields != fields.len() as u64
        {
            return None;
        }
        let recursive_args = recursive.into_iter().map(|(field, indices)| {
            apps(
                rec_head.clone(),
                params
                    .iter()
                    .cloned()
                    .chain([Term::Local(motive)])
                    .chain(minor_vars.iter().map(|id| Term::Local(*id)))
                    .chain(indices)
                    .chain([Term::Local(field)]),
            )
        });
        let body = apps(
            Term::Local(minor_vars[ordinal]),
            field_args.into_iter().chain(recursive_args),
        );
        let mut binders = rule_prefix.clone();
        binders.extend(fields);
        if read(e, rule.rhs, &[], 0, 256)? != bind(&binders, body, true) {
            return None;
        }
    }
    Some(())
}
