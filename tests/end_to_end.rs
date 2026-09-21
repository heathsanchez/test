use std::fs::File;
use std::io::BufReader;
use std::io::Cursor;
use std::path::PathBuf;

use metatron_kernel::verdict::Verdict;

fn run_fixture(name: &str) -> Verdict {
    let path = PathBuf::from(env!("CARGO_MANIFEST_DIR"))
        .join("tests")
        .join("fixtures")
        .join(name);
    metatron_kernel::run(BufReader::new(File::open(path).unwrap()))
}

fn run_residual(name: &str) -> Verdict {
    let path = PathBuf::from(env!("CARGO_MANIFEST_DIR"))
        .join("evidence")
        .join("residuals")
        .join(name)
        .join("fixture.ndjson");
    metatron_kernel::run(BufReader::new(File::open(path).unwrap()))
}

#[test]
fn sparse_name_axiom_is_accepted() {
    assert_eq!(run_fixture("sparse-name-index.ndjson"), Verdict::Accept);
}

#[test]
fn out_of_order_level_axiom_is_accepted() {
    assert_eq!(
        run_fixture("level-index-out-of-order.ndjson"),
        Verdict::Accept
    );
}

#[test]
fn unbound_axiom_type_is_rejected() {
    assert_eq!(run_fixture("bad-unbound-axiom.ndjson"), Verdict::Reject);
}

#[test]
fn unsupported_inductive_is_unknown() {
    assert_eq!(
        run_fixture("unsupported-inductive.ndjson"),
        Verdict::Unknown
    );
}

#[test]
fn beta_checked_definition_is_accepted() {
    assert_eq!(run_fixture("good-beta-definition.ndjson"), Verdict::Accept);
}

#[test]
fn definition_is_not_installed_before_its_value_is_checked() {
    assert_eq!(run_fixture("bad-self-proof.ndjson"), Verdict::Reject);
}

#[test]
fn g3_001_opaque_hint_does_not_make_a_definition_semantically_inaccessible() {
    assert_eq!(run_residual("G3-001"), Verdict::Accept);
}

#[test]
fn g4_001_dependent_bodies_are_related_under_a_shared_binder() {
    assert_eq!(run_residual("G4-001"), Verdict::Accept);
}

#[test]
fn g5_001_rigid_nonsort_is_refuted_not_erased_to_unknown() {
    assert_eq!(run_residual("G5-001"), Verdict::Reject);
}

#[test]
fn g6_001_non_propositional_theorem_is_rejected() {
    assert_eq!(run_residual("G6-001"), Verdict::Reject);
}

#[test]
fn valid_theorem_can_be_used_by_a_later_theorem() {
    assert_eq!(run_fixture("good-theorem-use.ndjson"), Verdict::Accept);
}

#[test]
fn theorem_is_not_installed_before_its_proof_is_checked() {
    assert_eq!(run_fixture("bad-self-theorem.ndjson"), Verdict::Reject);
}

#[test]
fn g7_001_duplicate_universe_parameters_are_rejected() {
    assert_eq!(run_residual("G7-001"), Verdict::Reject);
}

#[test]
fn g8_001_imax_idempotence_decides_the_peano_type() {
    assert_eq!(run_residual("G8-001"), Verdict::Accept);
}

#[test]
fn g9_001_derived_empty_inductive_authority_is_accepted() {
    assert_eq!(run_residual("G9-001"), Verdict::Accept);
}

#[test]
fn derived_empty_recursor_is_available_as_an_opaque_constant() {
    assert_eq!(run_fixture("good-empty-recursor.ndjson"), Verdict::Accept);
}

#[test]
fn fabricated_extra_and_orphan_recursors_are_rejected() {
    assert_eq!(run_fixture("bad-extra-recursor.ndjson"), Verdict::Reject);
    assert_eq!(run_fixture("bad-orphan-recursor.ndjson"), Verdict::Reject);
}

#[test]
fn empty_recursor_metadata_is_checked_not_trusted() {
    let bytes = include_str!("../evidence/residuals/G9-001/fixture.ndjson");
    let perturbed = bytes.replacen("\"k\":false", "\"k\":true", 1);
    assert_eq!(
        metatron_kernel::run(Cursor::new(perturbed)),
        Verdict::Reject
    );
}

#[test]
fn g10_001_derived_binary_enum_authority_is_accepted() {
    assert_eq!(run_residual("G10-001"), Verdict::Accept);
}

#[test]
fn binary_enum_constructor_index_is_checked_not_trusted() {
    let bytes = include_str!("../evidence/residuals/G10-001/fixture.ndjson");
    let perturbed = bytes.replacen("\"cidx\":0", "\"cidx\":1", 1);
    assert_eq!(
        metatron_kernel::run(Cursor::new(perturbed)),
        Verdict::Reject
    );
}

#[test]
fn binary_enum_recursor_rules_are_derived_not_axiomatized() {
    let bytes = include_str!("../evidence/residuals/G10-001/fixture.ndjson");
    let perturbed = bytes.replacen(
        "\"ctor\":2,\"nfields\":0,\"rhs\":18",
        "\"ctor\":2,\"nfields\":0,\"rhs\":21",
        1,
    );
    assert_eq!(
        metatron_kernel::run(Cursor::new(perturbed)),
        Verdict::Reject
    );
}

fn run_g11_perturbation(from: &str, to: &str) -> Verdict {
    let bytes = include_str!("../evidence/residuals/G11-001/fixture.ndjson");
    assert!(bytes.contains(from), "missing perturbation source: {from}");
    metatron_kernel::run(Cursor::new(bytes.replacen(from, to, 1)))
}

