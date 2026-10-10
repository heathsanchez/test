use metatron_kernel::{
    environment::Environment,
    id::{ExprId,IdTable,LevelId,NameId},
    level::LevelTerm,
    syntax::{Expr,Level},
    typecheck::{TypeChecker,TypeValue},
    value::{Closure,EnvFrame,FreeId,LevelSubstitution},
};

fn compare_level_substitutions(right_level: LevelTerm) -> bool {
    let mut es=IdTable::default();
    let mut ls=IdTable::default();
    ls.insert(LevelId(0),Level::Zero).unwrap();
    ls.insert(LevelId(1),Level::Param(NameId(10))).unwrap();
    ls.insert(LevelId(2),Level::Succ(LevelId(0))).unwrap();
    es.insert(ExprId(0),Expr::Sort(LevelId(1))).unwrap();
    es.insert(ExprId(1),Expr::Lam{domain:ExprId(0),body:ExprId(0)}).unwrap();
    let env=Environment::empty();
    let ck=TypeChecker::new(&es,&ls,&env);
    let lhs=Closure::with_levels(
       ExprId(1),EnvFrame::empty().extend_free(FreeId(100)),
       LevelSubstitution::new(vec![(NameId(10),LevelTerm::Zero)]));
    let rhs=Closure::with_levels(
       ExprId(1),EnvFrame::empty().extend_free(FreeId(200)),
       LevelSubstitution::new(vec![
           (NameId(10),right_level),
           (NameId(11),LevelTerm::Succ(Box::new(LevelTerm::Zero)))
       ]));
    assert_ne!(lhs.env.id(),rhs.env.id());
    ck.convert(&TypeValue::Term(lhs),&TypeValue::Term(rhs),1024).is_proven()
}

#[test]
fn the_same_instantiated_universe_survives_irrelevant_mapping_differences(){
    assert!(compare_level_substitutions(LevelTerm::Zero));
}
#[test]
fn genuinely_distinct_instantiated_universes_cannot_be_merged(){
    assert!(!compare_level_substitutions(LevelTerm::Succ(Box::new(LevelTerm::Zero))));
}
