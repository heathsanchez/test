use metatron_kernel::environment::{ConstantDecl, Environment};
use metatron_kernel::id::{ExprId, IdTable, LevelId, NameId};
use metatron_kernel::judgment::Judgment;
use metatron_kernel::syntax::{Expr, Level};
use metatron_kernel::typecheck::{TypeChecker, TypeValue};
use metatron_kernel::value::{Closure, EnvFrame};

#[test]
fn mismatched_proof_types_refute_before_proof_whnf() {
    let mut levels = IdTable::default();
    levels.insert(LevelId(0), Level::Zero).unwrap();

    let mut expressions = IdTable::default();
    expressions
        .insert(ExprId(0), Expr::Sort(LevelId(0)))
        .unwrap();
    expressions
        .insert(
            ExprId(1),
            Expr::Const {
                name: NameId(1),
                levels: Vec::new(),
            },
        )
        .unwrap();
    expressions
        .insert(
            ExprId(2),
            Expr::Const {
                name: NameId(2),
                levels: Vec::new(),
            },
        )
        .unwrap();
    expressions
        .insert(
            ExprId(3),
            Expr::Const {
                name: NameId(3),
                levels: Vec::new(),
            },
        )
        .unwrap();
    expressions
        .insert(
            ExprId(4),
            Expr::Const {
                name: NameId(4),
                levels: Vec::new(),
            },
        )
        .unwrap();

    // P Q : Prop; hp : P; hq : Q.  P and Q are distinct opaque proposition
    // constants, so their proof terms cannot be definitionally equal.
    let environment = Environment::empty()
        .extend(NameId(1), ConstantDecl::axiom(Vec::new(), ExprId(0)))
        .unwrap()
        .extend(NameId(2), ConstantDecl::axiom(Vec::new(), ExprId(0)))
        .unwrap()
        .extend(NameId(3), ConstantDecl::axiom(Vec::new(), ExprId(1)))
        .unwrap()
        .extend(NameId(4), ConstantDecl::axiom(Vec::new(), ExprId(2)))
        .unwrap();

    let checker = TypeChecker::new(&expressions, &levels, &environment);
    let left = TypeValue::Term(Closure::new(ExprId(3), EnvFrame::empty()));
    let right = TypeValue::Term(Closure::new(ExprId(4), EnvFrame::empty()));

    assert_eq!(
        checker.convert(&left, &right, 4096),
        Judgment::refuted("proof-proposition-types-not-defeq")
    );
}
