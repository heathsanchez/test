use std::io::Cursor;
use metatron_kernel::verdict::Verdict;
#[test]
fn native_nat_iota_does_not_require_exported_predecessor_literals() {
    assert_eq!(metatron_kernel::run(Cursor::new(include_str!("fixtures/good-sparse-native-nat-rec.ndjson"))),Verdict::Accept);
    assert_ne!(metatron_kernel::run(Cursor::new(include_str!("fixtures/bad-sparse-native-nat-rec.ndjson"))),Verdict::Accept);
}
