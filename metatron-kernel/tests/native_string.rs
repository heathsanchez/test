use std::io::Cursor;
use metatron_kernel::verdict::Verdict;
const SOURCE:&str=include_str!("fixtures/good-native-string.ndjson");
#[test]
fn checked_utf8_string_carrier_types_native_literals() {
    assert_eq!(metatron_kernel::run(Cursor::new(SOURCE)),Verdict::Accept);
}
#[test]
fn renamed_or_forged_string_carrier_grants_no_literal_typing() {
    assert_ne!(metatron_kernel::run(Cursor::new(SOURCE.replace("String","RenamedString"))),Verdict::Accept);
    assert_ne!(metatron_kernel::run(Cursor::new(SOURCE.replace("IsValidUTF8","ArbitraryPredicate"))),Verdict::Accept);
}

fn literal_family_source(other:&str)->String {
    use serde_json::json;
    let mut source=SOURCE.to_string();
    for row in [
        json!({"in":100,"str":{"pre":0,"str":"LiteralCarrier"}}),
        json!({"in":101,"str":{"pre":0,"str":"literalWitness"}}),
        json!({"in":102,"str":{"pre":0,"str":"literalAlias"}}),
        json!({"ie":71,"forallE":{"name":4,"binderInfo":"default","type":39,"body":0}}),
        json!({"axiom":{"name":100,"levelParams":[],"type":71,"isUnsafe":false}}),
        json!({"ie":72,"const":{"name":100,"us":[]}}),
        json!({"ie":73,"app":{"fn":72,"arg":70}}),
        json!({"axiom":{"name":101,"levelParams":[],"type":73,"isUnsafe":false}}),
        json!({"ie":74,"strVal":other}),
        json!({"ie":75,"app":{"fn":72,"arg":74}}),
        json!({"ie":76,"const":{"name":101,"us":[]}}),
        json!({"def":{"name":102,"all":[102],"levelParams":[],"type":75,"value":76,"hints":"abbrev","safety":"safe"}}),
    ] {source.push_str(&row.to_string());source.push('\n');}
    source
}
#[test]
fn checked_identical_native_literals_convert_inside_an_opaque_type_family() {
    assert_eq!(metatron_kernel::run(Cursor::new(literal_family_source("_hyg🙂"))),Verdict::Accept);
}
#[test]
fn native_literal_congruence_does_not_identify_distinct_strings() {
    assert_ne!(metatron_kernel::run(Cursor::new(literal_family_source("_hyg🙃"))),Verdict::Accept);
}
