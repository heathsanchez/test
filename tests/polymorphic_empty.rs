use metatron_kernel::verdict::Verdict;
use serde_json::{Value,json};
use std::io::Cursor;
const SOURCE:&str=include_str!("fixtures/good-polymorphic-empty.ndjson");
fn rows()->Vec<Value>{SOURCE.lines().map(|l|serde_json::from_str(l).unwrap()).collect()}
fn run(rows:Vec<Value>)->Verdict {metatron_kernel::run(Cursor::new(rows.iter().map(|r|format!("{r}\n")).collect::<String>()))}
#[test]
fn polymorphic_empty_derives_its_independent_large_eliminator() {
    assert_eq!(run(rows()),Verdict::Accept);
    assert_eq!(metatron_kernel::run(Cursor::new(SOURCE.replace("\"str\": \"Empty\"","\"str\": \"RenamedEmpty\""))),Verdict::Accept);
}
#[test]
fn polymorphic_empty_refuses_wrong_owner_universe_and_false_metadata() {
    for mutation in 0..3 {
        let mut rows=rows();
        if mutation==0 {rows.iter_mut().find(|r|r["ie"]==1).unwrap()["const"]["us"]=json!([2]);}
        else {let b=rows.iter_mut().find(|r|r.get("inductive").is_some()).unwrap();
            if mutation==1 {b["inductive"]["types"][0]["isRec"]=json!(true);}
            else {b["inductive"]["recs"][0]["levelParams"]=json!([3,3]);}}
        assert_ne!(run(rows),Verdict::Accept);
    }
}
