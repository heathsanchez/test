use std::io::Cursor;

use metatron_kernel::verdict::Verdict;
use metatron_kernel::{run, run_observed};
use sha2::{Digest, Sha256};

const TWO_THEOREMS: &str = include_str!("fixtures/good-theorem-use.ndjson");
const INDUCTIVE: &str = include_str!("fixtures/good-closed-record-3.ndjson");

fn digest_hex(digest: &[u8; 32]) -> String {
    digest.iter().map(|byte| format!("{byte:02x}")).collect()
}

#[test]
fn mgso_observation_records_only_completed_authentic_declarations() {
    let original = run(Cursor::new(TWO_THEOREMS));
    let (verdict, digest, checked) = run_observed(Cursor::new(TWO_THEOREMS));
    assert_eq!(original, Verdict::Accept);
    assert_eq!(verdict, original);
    assert_eq!(
        digest_hex(&digest),
        "5e4664a6d4f05afbeff4e0af19681e88b2817c48787a9a281c4ba95d80483333"
    );
    assert_eq!(checked.len(), 2);
    assert_eq!(checked[0].index, 0);
    assert_eq!(checked[0].name, "pImpliesP");
    assert_eq!(checked[0].kind, "theorem");
    assert_eq!(checked[1].index, 1);
    assert_eq!(checked[1].name, "thmProof");
    assert_eq!(checked[1].kind, "theorem");
}

#[test]
fn mgso_observation_hashes_exact_source_bytes_not_parsed_equivalence() {
    let with_crlf = TWO_THEOREMS.replace('\n', "\r\n");
    let without_final_newline = TWO_THEOREMS.trim_end_matches('\n');
    let (base_verdict, base_sha, _) = run_observed(Cursor::new(TWO_THEOREMS));
    let (crlf_verdict, crlf_sha, _) = run_observed(Cursor::new(with_crlf));
    let (trimmed_verdict, trimmed_sha, _) = run_observed(Cursor::new(without_final_newline));
    assert_eq!(base_verdict, Verdict::Accept);
    assert_eq!(crlf_verdict, base_verdict);
    assert_eq!(trimmed_verdict, base_verdict);
    assert_ne!(base_sha, crlf_sha);
    assert_ne!(base_sha, trimmed_sha);
}

#[test]
fn mgso_observation_finishes_digest_even_after_parse_error() {
    let malformed = format!("{{not json}}\n{}", "trailing bytes".repeat(20000));
    let (verdict, digest, events) = run_observed(Cursor::new(malformed.as_bytes()));
    assert_eq!(verdict, Verdict::Error);
    assert!(events.is_empty());
    assert_eq!(
        digest.as_slice(),
        Sha256::digest(malformed.as_bytes()).as_slice()
    );
}

#[test]
fn mgso_observation_discards_partial_prefix_after_rejected_suffix() {
    let duplicate = TWO_THEOREMS
        .lines()
        .find(|line| line.contains("\"thm\""))
        .expect("genuine theorem");
    let input = format!("{TWO_THEOREMS}{duplicate}\n");
    let baseline = run(Cursor::new(&input));
    let (observed, _, checked) = run_observed(Cursor::new(&input));
    assert_eq!(baseline, Verdict::Reject);
    assert_eq!(observed, baseline);
    assert!(checked.is_empty());
}

#[test]
fn mgso_observation_does_not_promote_outer_string_guard_unknown() {
    let input = format!("{TWO_THEOREMS}{{\"ie\":999,\"strVal\":\"unqualified\"}}\n");
    assert_eq!(run(Cursor::new(&input)), Verdict::Unknown);
    let (observed, _, checked) = run_observed(Cursor::new(input));
    assert_eq!(observed, Verdict::Unknown);
    assert!(checked.is_empty());
}

#[test]
fn mgso_observation_preserves_forged_unknown_and_invalid_verdicts() {
    for (fixture, expected) in [
        (
            include_str!("fixtures/bad-self-theorem.ndjson"),
            Verdict::Reject,
        ),
        (
            include_str!("fixtures/unsupported-inductive.ndjson"),
            Verdict::Unknown,
        ),
        ("{not json}\n", Verdict::Error),
    ] {
        let fresh = run(Cursor::new(fixture));
        let (shadow, _, checked) = run_observed(Cursor::new(fixture));
        assert_eq!(fresh, expected);
        assert_eq!(shadow, fresh);
        assert!(checked.is_empty());
    }
}

#[test]
fn mgso_observation_includes_inductive_only_after_its_admission() {
    let baseline = run(Cursor::new(INDUCTIVE));
    let (observed, _, checked) = run_observed(Cursor::new(INDUCTIVE));
    assert_eq!(baseline, Verdict::Accept);
    assert_eq!(observed, baseline);
    assert_eq!(checked.len(), 3);
    for (index, event) in checked.iter().enumerate() {
        assert_eq!(event.index, index);
        assert_eq!(event.kind, "inductive");
        assert!(!event.name.is_empty());
    }
}
