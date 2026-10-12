use std::io::Cursor;
use metatron_kernel::verdict::Verdict;
#[test]
fn closed_field_enum_derives_all_constructor_equations() {
    assert_eq!(metatron_kernel::run(Cursor::new(include_str!("fixtures/good-closed-field-enum.ndjson"))), Verdict::Accept);
}
