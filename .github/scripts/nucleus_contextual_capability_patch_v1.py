#!/usr/bin/env python3
"""Isolated Nucleus candidate: context-exact positive conversion memo and
support-complete closure congruence. All changed Rust is published in CI diff.

This does NOT promote any new ACCEPT automatically. No result may be accepted
from syntax identity, pointer/hash coincidence, or an UNKNOWN certificate.
"""
from pathlib import Path
import sys

root = Path(sys.argv[1] if len(sys.argv) > 1 else "metatron-kernel")
cv = root / "src" / "convert.rs"
tc = root / "src" / "typecheck.rs"

def replace_once(s, old, new, label):
    n = s.count(old)
    if n != 1:
        raise SystemExit(f"PATCH_FAILURE {label}: found {n}, expected 1")
    return s.replace(old, new, 1)

a = tc.read_text()
field = "    exposure_cache: ExposureCache,\n"
a = replace_once(a, field, field +
    "    // Exact scope + immutable authority are part of the reusable warrant.\n"
    "    // A HashMap collision is never an equality test (Eq checks the full key).\n"
    "    pub(crate) contextual_conversion_memo: Rc<RefCell<HashMap<\n"
    "        (crate::machine::AuthorityId, TypeValue, TypeValue, usize, Vec<TypeValue>, bool),\n"
    "        crate::judgment::WarrantId,\n"
    "    >>>,\n", "typed memo field")
needle = "            exposure_cache: new_exposure_cache(),\n"
assert a.count(needle) == 4, a.count(needle)
a = a.replace(needle, needle +
    "            contextual_conversion_memo: Rc::new(RefCell::new(HashMap::new())),\n")
tc.write_text(a)

s = cv.read_text()
s = replace_once(s,
    "type ConversionVisitKey = (crate::machine::AuthorityId, TypeValue, TypeValue);",
    "type ConversionVisitKey = (crate::machine::AuthorityId, TypeValue, TypeValue, Option<(usize, Vec<TypeValue>)>);",
    "contextful visit key")
