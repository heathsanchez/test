use metatron_kernel::environment::{ConstantDecl, Environment};
use metatron_kernel::id::{ExprId, IdTable, LevelId, NameId};
use metatron_kernel::level::LevelTerm;
use metatron_kernel::syntax::{Expr, Level};
use metatron_kernel::typecheck::{TypeChecker, TypeValue};
use metatron_kernel::value::{Closure, EnvFrame, FreeId, LevelSubstitution};

fn fixture() -> (IdTable<ExprId, Expr>, IdTable<LevelId, Level>, Environment, ExprId) {
    let mut expressions = IdTable::default();
    let mut levels = IdTable::default();
    levels.insert(LevelId(0), Level::Zero).unwrap();
    expressions.insert(ExprId(0), Expr::BVar(0)).unwrap();
    expressions.insert(ExprId(1), Expr::Const { name: NameId(1), levels: vec![] }).unwrap();
    expressions.insert(ExprId(2), Expr::Sort(LevelId(0))).unwrap();
    levels.insert(LevelId(1), Level::Succ(LevelId(0))).unwrap();
    expressions.insert(ExprId(600), Expr::Sort(LevelId(1))).unwrap();
    expressions.insert(ExprId(601), Expr::Const { name: NameId(2), levels: vec![] }).unwrap();
    expressions.insert(ExprId(602), Expr::Pi { domain: ExprId(601), body: ExprId(601) }).unwrap();
    expressions.insert(ExprId(603), Expr::Pi { domain: ExprId(601), body: ExprId(602) }).unwrap();
    let environment = Environment::empty()
        .extend(NameId(2), ConstantDecl::axiom(vec![], ExprId(600))).unwrap()
        .extend(NameId(1), ConstantDecl::axiom(vec![], ExprId(603))).unwrap();
    let mut root = ExprId(0);
    for i in 0..159 {
        let first = ExprId(3 + i * 2);
        let second = ExprId(4 + i * 2);
        expressions.insert(first, Expr::App { fun: ExprId(1), arg: root }).unwrap();
        expressions.insert(second, Expr::App { fun: first, arg: root }).unwrap();
        root = second;
    }
    (expressions, levels, environment, root)
}
fn captured(root: ExprId, free: u64, unused: u64) -> TypeValue {
    let mut value = Closure::new(ExprId(0), EnvFrame::empty().extend_free(FreeId(free)));
    for _ in 0..37 { value = Closure::new(ExprId(0), EnvFrame::empty().extend(value)); }
    TypeValue::Term(Closure::new(root, EnvFrame::empty().extend_free(FreeId(unused)).extend(value)))
}

#[test]
fn complete_shared_source_dag_reuses_support_and_exact_alias_captures() {
    let (expressions, levels, environment, root) = fixture();
    let checker = TypeChecker::new(&expressions, &levels, &environment);
    let left = captured(root, 1, 8);
    let right = captured(root, 1, 9);
    assert!(checker.convert(&left, &right, 4096).is_proven());
    assert!(checker.convert(&left, &right, 256).is_proven(), "completed support plus37 aliases should fit bounded reuse");
    assert!(!checker.convert(&left, &captured(root, 2, 9), 256).is_proven(), "different actual data cannot inherit identity");
    assert!(!checker.convert(&left, &right, 0).is_proven());
}

