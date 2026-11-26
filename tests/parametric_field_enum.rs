use std::io::Cursor;
use metatron_kernel::verdict::Verdict;
const SOURCE: &str = include_str!("fixtures/good-parametric-field-enum.ndjson");
#[test]
fn parametric_enum_checks_field_universes_and_rules() {
    assert_eq!(metatron_kernel::run(Cursor::new(SOURCE)),Verdict::Accept);
}
#[test]
fn parametric_enum_declines_binder_and_universe_mutants() {
    let rows: Vec<serde_json::Value> = SOURCE.lines().map(|s|serde_json::from_str(s).unwrap()).collect();
    let first=rows.iter().position(|r|r.get("inductive").is_some()).unwrap();
    for (i,row) in rows.iter().enumerate().skip(first+1) {
        if let Some(b)=row["bvar"].as_u64() {
            let mut v=rows.clone();v[i]["bvar"]=serde_json::json!(b+1);
            assert_ne!(metatron_kernel::run(Cursor::new(v.iter().map(|r|format!("{r}\n")).collect::<String>())),Verdict::Accept,"mutated variable at row {i}");
        }
    }
    // Mutate constructor fields to Type, outside the declared Type 0 carrier.
    let mut v=rows.clone();let last=v.len()-1;
    let mut ids=Vec::new();
    for ctor in rows[last]["inductive"]["ctors"].as_array().unwrap() {
        let mut id=ctor["type"].as_u64().unwrap();
        for _ in 0..3 {id=rows.iter().find(|r|r["ie"].as_u64()==Some(id)).unwrap()["forallE"]["body"].as_u64().unwrap();}
        for _ in 0..2 {let r=rows.iter().find(|r|r["ie"].as_u64()==Some(id)).unwrap();ids.push(r["forallE"]["type"].as_u64().unwrap());id=r["forallE"]["body"].as_u64().unwrap();}
    }
    // The minor/rule annotations are separate source nodes; changing only a
    // ctor field must already decline, irrespective of the later mismatch.
    for id in ids {let r=v.iter_mut().find(|r|r["ie"].as_u64()==Some(id)).unwrap();*r=serde_json::json!({"ie":id,"sort":1});}
    assert_ne!(metatron_kernel::run(Cursor::new(v.iter().map(|r|format!("{r}\n")).collect::<String>())),Verdict::Accept);
}

#[test]
fn missing_rules_decline_without_panicking() {
    let mut rows:Vec<serde_json::Value>=SOURCE.lines().map(|s|serde_json::from_str(s).unwrap()).collect();
    rows.last_mut().unwrap()["inductive"]["recs"][0]["rules"]=serde_json::json!([]);
    assert_ne!(metatron_kernel::run(Cursor::new(rows.iter().map(|r|format!("{r}\n")).collect::<String>())),Verdict::Accept);
}
