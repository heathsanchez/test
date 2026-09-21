use std::fs::File;
use std::io::BufReader;
use std::path::PathBuf;

use metatron_kernel::verdict::Verdict;

fn run_fixture(name: &str) -> Verdict {
    let path = PathBuf::from(env!("CARGO_MANIFEST_DIR"))
        .join("tests")
        .join("fixtures")
        .join(name);
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
