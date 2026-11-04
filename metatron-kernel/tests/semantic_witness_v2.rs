#![cfg(feature = "semantic-witness")]

use std::io::Cursor;

use metatron_kernel::run;
use metatron_kernel::run_dependency_witness_v2;
use metatron_kernel::verdict::Verdict;

const ORIGINAL: &str = include_str!("fixtures/good-theorem-use.ndjson");

#[test]
fn source_resolution_global_guards_and_local_reads_are_distinct() {
    // Removing the IdTable hook, environment channel hook or preflight-phase
    // transition must fail an independently asserted event here.
    let (verdict, whole_export_sha, witnessed, global) =
        run_dependency_witness_v2(Cursor::new(ORIGINAL));
    assert_eq!(verdict, Verdict::Accept);
    assert_eq!(verdict, run(Cursor::new(ORIGINAL)));
    assert_eq!(witnessed.len(), 2);
    assert_eq!(global.read_coverage, "PARTIAL");
    assert_eq!(global.verification_reuse_authority, "NONE");
    assert_eq!(global.proof_skips, 0);
    assert!(!global.source_resolution_reads.is_empty());
    assert!(global.source_resolution_reads.iter().any(|read|
        read.table == "expression" && read.access == "point" && read.present == Some(true)
    ));
    assert!(global.guards.iter().any(|guard|
        guard.stage == "quotient-source-ownership" && guard.result == "PASS"
    ));
    assert_eq!(witnessed[1].global_export_sha256, whole_export_sha);
    assert!(witnessed[1].table_reads.iter().any(|read|
        read.table == "expression" && read.access == "point" && read.present == Some(true)
    ));
    assert!(witnessed[1].environment_reads.iter().any(|read|
        read.channel == "constant" && read.name_id == Some(1) && read.present == Some(true)
    ));
    assert_eq!(witnessed[1].read_coverage, "PARTIAL");
    assert_eq!(witnessed[1].proof_skips, 0);
    assert_eq!(run_dependency_witness_v2(Cursor::new(ORIGINAL)),
               (verdict, whole_export_sha, witnessed, global));
}

#[test]
fn later_global_quotient_owner_forgery_is_exposed_and_cannot_admit_prefix() {
    let forged = format!(
        "{ORIGINAL}{{\"in\":10,\"str\":{{\"pre\":0,\"str\":\"NotQuot\"}}}}\n\
         {{\"quot\":{{\"kind\":\"type\",\"levelParams\":[],\"name\":10,\"type\":0}}}}\n"
    );
    let (verdict, forged_sha, witnessed, global) =
        run_dependency_witness_v2(Cursor::new(&forged));
    assert_eq!(verdict, Verdict::Reject);
    assert_eq!(verdict, run(Cursor::new(&forged)));
    assert_ne!(forged_sha, run_dependency_witness_v2(Cursor::new(ORIGINAL)).1);
    assert!(witnessed.is_empty());
    assert!(global.guards.iter().any(|guard|
        guard.stage == "quotient-source-ownership" && guard.result == "REJECT"
    ));
    assert!(!global.guards.iter().any(|guard|guard.result == "PASS" &&
        guard.stage == "recursor-external-constructor"));
    assert_eq!(global.verification_reuse_authority, "NONE");
    assert_eq!(global.proof_skips, 0);
}

#[test]
fn failed_export_after_valid_prefix_keeps_diagnostics_but_no_admissions() {
    let source = format!("{ORIGINAL}{{\"ie\":999,\"strVal\":\"unqualified\"}}\n");
    let (verdict, _, witnessed, global) = run_dependency_witness_v2(Cursor::new(&source));
    assert_eq!(verdict, Verdict::Unknown);
    assert!(witnessed.is_empty());
    assert_eq!(global.verification_reuse_authority, "NONE");
    assert_eq!(global.proof_skips, 0);
}
