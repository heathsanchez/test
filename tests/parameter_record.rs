use std::io::Cursor;
use metatron_kernel::verdict::Verdict;
const SOURCE:&str=include_str!("fixtures/good-parameter-record.ndjson");
#[test]
fn checked_parameter_record_derives_twenty_one_field_telescope() {
    assert_eq!(metatron_kernel::run(Cursor::new(SOURCE)),Verdict::Accept);
}

fn mutate(update:impl FnOnce(&mut Vec<serde_json::Value>))->Verdict {
    let mut rows=SOURCE.lines().map(|s|serde_json::from_str(s).unwrap()).collect::<Vec<_>>();update(&mut rows);
    metatron_kernel::run(Cursor::new(rows.iter().map(|r|format!("{r}\n")).collect::<String>()))
}

#[test]
fn parameter_record_requires_field_universe_and_exact_rule_annotations() {
    assert_ne!(mutate(|rows| {
        let block=&rows.last().unwrap()["inductive"];
        let ctor=block["ctors"][0]["type"].as_u64().unwrap();
        let body=rows.iter().find(|r|r["ie"].as_u64()==Some(ctor)).unwrap()["forallE"]["body"].as_u64().unwrap();
        let sort=rows.iter().find(|r|r["ie"].as_u64()==Some(ctor)).unwrap()["forallE"]["type"].clone();
        rows.iter_mut().find(|r|r["ie"].as_u64()==Some(body)).unwrap()["forallE"]["type"]=sort;
    }),Verdict::Accept,"a field of Type (u+1) cannot fit a Type u carrier");
    assert_ne!(mutate(|rows| {
        let mut rhs=rows.last().unwrap()["inductive"]["recs"][0]["rules"][0]["rhs"].as_u64().unwrap();
        for _ in 0..3 {rhs=rows.iter().find(|r|r["ie"].as_u64()==Some(rhs)).unwrap()["lam"]["body"].as_u64().unwrap();}
        let wrong=rows.iter().find(|r|r["bvar"]==1).unwrap()["ie"].clone();
        rows.iter_mut().find(|r|r["ie"].as_u64()==Some(rhs)).unwrap()["lam"]["type"]=wrong;
    }),Verdict::Accept);
}

#[test]
fn parameter_record_namespace_does_not_supply_typing_authority() {
    assert_eq!(metatron_kernel::run(Cursor::new(SOURCE.replace("Operations","RenamedOperations"))),Verdict::Accept);
}