#[test]
fn source_identity_preserves_instantiated_universes_and_rejects_cycles() {
    let (mut expressions, mut levels, environment, _) = fixture();
    levels.insert(LevelId(2), Level::Param(NameId(7))).unwrap();
    expressions.insert(ExprId(500), Expr::Sort(LevelId(2))).unwrap();
    expressions.insert(ExprId(501), Expr::Lam { domain: ExprId(2), body: ExprId(501) }).unwrap();
    let checker = TypeChecker::new(&expressions, &levels, &environment);
    let term = |level| TypeValue::Term(Closure::with_levels(ExprId(500),
        EnvFrame::empty().extend_free(FreeId(1)), LevelSubstitution::new(vec![(NameId(7), level)])));
    assert!(!checker.convert(&term(LevelTerm::Zero), &term(LevelTerm::Succ(Box::new(LevelTerm::Zero))), 256).is_proven());
    let left = TypeValue::Term(Closure::new(ExprId(501), EnvFrame::empty().extend_free(FreeId(1))));
    let right = TypeValue::Term(Closure::new(ExprId(501), EnvFrame::empty().extend_free(FreeId(2))));
    assert!(!checker.convert(&left, &right, 64).is_proven(), "cyclic syntax cannot earn a complete support certificate");
}

#[test]
fn copied_shifted_source_dag_matches_actual_capture_not_offset_shape() {
    let (mut expressions, levels, environment, _) = fixture();
    let mut left = ExprId(700);
    let mut right = ExprId(701);
    expressions.insert(left, Expr::BVar(1)).unwrap();
    expressions.insert(right, Expr::BVar(2)).unwrap();
    for i in 0..106 {
        let lf = ExprId(702 + i * 4); let lb = ExprId(703 + i * 4);
        let rf = ExprId(704 + i * 4); let rb = ExprId(705 + i * 4);
        expressions.insert(lf, Expr::App { fun: ExprId(1), arg: left }).unwrap();
        expressions.insert(lb, Expr::App { fun: lf, arg: left }).unwrap();
        expressions.insert(rf, Expr::App { fun: ExprId(1), arg: right }).unwrap();
        expressions.insert(rb, Expr::App { fun: rf, arg: right }).unwrap();
        left = lb; right = rb;
    }
    expressions.insert(ExprId(1200), Expr::App { fun: ExprId(1), arg: left }).unwrap();
    expressions.insert(ExprId(1201), Expr::App { fun: ExprId(1), arg: right }).unwrap();
    expressions.insert(ExprId(1202), Expr::Lam { domain: ExprId(601), body: ExprId(1200) }).unwrap();
    expressions.insert(ExprId(1203), Expr::Lam { domain: ExprId(601), body: ExprId(1201) }).unwrap();
    let checker = TypeChecker::new(&expressions, &levels, &environment);
    let alias = |free| {
        let mut value = Closure::new(ExprId(0), EnvFrame::empty().extend_free(FreeId(free)));
        for _ in 0..37 { value = Closure::new(ExprId(0), EnvFrame::empty().extend(value)); }
        value
    };
    let left = TypeValue::Term(Closure::new(ExprId(1202), EnvFrame::empty().extend(alias(9))));
    let right = |free| TypeValue::Term(Closure::new(ExprId(1203),
        EnvFrame::empty().extend(alias(free)).extend_free(FreeId(99))));
    assert!(checker.convert(&left, &right(9), 4096).is_proven());
    assert!(checker.convert(&left, &right(9), 128).is_proven(), "copied217-node syntax and shifted used capture need a complete paired support proof");
    assert!(!checker.convert(&left, &right(10), 128).is_proven(), "same offset shift does not identify different actual data");
}

#[test]
fn paired_sources_do_not_identify_bound_and_external_variables() {
    let (mut expressions, levels, environment, _) = fixture();
    expressions.insert(ExprId(700), Expr::BVar(1)).unwrap();
    expressions.insert(ExprId(701), Expr::Lam { domain: ExprId(601), body: ExprId(0) }).unwrap();
    expressions.insert(ExprId(702), Expr::Lam { domain: ExprId(601), body: ExprId(700) }).unwrap();
    let checker = TypeChecker::new(&expressions, &levels, &environment);
    let left = TypeValue::Term(Closure::new(ExprId(701), EnvFrame::empty().extend_free(FreeId(0))));
    let right = TypeValue::Term(Closure::new(ExprId(702), EnvFrame::empty().extend_free(FreeId(1))));
    assert!(!checker.convert(&left, &right, 256).is_proven(), "ambientFree1 must not alias the fresh virtual lambda binder");
}

