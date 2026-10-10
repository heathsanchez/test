//! Conservative free-variable-support congruence for captured source terms.
//!
//! A positive result certifies equality by identical syntax and recursively
//! identical substituted dependencies. This never identifies different source
//! proof hypotheses, even when they happen to reuse a FreeId number.
//! Budget exhaustion and unrecognized bindings conservatively return false.

use std::collections::HashSet;
use crate::id::{ExprId, IdTable};
use crate::syntax::Expr;
use crate::value::{Closure, EnvBinding, EnvFrame};

type Visit = (ExprId, u64, u64, u64);

pub(crate) fn same_term_by_exact_support(
    expressions: &IdTable<ExprId, Expr>,
    a: &Closure,
    b: &Closure,
    budget: usize,
) -> bool {
    let mut left = budget.min(4_096);
    let mut visited: HashSet<Visit> = HashSet::new();
    compare_closures(expressions, a, b, &mut left, &mut visited)
}

fn compare_closures(
    expressions: &IdTable<ExprId, Expr>,
    a: &Closure,
    b: &Closure,
    remaining: &mut usize,
    visited: &mut HashSet<Visit>,
) -> bool {
    if a.expr != b.expr || a.levels != b.levels {
        return false;
    }
    if a.env == b.env {
        return true;
    }
    compare_expression(expressions, a.expr, &a.env, &b.env, 0, remaining, visited)
}

fn compare_expression(
    expressions: &IdTable<ExprId, Expr>,
    expr: ExprId,
    left: &EnvFrame,
    right: &EnvFrame,
    binder_depth: u64,
    remaining: &mut usize,
    visited: &mut HashSet<Visit>,
) -> bool {
    if left == right {
        return true;
    }
    if *remaining == 0 {
        return false;
    }
    *remaining -= 1;
    // No coinductive equality from a repeated unresolved graph obligation.
    if !visited.insert((expr, left.id(), right.id(), binder_depth)) {
        return false;
    }
    let Some(e) = expressions.get(expr) else {
        return false;
    };
    match e {
        Expr::BVar(i) if *i < binder_depth => true,
        Expr::BVar(i) => {
            let Some(idx) = i.checked_sub(binder_depth) else {
                return false;
            };
            let (Some((lid, l)), Some((rid, r))) =
                (left.lookup_with_node_id(idx), right.lookup_with_node_id(idx))
            else {
                return false;
            };
            match (l, r) {
                // FreeId numbers may be reused by different source contexts;
                // identical binding-node lineage is essential here.
                (EnvBinding::Free(x), EnvBinding::Free(y)) => lid == rid && x == y,
                (EnvBinding::Neutral(x), EnvBinding::Neutral(y)) => lid == rid && x == y,
                (EnvBinding::Closure(x), EnvBinding::Closure(y)) =>
                    compare_closures(expressions, &x, &y, remaining, visited),
                _ => false,
            }
        }
        Expr::App {fun,arg} =>
            compare_expression(expressions,*fun,left,right,binder_depth,remaining,visited)
            && compare_expression(expressions,*arg,left,right,binder_depth,remaining,visited),
        Expr::Lam {domain,body} | Expr::Pi {domain,body} =>
            compare_expression(expressions,*domain,left,right,binder_depth,remaining,visited)
            && binder_depth.checked_add(1).is_some_and(|next|
                compare_expression(expressions,*body,left,right,next,remaining,visited)),
        Expr::Let {ty,value,body} =>
            compare_expression(expressions,*ty,left,right,binder_depth,remaining,visited)
            && compare_expression(expressions,*value,left,right,binder_depth,remaining,visited)
            && binder_depth.checked_add(1).is_some_and(|next|
                compare_expression(expressions,*body,left,right,next,remaining,visited)),
        Expr::Proj {structure,..} =>
            compare_expression(expressions,*structure,left,right,binder_depth,remaining,visited),
        Expr::Sort(_) | Expr::Const {..} | Expr::NatLit(_) | Expr::StrLit(_) => true,
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::value::FreeId;

    #[test]
    fn irrelevant_captured_frames_do_not_change_closed_source_term() {
        let mut exprs = IdTable::default();
        exprs.insert(ExprId(10), Expr::Sort(crate::id::LevelId(0))).unwrap();
        let a = Closure::new(ExprId(10), EnvFrame::empty().extend_free(FreeId(11)));
        let b = Closure::new(ExprId(10), EnvFrame::empty().extend_free(FreeId(12)));
        assert!(same_term_by_exact_support(&exprs, &a, &b, 16));
        assert!(!same_term_by_exact_support(&exprs, &a, &b, 0));
    }

    #[test]
    fn separately_bound_same_numbered_free_variable_is_not_identified() {
        let mut exprs = IdTable::default();
        exprs.insert(ExprId(10), Expr::BVar(0)).unwrap();
        let a = Closure::new(ExprId(10), EnvFrame::empty().extend_free(FreeId(3)));
        let b = Closure::new(ExprId(10), EnvFrame::empty().extend_free(FreeId(3)));
        assert!(!same_term_by_exact_support(&exprs, &a, &b, 32));
    }

    #[test]
    fn independent_closed_substitutions_are_reused() {
        let mut exprs = IdTable::default();
        exprs.insert(ExprId(10), Expr::BVar(0)).unwrap();
        exprs.insert(ExprId(11), Expr::Sort(crate::id::LevelId(0))).unwrap();
        let root = EnvFrame::empty();
        let a = Closure::new(ExprId(10),
            root.extend_free(FreeId(7)).extend(Closure::new(ExprId(11),root.clone())));
        let b = Closure::new(ExprId(10),
            root.extend_free(FreeId(8)).extend(Closure::new(ExprId(11),root.clone())));
        assert!(same_term_by_exact_support(&exprs, &a, &b, 32));
    }

    #[test]
    fn unrelated_source_bindings_cannot_be_equated() {
        let mut exprs = IdTable::default();
        exprs.insert(ExprId(10), Expr::BVar(0)).unwrap();
        exprs.insert(ExprId(11), Expr::BVar(1)).unwrap();
        let root=EnvFrame::empty();
        let a=Closure::new(ExprId(10),root.extend_free(FreeId(1))
            .extend(Closure::new(ExprId(11),root.extend_free(FreeId(2)))));
        let b=Closure::new(ExprId(10),root.extend_free(FreeId(3))
            .extend(Closure::new(ExprId(11),root.extend_free(FreeId(4)))));
        assert!(!same_term_by_exact_support(&exprs,&a,&b,64));
    }

    #[test]
    fn nested_lambda_preserves_binder_offsets_and_external_support() {
        let mut exprs = IdTable::default();
        exprs.insert(ExprId(0), Expr::Sort(crate::id::LevelId(0))).unwrap();
        exprs.insert(ExprId(1), Expr::BVar(0)).unwrap();
        exprs.insert(ExprId(2), Expr::Lam{domain:ExprId(0),body:ExprId(1)}).unwrap();
        let root=EnvFrame::empty();
        let a=Closure::new(ExprId(2),root.extend_free(FreeId(100)));
        let b=Closure::new(ExprId(2),root.extend_free(FreeId(200)));
        assert!(same_term_by_exact_support(&exprs,&a,&b,32));
    }
}
