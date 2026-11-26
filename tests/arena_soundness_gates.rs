//! Original (unmodified) negative Arena exports from lean-kernel-arena
//! commit 6c2d82164f1a2b1ac94aee62290fe78a3c3853fb, exporter 3.1.0.
//! SHA-256 of each fixture, in test order:
//! e144c9d6a65cc1fbd26a0875788306d72e7690eae61d12d2967a3c4ea7c3287c
//! 61cff0dc13e0287cd21541543b63fc47aa89bebf14d30f14766b4d74f5c77c8c
//! a366791c3deb8c259c8b5f03d61c5016879c1177756372fbd2302539d7c8e581
//! ebacb89b4e72a34aed58f4479e864f562c80ae110e26e7b839563e828cd08f07
//!
//! These two forgeries require full strict REJECT, not merely non-ACCEPT:
//! a negative-only proof-irrelevance check must not conceal UNKNOWN.

use std::io::Cursor;
use metatron_kernel::verdict::Verdict;

#[test]
fn indexed_bool_proposition_is_independently_checked_before_any_forged_proof() {
    let source = include_str!("fixtures/rec-rule-proof-irrel.ndjson");
    // Exact source prefix ending at `Box`. The later forged `J.rec` must
    // never influence the independent admission of this genuine inductive.
    let box_line = source
        .lines()
        .position(|line| line.starts_with("{\"inductive\":") && line.contains("\"induct\":12"))
        .expect("Arena export changed; requalify the source prefix");
    let prefix = source.lines().take(box_line + 1).collect::<Vec<_>>().join("\n");
    assert_eq!(metatron_kernel::run(Cursor::new(prefix)), Verdict::Accept);
}

#[test]
fn proof_irrelevance_forgeries_reject_after_source_qualified_indexed_inductive() {
    let rule = include_str!("fixtures/rec-rule-proof-irrel.ndjson");
    let ty = include_str!("fixtures/rec-type-proof-irrel.ndjson");
    assert_eq!(metatron_kernel::run(Cursor::new(rule)), Verdict::Reject);
    assert_eq!(metatron_kernel::run(Cursor::new(ty)), Verdict::Reject);
}

#[test]
fn matching_index_identity_is_not_refuted_by_the_mismatch_guard() {
    let source = include_str!("fixtures/rec-type-proof-irrel.ndjson");
    // Change only the forged `Box.mk true` inside `@id (Box false) ...`
    // to `Box.mk false`. The resulting `id` application has no index
    // contradiction; the still-unsupported Q family must remain UNKNOWN.
    let consistent = source.replacen(
        "\"app\":{\"arg\":14,\"fn\":34},\"ie\":314",
        "\"app\":{\"arg\":12,\"fn\":34},\"ie\":314",
        1,
    );
    assert_ne!(consistent, source, "requalify after exporter changes");
    let q_line = consistent
        .lines()
        .position(|line| line.starts_with("{\"inductive\":") && line.contains("\"induct\":92"))
        .expect("Arena Q source block absent");
    let prefix = consistent.lines().take(q_line + 1).collect::<Vec<_>>().join("\n");
    assert_eq!(metatron_kernel::run(Cursor::new(prefix)), Verdict::Unknown);
}

#[test]
fn nested_constructor_and_open_term_cache_forgeries_reject() {
    let nested = include_str!("fixtures/rec-rule-proof-irrel-nested.ndjson");
    let open = include_str!("fixtures/open-term-cache-context.ndjson");
    assert_eq!(metatron_kernel::run(Cursor::new(nested)), Verdict::Reject);
    assert_eq!(metatron_kernel::run(Cursor::new(open)), Verdict::Reject);
}
