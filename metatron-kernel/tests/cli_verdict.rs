use metatron_kernel::verdict::Verdict;

#[test]
fn arena_exit_codes_preserve_unknown() {
    assert_eq!(Verdict::Accept.exit_code(), 0);
    assert_eq!(Verdict::Reject.exit_code(), 1);
    assert_eq!(Verdict::Unknown.exit_code(), 2);
    assert_eq!(Verdict::Error.exit_code(), 3);
}
