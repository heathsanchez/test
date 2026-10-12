use std::io::Cursor;
use metatron_kernel::verdict::Verdict;
const BASE: &str = r#"{"meta":{"format":{"version":"3.1.0"}}}
{"in":1,"str":{"pre":0,"str":"A"}}
{"in":2,"str":{"pre":0,"str":"a"}}
{"in":3,"str":{"pre":0,"str":"v"}}
{"il":1,"succ":0}
{"ie":0,"sort":1}
{"ie":1,"const":{"name":1,"us":[]}}
{"ie":2,"const":{"name":2,"us":[]}}
{"axiom":{"name":1,"levelParams":[],"type":0}}
{"axiom":{"name":2,"levelParams":[],"type":1}}
{"opaque":{"all":[3],"isUnsafe":false,"name":3,"levelParams":[],"type":1,"value":2}}
"#;
#[test]
fn checks_opaque_type_and_value_before_admission() {
    assert_eq!(metatron_kernel::run(Cursor::new(BASE)),Verdict::Accept);
    assert_ne!(metatron_kernel::run(Cursor::new(BASE.replace("\"value\":2", "\"value\":0"))),Verdict::Accept);
    assert_ne!(metatron_kernel::run(Cursor::new(BASE.replace("\"isUnsafe\":false", "\"isUnsafe\":true"))),Verdict::Accept);
}
#[test]
fn checked_opaque_bodies_are_not_delta_reduction_rules() {
    let source=BASE.replace("\"type\":1,\"value\":2", "\"type\":0,\"value\":1");
    let source=source+ r#"{"in":4,"str":{"pre":0,"str":"w"}}
{"ie":3,"const":{"name":3,"us":[]}}
{"opaque":{"all":[4],"isUnsafe":false,"name":4,"levelParams":[],"type":3,"value":2}}
"#;
    assert_ne!(metatron_kernel::run(Cursor::new(source)),Verdict::Accept);
}

#[test]
fn opaque_group_metadata_does_not_block_an_independently_closed_body() {
    let grouped=BASE.replace("{\"opaque\":", "{\"in\":4,\"str\":{\"pre\":0,\"str\":\"pending\"}}\n{\"opaque\":").replace("\"all\":[3]","\"all\":[3,4]");
    assert_eq!(metatron_kernel::run(Cursor::new(&grouped)),Verdict::Accept);
    for target in [3,4] {
        let circular=grouped.replace("{\"opaque\":",&format!("{{\"ie\":3,\"const\":{{\"name\":{target},\"us\":[]}}}}\n{{\"opaque\":" )).replace("\"value\":2","\"value\":3");
        assert_ne!(metatron_kernel::run(Cursor::new(circular)),Verdict::Accept);
    }
}
