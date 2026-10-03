use std::io::Cursor;
use metatron_kernel::checker::{check_export, Limits};
use metatron_kernel::parser::parse;
use metatron_kernel::verdict::Verdict;

const WITNESS: &str = include_str!("fixtures/good-closed-pair-v434.ndjson");

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
