use std::collections::HashMap;

use metatron_kernel::id::{IdTable, LevelId, NameId};
use metatron_kernel::level::{
    LevelError, LevelTerm, imax, instantiate_level, level_equal, max, succ,
};
use metatron_kernel::syntax::Level;

#[test]
fn max_is_commutative_and_idempotent() {
    let u = LevelTerm::param("u");
    let v = LevelTerm::param("v");

    assert!(level_equal(max(u.clone(), v.clone()), max(v, u.clone()), 64).is_proven());
    assert!(level_equal(max(u.clone(), u.clone()), u, 64).is_proven());
}

#[test]
fn unresolved_imax_does_not_guess() {
    let u = LevelTerm::param("u");
    let v = LevelTerm::param("v");

    assert!(level_equal(imax(u.clone(), v.clone()), max(u, v), 64).is_unknown());
}

#[test]
fn imax_with_successor_right_is_max() {
    let u = LevelTerm::param("u");
    let v1 = succ(LevelTerm::param("v"));

    assert!(level_equal(imax(u.clone(), v1.clone()), max(u, v1), 64).is_proven());
}

#[test]
fn imax_is_idempotent_without_parameter_case_enumeration() {
    let u = LevelTerm::param("u");

    assert!(level_equal(imax(u.clone(), u.clone()), u, 64).is_proven());
}

#[test]
fn equality_over_26_parameters_does_not_enumerate_boolean_cases() {
    let ascending = ('a'..='z')
        .map(|name| LevelTerm::param(name.to_string()))
        .reduce(max)
        .unwrap();
    let descending = ('a'..='z')
        .rev()
        .map(|name| LevelTerm::param(name.to_string()))
        .reduce(max)
        .unwrap();

    assert!(level_equal(ascending, descending, 256).is_proven());
}

#[test]
fn instantiation_expands_sparse_level_graph_with_explicit_substitution() {
    let mut levels = IdTable::default();
    levels.insert(LevelId(0), Level::Zero).unwrap();
    levels.insert(LevelId(7), Level::Param(NameId(3))).unwrap();
    levels.insert(LevelId(2), Level::Succ(LevelId(7))).unwrap();
    let substitution = HashMap::from([(NameId(3), LevelTerm::param("u"))]);

    let instantiated = instantiate_level(&levels, LevelId(2), &substitution, 16).unwrap();
    assert_eq!(instantiated, succ(LevelTerm::param("u")));
}

#[test]
fn instantiation_rejects_cycles_missing_parameters_and_exhausted_budget() {
    let mut levels = IdTable::default();
    levels.insert(LevelId(1), Level::Succ(LevelId(1))).unwrap();
    levels.insert(LevelId(2), Level::Param(NameId(9))).unwrap();
    let substitution = HashMap::new();

    assert_eq!(
        instantiate_level(&levels, LevelId(1), &substitution, 8),
        Err(LevelError::Cycle(LevelId(1)))
    );
    assert_eq!(
        instantiate_level(&levels, LevelId(2), &substitution, 8),
        Err(LevelError::MissingSubstitution(NameId(9)))
    );
    assert_eq!(
        instantiate_level(&levels, LevelId(1), &substitution, 0),
        Err(LevelError::BudgetExhausted)
    );
}

#[test]
fn max_algebra_preserves_opaque_imax_atoms() {
    let atom=imax(succ(LevelTerm::param("u")),imax(succ(LevelTerm::param("u")),LevelTerm::param("v")));
    let left=max(atom.clone(),max(atom.clone(),succ(LevelTerm::Zero)));
    let right=max(succ(LevelTerm::Zero),atom);
    assert!(level_equal(left,right,256).is_proven());
}

#[test]
fn opaque_imax_atoms_do_not_license_universe_inequality() {
    let u=LevelTerm::param("u");let v=LevelTerm::param("v");
    assert!(level_equal(max(imax(u.clone(),v.clone()),succ(LevelTerm::Zero)),max(max(u,v),succ(LevelTerm::Zero)),256).is_unknown());
}

#[test]
fn max_algebra_is_congruent_inside_nested_imax() {
    let a=LevelTerm::param("a");let b=LevelTerm::param("b");let c=LevelTerm::param("c");let v=LevelTerm::param("v");
    let left=imax(max(max(succ(a.clone()),b.clone()),c.clone()),imax(max(b.clone(),c.clone()),v.clone()));
    let right=imax(max(b.clone(),max(c.clone(),succ(a))),imax(max(c,b),v));
    assert!(level_equal(left,right,512).is_proven());
}

#[test]
fn opaque_max_successor_distribution_and_constant_absorption() {
    let a=imax(LevelTerm::param("u"),LevelTerm::param("v"));
    assert!(level_equal(succ(max(a.clone(),LevelTerm::param("w"))),max(succ(a.clone()),succ(LevelTerm::param("w"))),256).is_proven());
    assert!(level_equal(max(succ(a.clone()),succ(LevelTerm::Zero)),succ(a.clone()),256).is_proven());
    assert!(!level_equal(max(a.clone(),succ(LevelTerm::Zero)),a,256).is_proven());
    let a=imax(LevelTerm::param("u"),LevelTerm::param("v"));
    assert!(level_equal(max(a.clone(),succ(LevelTerm::Zero)),max(succ(LevelTerm::Zero),a),1).is_unknown());
}

#[test]
fn nested_imax_congruence_does_not_drop_or_swap_its_arguments() {
    let a=LevelTerm::param("a");let b=LevelTerm::param("b");let c=LevelTerm::param("c");
    assert!(!level_equal(imax(max(a.clone(),b.clone()),c.clone()),imax(a.clone(),c.clone()),512).is_proven());
    assert!(!level_equal(imax(max(a.clone(),b.clone()),c.clone()),imax(c,max(a,b)),512).is_proven());
}