old = """    let mut congruence_attempts = 32;
    convert_in_context_with_congruence(
        checker, left, right, budget, delta_policy, initial_depth, context, 0,
        &mut congruence_attempts,
    )
}"""
new = """    // Only fully PROVEN conversions are reusable. Exact source authority,
    // both terms, semantic policy, depth and the ENTIRE lexical context are
    // included in the key. The map is scoped to this immutable TypeChecker.
    // An entry retains the original trusted warrant, not a guessed shortcut.
    let use_memo = std::env::var_os("NUCLEUS_EXPERIMENTAL_CONTEXT_MEMO").is_some();
    let memo_key = use_memo.then(|| (
        checker.authority(), left.clone(), right.clone(),
        initial_depth, context.to_vec(),
        delta_policy == DeltaPolicy::GuardedSemanticFallback,
    ));
    if let Some(key) = memo_key.as_ref()
        && let Some(warrant) = checker.contextual_conversion_memo.borrow().get(key).copied()
    {
        #[cfg(feature = "diagnostics")]
        if std::env::var_os("NUCLEUS_TRACE_CONTEXT_MEMO").is_some() {
            use std::sync::atomic::{AtomicUsize, Ordering};
            static HIT: AtomicUsize = AtomicUsize::new(0);
            if HIT.fetch_add(1, Ordering::Relaxed) < 96 {
                eprintln!("NUCLEUS_CONTEXT_MEMO_HIT:depth={initial_depth}:context={}:warrant={warrant:?}", context.len());
            }
        }
        return Judgment::Proven { value: (), warrant };
    }
    let mut congruence_attempts = 32;
    let result = convert_in_context_with_congruence(
        checker, left, right, budget, delta_policy, initial_depth, context, 0,
        &mut congruence_attempts,
    );
    if let (Some(key), Judgment::Proven { warrant, .. }) = (memo_key, &result) {
        let mut entries = checker.contextual_conversion_memo.borrow_mut();
        // No drop-all eviction cliffs. Beyond this high-water mark, admit
        // no more entries but retain previous useful exact certificates.
        if entries.len() < 16384 {
            entries.insert(key, *warrant);
        }
    }
    result
}"""
s = replace_once(s,old,new,"bounded exact conversion cache")
old = """        if !visited.insert((checker.authority(), left.clone(), right.clone())) {
            continue;
        }
"""
new = """        // An equality visited in a DIFFERENT binder scope is not a proof
        // for this scope. Keep the legacy visit key for the control arm.
        let protected_scope = std::env::var_os("NUCLEUS_EXPERIMENTAL_CONTEXT_VISIT")
            .is_some().then(|| (depth, local_context.clone()));
        if !visited.insert((
            checker.authority(), left.clone(), right.clone(), protected_scope,
        )) {
            continue;
        }
        if std::env::var_os("NUCLEUS_EXPERIMENTAL_CAPTURE_SUPPORT").is_some()
            && depth == context.len()
            && let (TypeValue::Term(lhs), TypeValue::Term(rhs)) = (&left, &right)
            && lhs != rhs
            && let Some(certificate) = checked_capture_support_congruence(
                checker, lhs, rhs, depth, context, remaining,
            )
        {
            #[cfg(feature = "diagnostics")]
            if std::env::var_os("NUCLEUS_TRACE_CAPTURE_SUPPORT").is_some() {
                use std::sync::atomic::{AtomicUsize, Ordering};
                static COUNT: AtomicUsize = AtomicUsize::new(0);
                if COUNT.fetch_add(1, Ordering::Relaxed) < 96 {
                    eprintln!(
                        "NUCLEUS_CAPTURE_SUPPORT_CERT:expr={:?}:depth={depth}:premises={certificate:?}",
                        lhs.expr,
                    );
                }
            }
            continue;
        }
"""
s = replace_once(s,old,new,"source-scoped proof rule")
helper = """
/// A bounded replayable list of substitution-congruence premises. An entry
/// for bvar k is admitted only when its actual two captured bindings are
/// definitionally equal in the SAME independently supplied typed context.
/// Syntax identity alone, equality of types alone, and hashes cannot prove it.
/// The two closure expressions and all level substitutions must be identical.
fn checked_capture_support_congruence(
    checker: &TypeChecker<'_>,
    left: &Closure,
    right: &Closure,
    depth: usize,
    context: &[TypeValue],
    budget: usize,
) -> Option<Vec<(u64, crate::judgment::WarrantId)>> {
    if depth != context.len()
        || left.expr != right.expr
        || left.levels != right.levels
        || budget < 8
    {
        return None;
    }

    // Walk only bvars that are free in the shared source expression.
    // Locally bound lambda/Pi/let bvars cancel because both operands have
    // exactly the same expression, independent of irrelevant captured slots.
    // Visited keys include binder depth: a shared DAG can appear under
    // different binding depths.
    let mut tasks = vec![(left.expr, 0_usize)];
    let mut seen = HashSet::new();
    let mut support = HashSet::<u64>::new();
    let mut fuel = budget.min(2048);
    while let Some((expression, binders)) = tasks.pop() {
        if fuel == 0 || binders > 128 {
            return None;
        }
        fuel -= 1;
        if !seen.insert((expression, binders)) {
            continue;
        }
        match checker.expression(expression)? {
            Expr::BVar(index) => {
                if *index >= binders as u64 {
                    support.insert(index.checked_sub(binders as u64)?);
                }
            }
            Expr::App { fun, arg } => {
                tasks.push((*fun, binders));
                tasks.push((*arg, binders));
            }
            Expr::Lam { domain, body } | Expr::Pi { domain, body } => {
                tasks.push((*domain, binders));
                tasks.push((*body, binders.checked_add(1)?));
            }
            Expr::Let { ty, value, body } => {
                tasks.push((*ty, binders));
                tasks.push((*value, binders));
                tasks.push((*body, binders.checked_add(1)?));
            }
            Expr::Proj { structure, .. } => tasks.push((*structure, binders)),
            Expr::Sort(_) | Expr::Const { .. } | Expr::NatLit(_) | Expr::StrLit(_) => {}
        }
    }

    let mut indices: Vec<u64> = support.into_iter().collect();
    indices.sort_unstable();
    let mut certificate = Vec::with_capacity(indices.len());
    for index in indices {
        let left_binding = left.env.lookup(index)?;
        let right_binding = right.env.lookup(index)?;
        let warrant = match (left_binding, right_binding) {
            (EnvBinding::Closure(lhs), EnvBinding::Closure(rhs)) if lhs == rhs =>
                crate::judgment::WarrantId("same-immutable-captured-closure"),
            (EnvBinding::Closure(lhs), EnvBinding::Closure(rhs)) => {
                // Strictly decreasing recursion budget; this is the SAME
                // ambient source context and never a frame-ID equivalence.
                let local_budget = fuel.min(budget / 2).min(512);
                if local_budget < 8 {
                    return None;
                }
                match convert_with_policy_in_context(
                    checker, &TypeValue::Term(lhs), &TypeValue::Term(rhs),
                    local_budget, DeltaPolicy::PreferredOnly, depth, context,
                ) {
                    Judgment::Proven { warrant, .. } => warrant,
                    _ => return None,
                }
            }
            (EnvBinding::Free(a), EnvBinding::Free(b))
                if a == b && usize::try_from(a.0).ok()? < context.len() =>
                crate::judgment::WarrantId("same-contextual-bound-variable"),
            (EnvBinding::Neutral(a), EnvBinding::Neutral(b)) if a == b => {
                match a.head {
                    crate::value::NeutralHead::Free(id)
                        if a.spine.is_empty()
                            && usize::try_from(id.0).ok()? < context.len() =>
                        crate::judgment::WarrantId("same-contextual-neutral-local"),
                    crate::value::NeutralHead::Const { .. }
                        if a.spine.is_empty() =>
                        crate::judgment::WarrantId("same-immutable-rigid-neutral"),
                    _ => return None,
                }
            }
            _ => return None,
        };
        certificate.push((index, warrant));
    }
    Some(certificate)
}

"""
anchor = "fn compare_values(\n"
s = replace_once(s,anchor,helper+anchor,"support-congruence proof helper")
# Local unit tests inspect the *actual captured dependency support*, not name
# fingerprints from Arena exports. These must pass with all other Rust tests.
tests = """
#[cfg(test)]
mod capture_support_v1_tests {
    use super::*;
    use crate::environment::Environment;
    use crate::id::{IdTable, LevelId};
    use crate::syntax::Level;
    use crate::value::EnvFrame;

    #[test]
    fn unused_captured_binding_is_not_a_semantic_distinction() {
        let mut exprs = IdTable::default();
        exprs.insert(ExprId(1), Expr::BVar(1)).unwrap();
        exprs.insert(ExprId(2), Expr::Sort(LevelId(0))).unwrap();
        exprs.insert(ExprId(3), Expr::Sort(LevelId(1))).unwrap();
        let mut levels = IdTable::default();
        levels.insert(LevelId(0), Level::Zero).unwrap();
        levels.insert(LevelId(1), Level::Succ(LevelId(0))).unwrap();
        let env = Environment::empty();
        let tc = TypeChecker::new(&exprs, &levels, &env);
        let used = Closure::new(ExprId(2), EnvFrame::empty());
        let a = Closure::new(ExprId(1),
            EnvFrame::empty().extend(used.clone()).extend(used.clone()));
        let b = Closure::new(ExprId(1),
            EnvFrame::empty().extend(used).extend(
                Closure::new(ExprId(3), EnvFrame::empty())));
        let certificate = checked_capture_support_congruence(
            &tc, &a, &b, 0, &[], 256
        ).expect("only the used de Bruijn binding matters");
        assert_eq!(certificate.len(), 1);
        assert_eq!(certificate[0].0, 1);
    }

    #[test]
    fn changed_used_binding_cannot_be_erased() {
        let mut exprs = IdTable::default();
        exprs.insert(ExprId(1), Expr::BVar(1)).unwrap();
        exprs.insert(ExprId(2), Expr::Sort(LevelId(0))).unwrap();
        exprs.insert(ExprId(3), Expr::Sort(LevelId(1))).unwrap();
        let mut levels = IdTable::default();
        levels.insert(LevelId(0), Level::Zero).unwrap();
        levels.insert(LevelId(1), Level::Succ(LevelId(0))).unwrap();
        let env = Environment::empty();
        let tc = TypeChecker::new(&exprs, &levels, &env);
        let a = Closure::new(ExprId(1), EnvFrame::empty().extend(
            Closure::new(ExprId(2), EnvFrame::empty())
        ).extend(Closure::new(ExprId(2), EnvFrame::empty())));
        let b = Closure::new(ExprId(1), EnvFrame::empty().extend(
            Closure::new(ExprId(3), EnvFrame::empty())
        ).extend(Closure::new(ExprId(2), EnvFrame::empty())));
        assert!(checked_capture_support_congruence(
            &tc, &a, &b, 0, &[], 256
        ).is_none());
    }

    #[test]
    fn missing_context_or_binding_never_generates_warrant() {
        let mut exprs = IdTable::default();
        exprs.insert(ExprId(1), Expr::BVar(0)).unwrap();
        let levels = IdTable::default();
        let env = Environment::empty();
        let tc = TypeChecker::new(&exprs, &levels, &env);
        let a = Closure::new(ExprId(1), EnvFrame::empty());
        let b = Closure::new(ExprId(1), EnvFrame::empty().extend_free(
            crate::value::FreeId(0)));
        assert!(checked_capture_support_congruence(
            &tc, &a, &b, 0, &[], 256
        ).is_none());
    }
}
"""
s += tests
cv.write_text(s)
print("PATCHED_CONTEXTUAL_CERT_V1", tc, cv)
