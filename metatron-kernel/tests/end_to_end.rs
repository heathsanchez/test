use std::fs::File;
use std::io::BufReader;
use std::io::{Cursor, Write};
use std::path::PathBuf;
use std::process::{Command, Stdio};

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

fn run_with_g15_oracle(family: &str, bytes: String) -> Verdict {
    let candidate = metatron_kernel::run(Cursor::new(bytes.as_bytes()));
    let Ok(oracle) = std::env::var("METATRON_G15_ORACLE") else {
        return candidate;
    };

    let mut child = Command::new(oracle)
        .stdin(Stdio::piped())
        .stdout(Stdio::null())
        .stderr(Stdio::inherit())
        .spawn()
        .expect("sealed G15 oracle must start");
    child
        .stdin
        .take()
        .expect("sealed G15 oracle stdin")
        .write_all(bytes.as_bytes())
        .expect("sealed G15 oracle input");
    let exit = child.wait().expect("sealed G15 oracle must finish");
    let oracle_verdict = match exit.code() {
        Some(0) => Verdict::Accept,
        Some(1) => Verdict::Reject,
        Some(2) => Verdict::Unknown,
        code => panic!("sealed G15 oracle returned unexpected exit code {code:?}"),
    };
    assert_eq!(
        candidate, oracle_verdict,
        "G15 changed the sealed {family} observable verdict vector"
    );
    candidate
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
fn declared_recursive_binary_enum_is_unknown_before_closed_enum_validation() {
    let bytes = include_str!("../evidence/residuals/G10-001/fixture.ndjson");
    let perturbed = bytes.replacen(
        "\"ctors\":[2,3],\"isRec\":false",
        "\"ctors\":[2,3],\"isRec\":true",
        1,
    );
    assert_ne!(bytes, perturbed, "recursive perturbation source must exist");
    assert_eq!(
        metatron_kernel::run(Cursor::new(perturbed)),
        Verdict::Unknown
    );
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

fn run_g12_perturbations(replacements: &[(&str, &str)]) -> Verdict {
    let mut bytes = include_str!("../evidence/residuals/G12-001/fixture.ndjson").to_owned();
    for (from, to) in replacements {
        assert!(bytes.contains(from), "missing perturbation source: {from}");
        bytes = bytes.replacen(from, to, 1);
    }
    run_with_g15_oracle("G12", bytes)
}

#[test]
fn g12_001_exact_and_authority_is_accepted() {
    assert_eq!(run_g12_perturbations(&[]), Verdict::Accept);
}

#[test]
fn and_parameter_and_field_order_are_derived_not_trusted() {
    let cases: &[&[(&str, &str)]] = &[
        &[
            (
                "\"forallE\":{\"binderInfo\":\"default\",\"body\":9,\"name\":5,\"type\":3}",
                "\"forallE\":{\"binderInfo\":\"default\",\"body\":9,\"name\":5,\"type\":14}",
            ),
            (
                "\"forallE\":{\"binderInfo\":\"default\",\"body\":8,\"name\":6,\"type\":3}",
                "\"forallE\":{\"binderInfo\":\"default\",\"body\":8,\"name\":6,\"type\":7}",
            ),
        ],
        &[
            (
                "\"app\":{\"arg\":5,\"fn\":4},\"ie\":6",
                "\"app\":{\"arg\":7,\"fn\":4},\"ie\":6",
            ),
            (
                "\"app\":{\"arg\":7,\"fn\":6},\"ie\":8",
                "\"app\":{\"arg\":5,\"fn\":6},\"ie\":8",
            ),
        ],
        &[(
            "\"numFields\":2,\"numParams\":2,\"type\":12",
            "\"numFields\":1,\"numParams\":2,\"type\":12",
        )],
        &[(
            "\"numFields\":2,\"numParams\":2,\"type\":12",
            "\"numFields\":2,\"numParams\":2,\"type\":11",
        )],
    ];

    for replacements in cases {
        assert_eq!(run_g12_perturbations(replacements), Verdict::Reject);
    }
}

#[test]
fn and_recursor_rule_and_metadata_are_derived_not_trusted() {
    let cases: &[(&str, &str)] = &[
        ("\"types\":[{\"all\":[1]", "\"types\":[{\"all\":[]"),
        ("\"cidx\":0,\"induct\":1", "\"cidx\":1,\"induct\":1"),
        ("\"cidx\":0,\"induct\":1", "\"cidx\":0,\"induct\":4"),
        (
            "\"numMinors\":1,\"numMotives\":1",
            "\"numMinors\":0,\"numMotives\":1",
        ),
        ("\"numParams\":2,\"rules\"", "\"numParams\":1,\"rules\""),
        (
            "\"ctor\":4,\"nfields\":2,\"rhs\":40",
            "\"ctor\":1,\"nfields\":2,\"rhs\":40",
        ),
        (
            "\"ctor\":4,\"nfields\":2,\"rhs\":40",
            "\"ctor\":4,\"nfields\":1,\"rhs\":40",
        ),
        (
            "\"ctor\":4,\"nfields\":2,\"rhs\":40",
            "\"ctor\":4,\"nfields\":2,\"rhs\":39",
        ),
        ("\"name\":7,\"numIndices\":0", "\"name\":4,\"numIndices\":0"),
        ("\"rules\":[{\"ctor\":4", "\"rules\":[{\"ctor\":1"),
        ("\"type\":32}],\"types\"", "\"type\":31}],\"types\""),
    ];

    for (from, to) in cases {
        assert_eq!(run_g12_perturbations(&[(*from, *to)]), Verdict::Reject);
    }
}

#[test]
fn and_broader_neighbors_preserve_unknown() {
    let cases = [
        (
            "\"name\":1,\"numIndices\":0,\"numNested\":0",
            "\"name\":1,\"numIndices\":1,\"numNested\":0",
        ),
        (
            "\"ctors\":[4],\"isRec\":false",
            "\"ctors\":[4],\"isRec\":true",
        ),
        (
            "\"types\":[{\"all\":[1],\"ctors\":[4],\"isRec\":false,\"isReflexive\":false,\"isUnsafe\":false",
            "\"types\":[{\"all\":[1],\"ctors\":[4],\"isRec\":false,\"isReflexive\":false,\"isUnsafe\":true",
        ),
        (
            "\"cidx\":0,\"induct\":1,\"isUnsafe\":false",
            "\"cidx\":0,\"induct\":1,\"isUnsafe\":true",
        ),
        (
            "\"recs\":[{\"all\":[1],\"isUnsafe\":false",
            "\"recs\":[{\"all\":[1],\"isUnsafe\":true",
        ),
        (
            "\"numIndices\":0,\"numNested\":0",
            "\"numIndices\":0,\"numNested\":1",
        ),
        (
            "\"name\":1,\"numIndices\":0,\"numNested\":0,\"numParams\":2",
            "\"name\":1,\"numIndices\":0,\"numNested\":0,\"numParams\":3",
        ),
    ];

    for (from, to) in cases {
        assert_eq!(run_g12_perturbations(&[(from, to)]), Verdict::Unknown);
    }
}

fn run_g13_perturbations(replacements: &[(&str, &str)]) -> Verdict {
    let mut bytes = include_str!("../evidence/residuals/G13-001/fixture.ndjson").to_owned();
    for (from, to) in replacements {
        assert!(bytes.contains(from), "missing perturbation source: {from}");
        bytes = bytes.replacen(from, to, 1);
    }
    run_with_g15_oracle("G13", bytes)
}

#[test]
fn g13_001_exact_prod_authority_is_accepted() {
    assert_eq!(run_g13_perturbations(&[]), Verdict::Accept);
}

#[test]
fn prod_universe_telescope_and_result_level_are_derived_not_trusted() {
    let cases: &[&[(&str, &str)]] = &[
        &[(
            "\"levelParams\":[2,3],\"name\":1",
            "\"levelParams\":[2],\"name\":1",
        )],
        &[(
            "\"levelParams\":[2,3],\"name\":1",
            "\"levelParams\":[3,2],\"name\":1",
        )],
        &[("{\"ie\":0,\"sort\":3}", "{\"ie\":0,\"sort\":4}")],
        &[("{\"ie\":1,\"sort\":4}", "{\"ie\":1,\"sort\":3}")],
        &[("{\"il\":5,\"max\":[3,4]}", "{\"il\":5,\"max\":[3,3]}")],
        &[(
            "\"levelParams\":[2,3],\"name\":6",
            "\"levelParams\":[3,2],\"name\":6",
        )],
        &[(
            "\"levelParams\":[10,2,3],\"name\":9",
            "\"levelParams\":[10,3,2],\"name\":9",
        )],
        &[("\"us\":[1,2]},\"ie\":6", "\"us\":[2,1]},\"ie\":6")],
        &[("\"us\":[1,2]},\"ie\":20", "\"us\":[2,1]},\"ie\":20")],
    ];

    for replacements in cases {
        assert_eq!(run_g13_perturbations(replacements), Verdict::Reject);
    }
}

#[test]
fn prod_constructor_recursor_rule_and_metadata_are_derived_not_trusted() {
    let cases: &[(&str, &str)] = &[
        ("\"types\":[{\"all\":[1]", "\"types\":[{\"all\":[]"),
        ("\"cidx\":0,\"induct\":1", "\"cidx\":1,\"induct\":1"),
        ("\"cidx\":0,\"induct\":1", "\"cidx\":0,\"induct\":6"),
        (
            "\"app\":{\"arg\":7,\"fn\":6},\"ie\":8",
            "\"app\":{\"arg\":9,\"fn\":6},\"ie\":8",
        ),
        (
            "\"app\":{\"arg\":9,\"fn\":8},\"ie\":10",
            "\"app\":{\"arg\":7,\"fn\":8},\"ie\":10",
        ),
        (
            "\"numFields\":2,\"numParams\":2,\"type\":14",
            "\"numFields\":1,\"numParams\":2,\"type\":14",
        ),
        (
            "\"numMinors\":1,\"numMotives\":1",
            "\"numMinors\":0,\"numMotives\":1",
        ),
        ("\"numParams\":2,\"rules\"", "\"numParams\":1,\"rules\""),
        (
            "\"ctor\":6,\"nfields\":2,\"rhs\":42",
            "\"ctor\":1,\"nfields\":2,\"rhs\":42",
        ),
        (
            "\"ctor\":6,\"nfields\":2,\"rhs\":42",
            "\"ctor\":6,\"nfields\":1,\"rhs\":42",
        ),
        (
            "\"ctor\":6,\"nfields\":2,\"rhs\":42",
            "\"ctor\":6,\"nfields\":2,\"rhs\":41",
        ),
        ("\"name\":9,\"numIndices\":0", "\"name\":6,\"numIndices\":0"),
        ("\"type\":34}],\"types\"", "\"type\":33}],\"types\""),
    ];

    for (from, to) in cases {
        assert_eq!(run_g13_perturbations(&[(*from, *to)]), Verdict::Reject);
    }
}

#[test]
fn prod_broader_neighbors_preserve_unknown() {
    let cases = [
        (
            "\"name\":1,\"numIndices\":0,\"numNested\":0",
            "\"name\":1,\"numIndices\":1,\"numNested\":0",
        ),
        (
            "\"ctors\":[6],\"isRec\":false",
            "\"ctors\":[6],\"isRec\":true",
        ),
        (
            "\"types\":[{\"all\":[1],\"ctors\":[6],\"isRec\":false,\"isReflexive\":false,\"isUnsafe\":false",
            "\"types\":[{\"all\":[1],\"ctors\":[6],\"isRec\":false,\"isReflexive\":false,\"isUnsafe\":true",
        ),
        (
            "\"cidx\":0,\"induct\":1,\"isUnsafe\":false",
            "\"cidx\":0,\"induct\":1,\"isUnsafe\":true",
        ),
        (
            "\"recs\":[{\"all\":[1],\"isUnsafe\":false",
            "\"recs\":[{\"all\":[1],\"isUnsafe\":true",
        ),
        (
            "\"numIndices\":0,\"numNested\":0",
            "\"numIndices\":0,\"numNested\":1",
        ),
        (
            "\"name\":1,\"numIndices\":0,\"numNested\":0,\"numParams\":2",
            "\"name\":1,\"numIndices\":0,\"numNested\":0,\"numParams\":3",
        ),
        (
            "\"forallE\":{\"binderInfo\":\"default\",\"body\":2,\"name\":5,\"type\":1},\"ie\":3",
            "\"forallE\":{\"binderInfo\":\"default\",\"body\":2,\"name\":5,\"type\":19},\"ie\":3",
        ),
    ];

    for (from, to) in cases {
        assert_eq!(run_g13_perturbations(&[(from, to)]), Verdict::Unknown);
    }
}

#[test]
fn g13_candidate_preserves_the_sealed_g12_behavior_vector() {
    let exact_and = include_str!("../evidence/residuals/G12-001/fixture.ndjson");
    let cases = [
        ("And exact", exact_and.to_owned(), Verdict::Accept),
        (
            "And malformed result",
            exact_and.replacen(
                "\"app\":{\"arg\":7,\"fn\":6},\"ie\":8",
                "\"app\":{\"arg\":5,\"fn\":6},\"ie\":8",
                1,
            ),
            Verdict::Reject,
        ),
        (
            "And indexed neighbor",
            exact_and.replacen(
                "\"name\":1,\"numIndices\":0,\"numNested\":0",
                "\"name\":1,\"numIndices\":1,\"numNested\":0",
                1,
            ),
            Verdict::Unknown,
        ),
    ];

    for (label, bytes, sealed_verdict) in cases {
        assert_eq!(
            metatron_kernel::run(Cursor::new(bytes)),
            sealed_verdict,
            "G12 differential mismatch for {label}",
        );
    }
}

fn run_g14_perturbations(replacements: &[(&str, &str)]) -> Verdict {
    let mut bytes = include_str!("../evidence/residuals/G14-001/fixture.ndjson").to_owned();
    for (from, to) in replacements {
        assert!(bytes.contains(from), "missing perturbation source: {from}");
        bytes = bytes.replacen(from, to, 1);
    }
    run_with_g15_oracle("G14", bytes)
}

#[test]
fn g14_001_exact_pprod_authority_is_accepted() {
    assert_eq!(run_g14_perturbations(&[]), Verdict::Accept);
}

#[test]
fn pprod_sort_telescope_and_result_level_are_derived_not_trusted() {
    let cases: &[&[(&str, &str)]] = &[
        &[(
            "\"levelParams\":[2,3],\"name\":1",
            "\"levelParams\":[2],\"name\":1",
        )],
        &[(
            "\"levelParams\":[2,3],\"name\":1",
            "\"levelParams\":[3,2],\"name\":1",
        )],
        &[("{\"ie\":0,\"sort\":1}", "{\"ie\":0,\"sort\":2}")],
        &[("{\"ie\":1,\"sort\":2}", "{\"ie\":1,\"sort\":1}")],
        &[("{\"il\":5,\"max\":[4,2]}", "{\"il\":5,\"max\":[4,1]}")],
        &[(
            "\"levelParams\":[2,3],\"name\":6",
            "\"levelParams\":[3,2],\"name\":6",
        )],
        &[(
            "\"levelParams\":[10,2,3],\"name\":9",
            "\"levelParams\":[10,3,2],\"name\":9",
        )],
        &[("\"us\":[1,2]},\"ie\":6", "\"us\":[2,1]},\"ie\":6")],
        &[("\"us\":[1,2]},\"ie\":20", "\"us\":[2,1]},\"ie\":20")],
        &[("{\"ie\":18,\"sort\":6}", "{\"ie\":18,\"sort\":1}")],
    ];

    for replacements in cases {
        assert_eq!(run_g14_perturbations(replacements), Verdict::Reject);
    }
}

#[test]
fn pprod_constructor_recursor_rule_and_metadata_are_derived_not_trusted() {
    let cases: &[(&str, &str)] = &[
        ("\"types\":[{\"all\":[1]", "\"types\":[{\"all\":[]"),
        ("\"cidx\":0,\"induct\":1", "\"cidx\":1,\"induct\":1"),
        ("\"cidx\":0,\"induct\":1", "\"cidx\":0,\"induct\":6"),
        (
            "\"app\":{\"arg\":7,\"fn\":6},\"ie\":8",
            "\"app\":{\"arg\":9,\"fn\":6},\"ie\":8",
        ),
        (
            "\"app\":{\"arg\":9,\"fn\":8},\"ie\":10",
            "\"app\":{\"arg\":7,\"fn\":8},\"ie\":10",
        ),
        (
            "\"numFields\":2,\"numParams\":2,\"type\":14",
            "\"numFields\":1,\"numParams\":2,\"type\":14",
        ),
        (
            "\"numMinors\":1,\"numMotives\":1",
            "\"numMinors\":0,\"numMotives\":1",
        ),
        ("\"numParams\":2,\"rules\"", "\"numParams\":1,\"rules\""),
        (
            "\"ctor\":6,\"nfields\":2,\"rhs\":42",
            "\"ctor\":1,\"nfields\":2,\"rhs\":42",
        ),
        (
            "\"ctor\":6,\"nfields\":2,\"rhs\":42",
            "\"ctor\":6,\"nfields\":1,\"rhs\":42",
        ),
        (
            "\"ctor\":6,\"nfields\":2,\"rhs\":42",
            "\"ctor\":6,\"nfields\":2,\"rhs\":41",
        ),
        ("\"name\":9,\"numIndices\":0", "\"name\":6,\"numIndices\":0"),
        ("\"type\":34}],\"types\"", "\"type\":33}],\"types\""),
    ];

    for (from, to) in cases {
        assert_eq!(run_g14_perturbations(&[(*from, *to)]), Verdict::Reject);
    }
}

#[test]
fn pprod_broader_neighbors_preserve_unknown() {
    let cases = [
        (
            "indexed",
            "\"name\":1,\"numIndices\":0,\"numNested\":0",
            "\"name\":1,\"numIndices\":1,\"numNested\":0",
        ),
        (
            "recursive",
            "\"ctors\":[6],\"isRec\":false",
            "\"ctors\":[6],\"isRec\":true",
        ),
        (
            "unsafe type",
            "\"types\":[{\"all\":[1],\"ctors\":[6],\"isRec\":false,\"isReflexive\":false,\"isUnsafe\":false",
            "\"types\":[{\"all\":[1],\"ctors\":[6],\"isRec\":false,\"isReflexive\":false,\"isUnsafe\":true",
        ),
        (
            "unsafe constructor",
            "\"cidx\":0,\"induct\":1,\"isUnsafe\":false",
            "\"cidx\":0,\"induct\":1,\"isUnsafe\":true",
        ),
        (
            "unsafe recursor",
            "\"recs\":[{\"all\":[1],\"isUnsafe\":false",
            "\"recs\":[{\"all\":[1],\"isUnsafe\":true",
        ),
        (
            "nested",
            "\"numIndices\":0,\"numNested\":0",
            "\"numIndices\":0,\"numNested\":1",
        ),
        (
            "broader parameter count",
            "\"name\":1,\"numIndices\":0,\"numNested\":0,\"numParams\":2",
            "\"name\":1,\"numIndices\":0,\"numNested\":0,\"numParams\":3",
        ),
        (
            "dependent parameter",
            "\"forallE\":{\"binderInfo\":\"default\",\"body\":2,\"name\":5,\"type\":1},\"ie\":3",
            "\"forallE\":{\"binderInfo\":\"default\",\"body\":2,\"name\":5,\"type\":19},\"ie\":3",
        ),
        (
            "dependent field",
            "\"forallE\":{\"binderInfo\":\"default\",\"body\":11,\"name\":7,\"type\":5},\"ie\":12",
            "\"forallE\":{\"binderInfo\":\"default\",\"body\":11,\"name\":7,\"type\":17},\"ie\":12",
        ),
    ];

    for (label, from, to) in cases {
        assert_eq!(
            run_g14_perturbations(&[(from, to)]),
            Verdict::Unknown,
            "PProd broader-neighbor boundary failed for {label}",
        );
    }
}

#[test]
fn g14_candidate_preserves_the_sealed_g13_behavior_vector() {
    let exact_prod = include_str!("../evidence/residuals/G13-001/fixture.ndjson");
    let cases = [
        ("Prod exact", exact_prod.to_owned(), Verdict::Accept),
        (
            "Prod malformed result",
            exact_prod.replacen(
                "\"app\":{\"arg\":9,\"fn\":8},\"ie\":10",
                "\"app\":{\"arg\":7,\"fn\":8},\"ie\":10",
                1,
            ),
            Verdict::Reject,
        ),
        (
            "Prod indexed neighbor",
            exact_prod.replacen(
                "\"name\":1,\"numIndices\":0,\"numNested\":0",
                "\"name\":1,\"numIndices\":1,\"numNested\":0",
                1,
            ),
            Verdict::Unknown,
        ),
    ];

    for (label, bytes, sealed_verdict) in cases {
        assert_eq!(
            metatron_kernel::run(Cursor::new(bytes)),
            sealed_verdict,
            "G13 differential mismatch for {label}",
        );
    }
}

#[test]
fn g15_shared_representation_earns_no_fourth_family() {
    let pprod = include_str!("../evidence/residuals/G14-001/fixture.ndjson");
    let renamed = pprod.replacen("\"str\":\"PProd\"", "\"str\":\"PProd2\"", 1);

    assert_eq!(
        run_with_g15_oracle("renamed fourth family", renamed),
        Verdict::Unknown,
    );
}

#[test]
fn g15_leaves_frozen_punit_residual_unknown() {
    let punit = include_str!("../evidence/residuals/G16-001/fixture.ndjson").to_owned();

    assert_eq!(
        run_with_g15_oracle("PUnit boundary", punit),
        Verdict::Unknown,
    );
}


fn sealed_pre_g16_verdict(bytes: &str) -> Option<Verdict> {
    let Ok(oracle) = std::env::var("METATRON_G16_ORACLE") else {
        return None;
    };
    let mut child = Command::new(oracle)
        .stdin(Stdio::piped())
        .stdout(Stdio::null())
        .stderr(Stdio::inherit())
        .spawn()
        .expect("sealed pre-G16 oracle must start");
    child
        .stdin
        .take()
        .expect("sealed pre-G16 oracle stdin")
        .write_all(bytes.as_bytes())
        .expect("sealed pre-G16 oracle input");
    let exit = child.wait().expect("sealed pre-G16 oracle must finish");
    Some(match exit.code() {
        Some(0) => Verdict::Accept,
        Some(1) => Verdict::Reject,
        Some(2) => Verdict::Unknown,
        code => panic!("sealed pre-G16 oracle returned unexpected exit code {code:?}"),
    })
}

fn run_g16_perturbations(replacements: &[(&str, &str)]) -> Verdict {
    let mut bytes = include_str!("../evidence/residuals/G16-001/fixture.ndjson").to_owned();
    for (from, to) in replacements {
        assert!(bytes.contains(from), "missing perturbation source: {from}");
        bytes = bytes.replacen(from, to, 1);
    }
    if let Some(oracle) = sealed_pre_g16_verdict(&bytes) {
        assert_eq!(
            oracle,
            Verdict::Unknown,
            "G16 authority was already present at the sealed pre-G16 boundary",
        );
    }
    metatron_kernel::run(Cursor::new(bytes))
}

#[test]
fn g16_001_exact_punit_authority_is_accepted() {
    assert_eq!(run_g16_perturbations(&[]), Verdict::Accept);
}

#[test]
fn punit_sort_constructor_recursor_and_rule_are_derived_not_trusted() {
    let cases: &[(&str, &str)] = &[
        (
            "\"levelParams\":[2],\"name\":1",
            "\"levelParams\":[5],\"name\":1",
        ),
        ("{\"ie\":0,\"sort\":1}", "{\"ie\":0,\"sort\":2}"),
        ("\"all\":[1],\"ctors\":[3]", "\"all\":[1],\"ctors\":[]"),
        ("\"all\":[1],\"ctors\":[3]", "\"all\":[1],\"ctors\":[3,3]"),
        ("\"cidx\":0,\"induct\":1", "\"cidx\":1,\"induct\":1"),
        ("\"cidx\":0,\"induct\":1", "\"cidx\":0,\"induct\":4"),
        (
            "\"numFields\":0,\"numParams\":0,\"type\":1",
            "\"numFields\":1,\"numParams\":0,\"type\":1",
        ),
        (
            "\"numFields\":0,\"numParams\":0,\"type\":1",
            "\"numFields\":0,\"numParams\":1,\"type\":1",
        ),
        (
            "\"levelParams\":[5,2],\"name\":4",
            "\"levelParams\":[2,5],\"name\":4",
        ),
        (
            "\"numMinors\":1,\"numMotives\":1",
            "\"numMinors\":0,\"numMotives\":1",
        ),
        (
            "\"ctor\":3,\"nfields\":0,\"rhs\":13",
            "\"ctor\":1,\"nfields\":0,\"rhs\":13",
        ),
        (
            "\"ctor\":3,\"nfields\":0,\"rhs\":13",
            "\"ctor\":3,\"nfields\":1,\"rhs\":13",
        ),
        (
            "\"ctor\":3,\"nfields\":0,\"rhs\":13",
            "\"ctor\":3,\"nfields\":0,\"rhs\":12",
        ),
        ("\"type\":11}],\"types\"", "\"type\":10}],\"types\""),
    ];

    for (from, to) in cases {
        assert_eq!(run_g16_perturbations(&[(*from, *to)]), Verdict::Reject);
    }
}

#[test]
fn punit_broader_neighbors_preserve_unknown() {
    let cases = [
        (
            "\"name\":1,\"numIndices\":0,\"numNested\":0",
            "\"name\":1,\"numIndices\":1,\"numNested\":0",
        ),
        (
            "\"ctors\":[3],\"isRec\":false",
            "\"ctors\":[3],\"isRec\":true",
        ),
        (
            "\"isRec\":false,\"isReflexive\":false",
            "\"isRec\":false,\"isReflexive\":true",
        ),
        (
            "\"numIndices\":0,\"numNested\":0",
            "\"numIndices\":0,\"numNested\":1",
        ),
        (
            "\"types\":[{\"all\":[1],\"ctors\":[3],\"isRec\":false,\"isReflexive\":false,\"isUnsafe\":false",
            "\"types\":[{\"all\":[1],\"ctors\":[3],\"isRec\":false,\"isReflexive\":false,\"isUnsafe\":true",
        ),
        (
            "\"cidx\":0,\"induct\":1,\"isUnsafe\":false",
            "\"cidx\":0,\"induct\":1,\"isUnsafe\":true",
        ),
        (
            "\"recs\":[{\"all\":[1],\"isUnsafe\":false",
            "\"recs\":[{\"all\":[1],\"isUnsafe\":true",
        ),
    ];
    for (from, to) in cases {
        assert_eq!(run_g16_perturbations(&[(from, to)]), Verdict::Unknown);
    }
}

#[test]
fn punit_law_does_not_authorize_a_renamed_family() {
    let bytes = include_str!("../evidence/residuals/G16-001/fixture.ndjson");
    let renamed = bytes.replacen("\"str\":\"PUnit\"", "\"str\":\"PUnit2\"", 1);
    assert_ne!(bytes, renamed);
    assert_eq!(metatron_kernel::run(Cursor::new(renamed)), Verdict::Unknown);
}
