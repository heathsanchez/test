#![cfg(feature = "semantic-witness")]

use std::io::Cursor;

use metatron_kernel::run;
use metatron_kernel::run_dependency_witness;
use metatron_kernel::verdict::Verdict;

const ORIGINAL: &str = include_str!("fixtures/good-theorem-use.ndjson");

#[test]
fn checked_theorem_emits_real_read_and_conservative_global_barrier() {
    // Removing the actual Environment::get hook must make this test fail.
    let (verdict, sha256, witnessed) = run_dependency_witness(Cursor::new(ORIGINAL));
    assert_eq!(verdict, Verdict::Accept);
    assert_eq!(verdict, run(Cursor::new(ORIGINAL)));
    assert_eq!(witnessed.len(), 2);
    assert_eq!(witnessed[0].declaration.name, "pImpliesP");
    assert_eq!(witnessed[1].declaration.name, "thmProof");
    assert!(witnessed[1].constant_reads.iter().any(|read|
        read.name_id == 1 && read.present
    ));
    for witness in &witnessed {
        assert_eq!(witness.global_export_sha256, sha256);
        assert_eq!(witness.read_coverage, "PARTIAL");
        assert_eq!(witness.verification_reuse_authority, "NONE");
        assert_eq!(witness.proof_skips, 0);
    }
    let repeated = run_dependency_witness(Cursor::new(ORIGINAL));
    assert_eq!(repeated.0, verdict);
    assert_eq!(repeated.1, sha256);
    assert_eq!(repeated.2, witnessed);
}

#[test]
fn global_quotient_owner_forgery_rejects_even_with_unmodified_theorem_prefix() {
    // V3's counterexample: the theorem-local candidate identity still matches.
    let forged = format!(
        "{ORIGINAL}{{\"in\":10,\"str\":{{\"pre\":0,\"str\":\"NotQuot\"}}}}\n\
         {{\"quot\":{{\"kind\":\"type\",\"levelParams\":[],\"name\":10,\"type\":0}}}}\n"
    );
    assert_eq!(run(Cursor::new(&forged)), Verdict::Reject);
    let (verdict, source_sha256, witnessed) = run_dependency_witness(Cursor::new(&forged));
    assert_eq!(verdict, Verdict::Reject);
    assert!(witnessed.is_empty());
    assert_ne!(source_sha256, run_dependency_witness(Cursor::new(ORIGINAL)).1);
}

#[test]
fn rejected_unknown_and_malformed_exports_never_emit_admissions() {
    let outer_unknown = format!("{ORIGINAL}{{\"ie\":999,\"strVal\":\"unqualified\"}}\n");
    for (source, expected) in [
        (include_str!("fixtures/bad-self-theorem.ndjson"), Verdict::Reject),
        (include_str!("fixtures/unsupported-inductive.ndjson"), Verdict::Unknown),
        ("{not json}\n", Verdict::Error),
        (outer_unknown.as_str(), Verdict::Unknown),
    ] {
        assert_eq!(run(Cursor::new(source)), expected);
        let (actual, _sha256, witnessed) = run_dependency_witness(Cursor::new(source));
        assert_eq!(actual, expected);
        assert!(witnessed.is_empty());
    }
}
