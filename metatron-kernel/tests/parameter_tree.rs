use std::io::Cursor;
use metatron_kernel::verdict::Verdict;
const SOURCE:&str=include_str!("fixtures/good-parameter-tree.ndjson");
#[test]
fn parameter_tree_derives_payloads_and_both_recursive_hypotheses() {
    assert_eq!(metatron_kernel::run(Cursor::new(SOURCE)),Verdict::Accept);
}

fn mutate(update:impl FnOnce(&mut Vec<serde_json::Value>))->Verdict {
    let mut rows=SOURCE.lines().map(|s|serde_json::from_str(s).unwrap()).collect::<Vec<_>>();update(&mut rows);
    metatron_kernel::run(Cursor::new(rows.iter().map(|r|format!("{r}\n")).collect::<String>()))
}
#[test]
fn parameter_tree_requires_exact_parameter_and_induction_field_positions() {
    assert_ne!(mutate(|rows| {
        let rec=rows.last().unwrap()["inductive"]["recs"][0]["name"].as_u64().unwrap();
        let lookup=|id:u64|rows.iter().find(|r|r["ie"].as_u64()==Some(id)).unwrap();
        let calls=rows.iter().filter_map(|r| {
            let mut id=r["ie"].as_u64()?;let mut arity=0;
            loop {let e=lookup(id);if let Some(f)=e["app"]["fn"].as_u64() {arity+=1;id=f;} else {break;}}
            (arity==5 && lookup(id)["const"]["name"].as_u64()==Some(rec)).then_some(r["ie"].as_u64().unwrap())
        }).collect::<Vec<_>>();
        assert_eq!(calls.len(),2);
        let wrong=lookup(calls[0])["app"]["arg"].clone();
        rows.iter_mut().find(|r|r["ie"].as_u64()==Some(calls[1])).unwrap()["app"]["arg"]=wrong;
    }),Verdict::Accept,"the second IH cannot recur on the first field");
    assert_ne!(mutate(|rows| {
        let ctor=rows.last().unwrap()["inductive"]["ctors"][1]["type"].as_u64().unwrap();
        let mut id=ctor;
        for _ in 0..2 {id=rows.iter().find(|r|r["ie"].as_u64()==Some(id)).unwrap()["forallE"]["body"].as_u64().unwrap();}
        let recursive=rows.iter().find(|r|r["ie"].as_u64()==Some(id)).unwrap()["forallE"]["type"].as_u64().unwrap();
        let nat=serde_json::json!(1);
        rows.iter_mut().find(|r|r["ie"].as_u64()==Some(recursive)).unwrap()["app"]["arg"]=nat;
    }),Verdict::Accept,"recursive fields must preserve the fixed parameter");
    assert_eq!(metatron_kernel::run(Cursor::new(SOURCE.replace("ParameterTree","RenamedTree"))),Verdict::Accept);
}
