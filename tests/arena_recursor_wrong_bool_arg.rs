//! Lean Kernel Arena 6c2d8216, unchanged `bugs/rec-rule-wrong-arg` export.
//! SHA-256 cf3b02e4dc0c8a3adcf912f09e81a2e467c7cc667b5c5c545b50ad03760eccc9.

use std::io::Cursor;
use metatron_kernel::verdict::Verdict;

const WRONG_BOOL_ARG: &str = include_str!("fixtures/arena-bugs-rec-rule-wrong-arg-6c2d8216.ndjson");

#[test]
fn a_recursor_that_discards_its_bool_field_is_rejected() {
    assert_eq!(metatron_kernel::run(Cursor::new(WRONG_BOOL_ARG)), Verdict::Reject);
}
