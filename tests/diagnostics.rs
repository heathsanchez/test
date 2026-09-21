#![cfg(feature = "diagnostics")]

use std::io::Cursor;

#[test]
fn operation_counters_are_deterministic_and_observational_only() {
    let bytes = include_bytes!("../evidence/residuals/G11-001/fixture.ndjson");
    let first = metatron_kernel::run_with_diagnostics(Cursor::new(bytes));
    let second = metatron_kernel::run_with_diagnostics(Cursor::new(bytes));

    assert_eq!(first, second);
    assert_eq!(first.verdict, metatron_kernel::verdict::Verdict::Accept);
    assert!(first.operations.declarations > 0);
    assert!(first.operations.inductive_signatures > 0);
    assert!(first.operations.type_judgments > 0);
}
