use std::io::Cursor;
use metatron_kernel::verdict::Verdict;
use serde_json::{Value, json};
fn records() -> Vec<Value> {
    include_str!("fixtures/record3-shape.ndjson").lines()
        .map(|s| serde_json::from_str(s).unwrap()).collect()
}
fn run(rows: &[Value]) -> Verdict {
    let text=rows.iter().map(|r|r.to_string()+"\n").collect::<String>();
    metatron_kernel::run(Cursor::new(text.as_bytes()))
}
fn expr(rows: &mut [Value], id: u64) -> &mut Value {
    rows.iter_mut().find(|r|r["ie"].as_u64()==Some(id)).unwrap()
}
fn block(rows: &mut [Value]) -> &mut Value {
    &mut rows.iter_mut().find(|r|r.get("inductive").is_some()).unwrap()["inductive"]
}
#[test]
fn closed_three_data_fields_accept() {assert_eq!(run(&records()),Verdict::Accept);}
#[test]
fn renamed_closed_three_data_fields_accept() {
    let mut r=records();
    for row in &mut r {if row["in"].as_u64()==Some(1682){row["str"]["str"]=json!("TripleData");}}
    assert_eq!(run(&r),Verdict::Accept);
}
#[test]
fn each_field_universe_is_checked() {
    for ids in [[8031,8040,8046],[8030,8039,8045],[8029,8038,8044]] {
        let mut r=records();
        for (id,kind) in ids.into_iter().zip(["forallE","forallE","lam"]) {
            expr(&mut r,id)[kind]["type"]=json!(0); // Type itself exceeds record universe
        }
        assert_ne!(run(&r),Verdict::Accept);
    }
}
#[test]
fn record_rule_annotations_are_checked() {
    for id in [8048,8047,8046,8045,8044] {
        let mut r=records();expr(&mut r,id)["lam"]["type"]=json!(0);
        assert_ne!(run(&r),Verdict::Accept);
    }
}
#[test]
fn record_rule_and_metadata_are_checked() {
    for (key,value) in [("nfields",2),("ctor",1682)] {
        let mut r=records();block(&mut r)["recs"][0]["rules"][0][key]=json!(value);
        assert_ne!(run(&r),Verdict::Accept);
    }
    let mut r=records();expr(&mut r,3496)["app"]["arg"]=json!(0);
    assert_ne!(run(&r),Verdict::Accept);
}
#[test]
fn record_broader_neighbors_remain_unsupported() {
    for (key,value) in [("isRec",json!(true)),("isReflexive",json!(true)),("isUnsafe",json!(true)),("numIndices",json!(1)),("numParams",json!(1))] {
        let mut r=records();block(&mut r)["types"][0][key]=value;
        assert_ne!(run(&r),Verdict::Accept);
    }
}
