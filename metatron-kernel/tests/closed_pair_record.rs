use std::io::Cursor;
use metatron_kernel::checker::{check_export, Limits};
use metatron_kernel::parser::parse;
use metatron_kernel::verdict::Verdict;

const WITNESS: &str = include_str!("fixtures/good-closed-pair-v434.ndjson");

#[test]
fn closed_record_arity_is_checked_by_its_general_telescope() {
    for source in [include_str!("fixtures/good-closed-record-3.ndjson"), include_str!("fixtures/good-closed-record-4.ndjson")] {
        assert_eq!(verdict(source), Verdict::Accept);
    }
    for source in [include_str!("fixtures/bad-closed-record-3-universe.ndjson"), include_str!("fixtures/bad-closed-record-3-rule.ndjson")] {
        assert_ne!(verdict(source), Verdict::Accept);
    }
}

fn verdict(text: &str) -> Verdict {
    check_export(parse(Cursor::new(text)).unwrap().resolve().unwrap(), Limits::default())
}

fn mutate(edit: impl FnOnce(&mut Vec<serde_json::Value>)) -> Verdict {
    let mut records = WITNESS.lines().map(|s| serde_json::from_str(s).unwrap()).collect();
    edit(&mut records);
    verdict(&records.iter().map(|r| format!("{r}\n")).collect::<String>())
}

#[test]
fn closed_pair_record_has_a_derived_contract() {
    let export = parse(Cursor::new(WITNESS)).unwrap().resolve().unwrap();
    assert_eq!(check_export(export, Limits::default()), Verdict::Accept);
}

#[test]
fn closed_pair_record_does_not_depend_on_its_name() {
    let renamed = WITNESS.replace("\"str\":\"C\"", "\"str\":\"ClosedPair\"");
    let export = parse(Cursor::new(renamed)).unwrap().resolve().unwrap();
    assert_eq!(check_export(export, Limits::default()), Verdict::Accept);
}

#[test]
fn closed_pair_record_checks_field_universe_even_when_annotations_agree() {
    assert_ne!(mutate(|rows| {
        for (id, node) in [(74,"forallE"),(75,"forallE"),(81,"forallE"),(82,"forallE"),(88,"lam"),(89,"lam")] {
            let field = rows.iter_mut().find(|r| r.get("ie").and_then(|v| v.as_u64()) == Some(id)).unwrap();
            field[node]["type"] = serde_json::json!(42);
        }
    }), Verdict::Accept);
}

#[test]
fn closed_pair_record_checks_rule_field_annotations() {
    assert_ne!(mutate(|rows| {
        let field = rows.iter_mut().find(|r| r.get("ie").and_then(|v| v.as_u64()) == Some(89)).unwrap();
        field["lam"]["type"] = serde_json::json!(42);
    }), Verdict::Accept);
}

#[test]
fn closed_pair_record_does_not_admit_recursive_metadata() {
    assert_ne!(mutate(|rows| {
        let decl = rows.iter_mut().find(|r| r.get("inductive").and_then(|v| v.get("types")).and_then(|v| v.get(0)).and_then(|v| v.get("name")).and_then(|v| v.as_u64()) == Some(23)).unwrap();
        decl["inductive"]["types"][0]["isRec"] = serde_json::json!(true);
    }), Verdict::Accept);
}

#[test]
fn closed_pair_checks_each_closed_field_without_requiring_identical_type_ids() {
    let mut rows=WITNESS.lines().map(|s|serde_json::from_str::<serde_json::Value>(s).unwrap()).collect::<Vec<_>>();
    let block=rows.last().unwrap()["inductive"].clone();
    let lookup=|id:u64| rows.iter().find(|r|r["ie"].as_u64()==Some(id)).unwrap().clone();
    let ctor=block["ctors"][0]["type"].as_u64().unwrap();
    let first_type=lookup(ctor)["forallE"]["type"].clone();
    let second_ctor=lookup(ctor)["forallE"]["body"].as_u64().unwrap();
    let rec=block["recs"][0]["type"].as_u64().unwrap();
    let second_rec=lookup(rec)["forallE"]["body"].as_u64().unwrap();
    let minor=lookup(second_rec)["forallE"]["type"].as_u64().unwrap();
    let second_minor=lookup(minor)["forallE"]["body"].as_u64().unwrap();
    let mut rhs=block["recs"][0]["rules"][0]["rhs"].as_u64().unwrap();
    for _ in 0..3 {rhs=lookup(rhs)["lam"]["body"].as_u64().unwrap();}
    for (id,kind) in [(second_ctor,"forallE"),(second_minor,"forallE"),(rhs,"lam")] {
        rows.iter_mut().find(|r|r["ie"].as_u64()==Some(id)).unwrap()[kind]["type"]=serde_json::json!(1000);
    }
    let at=rows.len()-1;
    for r in [serde_json::json!({"in":1000,"str":{"pre":0,"str":"ClosedAlias"}}),serde_json::json!({"ie":1000,"const":{"name":1000,"us":[]}}),serde_json::json!({"def":{"name":1000,"all":[1000],"levelParams":[],"type":block["types"][0]["type"],"value":first_type,"hints":"abbrev","safety":"safe"}})].into_iter().rev() {rows.insert(at,r);}
    assert_eq!(verdict(&rows.iter().map(|r|format!("{r}\n")).collect::<String>()),Verdict::Accept);
}

#[test]
fn closed_pair_rejects_a_second_field_alone_above_the_carrier_universe() {
    assert_ne!(mutate(|rows| {
        // Keep the first field Nat and agree on all second-field annotations.
        // Expr 42 is Type 0, whose type Type 1 exceeds this Type 0 carrier.
        for (id,node) in [(74,"forallE"),(81,"forallE"),(88,"lam")] {
            rows.iter_mut().find(|r|r["ie"].as_u64()==Some(id)).unwrap()[node]["type"]=serde_json::json!(42);
        }
    }), Verdict::Accept);
}
