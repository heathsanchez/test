use std::io::Cursor;

use metatron_kernel::checker::{check_export, Limits};
use metatron_kernel::parser::parse;
use metatron_kernel::verdict::Verdict;

const WITNESS: &str = include_str!("fixtures/good-setoid-v434.ndjson");

fn verdict(text: &str) -> Verdict {
    check_export(parse(Cursor::new(text)).unwrap().resolve().unwrap(), Limits::default())
}

#[test]
fn relation_and_proof_record_checks_exact_exported_setoid() {
    assert_eq!(verdict(WITNESS), Verdict::Accept);
}

#[test]
fn relation_and_proof_record_does_not_depend_on_type_name() {
    let renamed = WITNESS.replace("\"str\":\"Setoid\"", "\"str\":\"RelationCertificate\"");
    assert_eq!(verdict(&renamed), Verdict::Accept);
}

#[test]
fn relation_record_recursor_cannot_lie_about_field_annotation() {
    let mut records: Vec<serde_json::Value> = WITNESS.lines().map(|line| serde_json::from_str(line).unwrap()).collect();
    let record = records.iter_mut().find(|record| record.get("ie").and_then(|x| x.as_u64()) == Some(142)).unwrap();
    record["lam"]["type"] = serde_json::json!(0);
    let malformed = records.iter().map(|record| format!("{record}\n")).collect::<String>();
    assert_ne!(verdict(&malformed), Verdict::Accept);
}

#[test]
fn relation_record_requires_proof_even_when_all_annotations_agree() {
    let mut records: Vec<serde_json::Value> = WITNESS.lines().map(|line| serde_json::from_str(line).unwrap()).collect();
    for (id, node, ty) in [(116, "forallE", 2), (130, "forallE", 11), (141, "lam", 12)] {
        let record = records.iter_mut().find(|r| r.get("ie").and_then(|x| x.as_u64()) == Some(id)).unwrap();
        record[node]["type"] = serde_json::json!(ty);
    }
    let malformed = records.iter().map(|record| format!("{record}\n")).collect::<String>();
    assert_ne!(verdict(&malformed), Verdict::Accept);
}

#[test]
fn relation_record_requires_the_correct_result_universe() {
    let mut records: Vec<serde_json::Value> = WITNESS.lines().map(|line| serde_json::from_str(line).unwrap()).collect();
    let record = records.iter_mut().find(|r| r.get("ie").and_then(|x| x.as_u64()) == Some(113)).unwrap();
    record["forallE"]["body"] = serde_json::json!(0);
    let malformed = records.iter().map(|record| format!("{record}\n")).collect::<String>();
    assert_ne!(verdict(&malformed), Verdict::Accept);
}