#[test]
fn ambient_free_zero_is_not_a_fresh_virtual_opening_binder() {
    let (mut expressions, levels, environment, _) = fixture();
    expressions.insert(ExprId(700), Expr::BVar(1)).unwrap();
    expressions.insert(ExprId(701), Expr::Lam { domain: ExprId(601), body: ExprId(0) }).unwrap();
    expressions.insert(ExprId(702), Expr::Lam { domain: ExprId(601), body: ExprId(700) }).unwrap();
    let checker = TypeChecker::new(&expressions, &levels, &environment);
    let left = TypeValue::Term(Closure::new(ExprId(701), EnvFrame::empty().extend_free(FreeId(0))));
    let right = TypeValue::Term(Closure::new(ExprId(702), EnvFrame::empty().extend_free(FreeId(0))));
    assert!(!checker.convert(&left, &right, 256).is_proven(), "lambda x => x differs from lambda x => ambientFree0");
}

#[test]
fn root_aliases_preserve_the_actual_payload_and_its_own_universes() {
    let (expressions, levels, environment, root) = fixture();
    let checker = TypeChecker::new(&expressions, &levels, &environment);
    let payload = |free| Closure::new(root, EnvFrame::empty().extend_free(FreeId(free)));
    let alias = |value: Closure| {
        let mut value = value;
        for _ in 0..37 { value = Closure::new(ExprId(0), EnvFrame::empty().extend(value)); }
        TypeValue::Term(Closure::with_levels(ExprId(0), EnvFrame::empty().extend(value),
            LevelSubstitution::new(vec![(NameId(7), LevelTerm::Succ(Box::new(LevelTerm::Zero)))])))
    };
    let right = TypeValue::Term(payload(9));
    assert!(checker.convert(&alias(payload(9)), &right, 4096).is_proven());
    assert!(checker.convert(&alias(payload(9)), &right, 128).is_proven(), "outer BVar universes are irrelevant; actual payload owns its universes");
    assert!(!checker.convert(&alias(payload(10)), &right, 128).is_proven());
    assert!(!checker.convert(&alias(payload(9)), &right, 0).is_proven());
    let changed_levels = Closure::with_levels(root, EnvFrame::empty().extend_free(FreeId(9)),
        LevelSubstitution::new(vec![(NameId(7), LevelTerm::Succ(Box::new(LevelTerm::Zero)))]));
    assert!(!checker.convert(&alias(changed_levels), &right, 128).is_proven(), "actual captured level maps must still match");
}

#[test]
fn root_aliases_do_not_identify_a_free_with_a_bound_lambda_or_cyclic_source() {
    let (mut expressions, levels, environment, _) = fixture();
    expressions.insert(ExprId(700), Expr::Lam { domain: ExprId(601), body: ExprId(0) }).unwrap();
    expressions.insert(ExprId(701), Expr::Lam { domain: ExprId(601), body: ExprId(701) }).unwrap();
    let checker = TypeChecker::new(&expressions, &levels, &environment);
    let free = TypeValue::Term(Closure::new(ExprId(0), EnvFrame::empty().extend_free(FreeId(0))));
    let lambda = TypeValue::Term(Closure::new(ExprId(700), EnvFrame::empty()));
    assert!(!checker.convert(&free, &lambda, 256).is_proven());
    let alias = TypeValue::Term(Closure::new(ExprId(0), EnvFrame::empty().extend(
        Closure::new(ExprId(701), EnvFrame::empty()))));
    let cyclic = TypeValue::Term(Closure::new(ExprId(701), EnvFrame::empty().extend_free(FreeId(0))));
    assert!(!checker.convert(&alias, &cyclic, 128).is_proven());
    let missing = TypeValue::Term(Closure::new(ExprId(0), EnvFrame::empty()));
    assert!(!checker.convert(&missing, &lambda, 256).is_proven());
}
