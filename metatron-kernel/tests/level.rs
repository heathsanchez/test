use std::collections::HashMap;

use metatron_kernel::id::{IdTable, LevelId, NameId};
use metatron_kernel::level::{LevelTerm, imax, instantiate_level, level_equal, max, succ};
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