#[test]
fn g11_001_derived_twobool_authority_is_accepted() {
    assert_eq!(run_residual("G11-001"), Verdict::Accept);
}

#[test]
fn twobool_constructor_claims_are_derived_not_trusted() {
    let cases = [
        ("\"cidx\":0,\"induct\":10", "\"cidx\":1,\"induct\":10"),
        ("\"induct\":10,\"isUnsafe\"", "\"induct\":1,\"isUnsafe\""),
        (
            "\"numFields\":2,\"numParams\":0,\"type\":24",
            "\"numFields\":1,\"numParams\":0,\"type\":24",
        ),
        (
            "\"numFields\":2,\"numParams\":0,\"type\":24",
            "\"numFields\":2,\"numParams\":0,\"type\":23",
        ),
    ];
    for (from, to) in cases {
        assert_eq!(run_g11_perturbation(from, to), Verdict::Reject);
    }
}

#[test]
fn twobool_recursor_and_rule_claims_are_derived_not_trusted() {
    let cases = [
        (
            "\"numMinors\":1,\"numMotives\":1",
            "\"numMinors\":0,\"numMotives\":1",
        ),
        (
            "\"ctor\":11,\"nfields\":2,\"rhs\":42",
            "\"ctor\":2,\"nfields\":2,\"rhs\":42",
        ),
        (
            "\"ctor\":11,\"nfields\":2,\"rhs\":42",
            "\"ctor\":11,\"nfields\":1,\"rhs\":42",
        ),
        (
            "\"ctor\":11,\"nfields\":2,\"rhs\":42",
            "\"ctor\":11,\"nfields\":2,\"rhs\":41",
        ),
        (
            "\"name\":14,\"numIndices\":0",
            "\"name\":11,\"numIndices\":0",
        ),
        ("\"rules\":[{\"ctor\":11", "\"rules\":[{\"ctor\":2"),
        ("\"type\":36}],\"types\"", "\"type\":35}],\"types\""),
    ];
    for (from, to) in cases {
        assert_eq!(run_g11_perturbation(from, to), Verdict::Reject);
    }
}

#[test]
fn twobool_does_not_earn_indexed_inductive_authority() {
    assert_eq!(
        run_g11_perturbation(
            "\"name\":10,\"numIndices\":0,\"numNested\":0",
            "\"name\":10,\"numIndices\":1,\"numNested\":0",
        ),
        Verdict::Unknown
    );
}

#[test]
fn twobool_does_not_earn_recursive_or_unsafe_authority() {
    assert_eq!(
        run_g11_perturbation(
            "\"ctors\":[11],\"isRec\":false",
            "\"ctors\":[11],\"isRec\":true",
        ),
        Verdict::Unknown
    );
    assert_eq!(
        run_g11_perturbation(
            "\"types\":[{\"all\":[10],\"ctors\":[11],\"isRec\":false,\"isReflexive\":false,\"isUnsafe\":false",
            "\"types\":[{\"all\":[10],\"ctors\":[11],\"isRec\":false,\"isReflexive\":false,\"isUnsafe\":true",
        ),
        Verdict::Unknown
    );
}

#[test]
fn shared_closed_inductive_engine_matches_sealed_g9_g10_g11_verdict_vector() {
    let g9 = include_str!("../evidence/residuals/G9-001/fixture.ndjson");
    let g10 = include_str!("../evidence/residuals/G10-001/fixture.ndjson");
    let g11 = include_str!("../evidence/residuals/G11-001/fixture.ndjson");
    let cases = [
        ("G9 exact", g9.to_owned(), Verdict::Accept),
        (
            "G9 recursor metadata",
            g9.replacen("\"k\":false", "\"k\":true", 1),
            Verdict::Reject,
        ),
        ("G10 exact", g10.to_owned(), Verdict::Accept),
        (
            "G10 constructor index",
            g10.replacen("\"cidx\":0", "\"cidx\":1", 1),
            Verdict::Reject,
        ),
        (
            "G10 rule body",
            g10.replacen(
                "\"ctor\":2,\"nfields\":0,\"rhs\":18",
                "\"ctor\":2,\"nfields\":0,\"rhs\":21",
                1,
            ),
            Verdict::Reject,
        ),
        ("G11 exact", g11.to_owned(), Verdict::Accept),
        (
            "G11 constructor owner",
            g11.replacen("\"induct\":10,\"isUnsafe\"", "\"induct\":1,\"isUnsafe\"", 1),
            Verdict::Reject,
        ),
        (
            "G11 rule body",
            g11.replacen(
                "\"ctor\":11,\"nfields\":2,\"rhs\":42",
                "\"ctor\":11,\"nfields\":2,\"rhs\":41",
                1,
            ),
            Verdict::Reject,
        ),
        (
            "G11 indexed neighbor",
            g11.replacen(
                "\"name\":10,\"numIndices\":0,\"numNested\":0",
                "\"name\":10,\"numIndices\":1,\"numNested\":0",
                1,
            ),
            Verdict::Unknown,
        ),
        (
            "G11 recursive neighbor",
            g11.replacen(
                "\"ctors\":[11],\"isRec\":false",
                "\"ctors\":[11],\"isRec\":true",
                1,
            ),
            Verdict::Unknown,
        ),
    ];

    for (label, bytes, sealed_verdict) in cases {
        assert_eq!(
            metatron_kernel::run(Cursor::new(bytes)),
            sealed_verdict,
            "causal equivalence failed for {label}",
        );
    }
}
