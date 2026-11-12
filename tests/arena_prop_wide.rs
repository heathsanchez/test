//! Unchanged Lean Kernel Arena 6c2d8216 native export, generated with
//! `uv run lka.py build-test perf/prop-struct-projections`.
//! SHA-256: 20f2f293fb8e9b75da413b62a0ccc04390ec72594ff0d10c510150784952e8c0.
//! The 200 proof fields are a workload, not evidence that their proofs are interchangeable.

use std::io::Cursor;

use metatron_kernel::verdict::Verdict;

const WIDE: &str = include_str!("fixtures/arena-perf-prop-struct-projections-6c2d8216.ndjson");

#[test]
fn arena_200_proposition_fields_accept_at_standard_budget() {
    assert_eq!(metatron_kernel::run(Cursor::new(WIDE)), Verdict::Accept);
}

#[test]
fn wide_structural_admission_does_not_trust_a_false_recursor_field_count() {
    let forged = WIDE.replacen(
        "\"ctor\":113,\"nfields\":200,\"rhs\":5275",
        "\"ctor\":113,\"nfields\":199,\"rhs\":5275",
        1,
    );
    assert_ne!(forged, WIDE, "upstream fixture changed; review the witness");
    assert_ne!(metatron_kernel::run(Cursor::new(forged)), Verdict::Accept);
}
