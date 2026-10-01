use std::io::Cursor;
use metatron_kernel::verdict::Verdict;
use serde_json::{Value, json};

fn records() -> Vec<Value> {
    include_str!("fixtures/iff-prefix.ndjson").lines()
        .map(|s| serde_json::from_str(s).unwrap()).collect()
}
fn run(rows: &[Value]) -> Verdict {
    let text = rows.iter().map(|r| r.to_string()+"\n").collect::<String>();
    metatron_kernel::run(Cursor::new(text.as_bytes()))
}
fn expr(rows: &mut [Value], id: u64) -> &mut Value {
    rows.iter_mut().find(|r| r["ie"].as_u64()==Some(id)).unwrap()
}
fn block(rows: &mut [Value]) -> &mut Value {
    &mut rows.iter_mut().find(|r| r.get("inductive").is_some()).unwrap()["inductive"]
}
#[test]
fn function_proof_pair_accepts() { assert_eq!(run(&records()), Verdict::Accept); }
#[test]
fn renamed_function_proof_pair_accepts() {
    let mut r=records();
    for row in &mut r {
        if row["in"].as_u64()==Some(1300) { row["str"]["str"]=json!("ProofArrows"); }
    }
    assert_eq!(run(&r), Verdict::Accept);
}
#[test]
fn either_function_field_returning_data_cannot_large_eliminate() {
    // Coherently change the constructor, minor and rule's corresponding
    // function codomain from a proposition to Prop itself (which is data).
    for ids in [[6142,1786,1262], [606,6153,6167]] {
        let mut r=records();
        for id in ids { expr(&mut r,id)["forallE"]["body"]=json!(2); }
        assert_ne!(run(&r), Verdict::Accept);
    }
}
#[test]
fn rule_binder_annotations_are_checked() {
    // The outer rule annotations and its two field annotations are part
    // of the exported reduction contract, even when the body is unchanged.
    for id in [6173,6172,6171,6170,6169,6168] {
        let mut r=records();
        expr(&mut r,id)["lam"]["type"]=json!(0); // motive universe sort
        assert_ne!(run(&r), Verdict::Accept, "binder {id}");
    }
}
#[test]
fn rule_field_order_is_checked() {
    let mut r=records();
    expr(&mut r,37)["app"]["arg"]=json!(6); // replace last field by another local
    assert_ne!(run(&r), Verdict::Accept);
}
#[test]
fn recursor_metadata_does_not_grant_authority() {
    for key in ["numParams","numIndices","numMinors","numMotives"] {
        let mut r=records(); block(&mut r)["recs"][0][key]=json!(9);
        assert_ne!(run(&r), Verdict::Accept);
    }
    let mut r=records(); block(&mut r)["recs"][0]["k"]=json!(true);
    assert_ne!(run(&r), Verdict::Accept);
}
#[test]
fn rule_metadata_is_checked() {
    for (key,value) in [("ctor",1300),("nfields",1)] {
        let mut r=records(); block(&mut r)["recs"][0]["rules"][0][key]=json!(value);
        assert_ne!(run(&r), Verdict::Accept);
    }
}
#[test]
fn recursive_indexed_and_unsafe_neighbors_stay_unsupported() {
    for (key,value) in [("isRec",json!(true)),("isReflexive",json!(true)),("isUnsafe",json!(true)),("numIndices",json!(1)),("numNested",json!(1))] {
        let mut r=records();block(&mut r)["types"][0][key]=value;
        assert_ne!(run(&r), Verdict::Accept);
    }
}
