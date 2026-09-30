use metatron_kernel::verdict::Verdict;
use serde_json::{Value, json};
use std::io::Cursor;

fn char_records() -> Vec<Value> {
    include_str!("fixtures/char_prefix.ndjson")
        .lines()
        .map(|line| serde_json::from_str(line).unwrap())
        .collect()
}
fn run(records: Vec<Value>) -> Verdict {
    let data = records
        .into_iter()
        .map(|r| r.to_string())
        .collect::<Vec<_>>()
        .join("\n");
    metatron_kernel::run(Cursor::new(data))
}
#[test]
fn dependent_data_and_proof_record_checks_actual_char_prefix() {
    assert_eq!(run(char_records()), Verdict::Accept);
}
#[test]
fn record_admission_preserves_metadata_and_recursor_controls() {
    for (section, field, value) in [
        ("types", "isRec", json!(true)),
        ("types", "numIndices", json!(1)),
        ("ctors", "numFields", json!(1)),
        ("recs", "k", json!(true)),
        ("recs", "numMinors", json!(2)),
    ] {
        let mut records = char_records();
        let block = records
            .iter_mut()
            .rev()
            .find_map(|r| r.get_mut("inductive"))
            .unwrap();
        block[section][0][field] = value;
        assert_ne!(run(records), Verdict::Accept, "{section}.{field}");
    }
}
#[test]
fn record_rule_cannot_swap_dependent_fields() {
    let mut records = char_records();
    let mut rhs = records
        .iter()
        .rev()
        .find_map(|r| r.get("inductive"))
        .unwrap()["recs"][0]["rules"][0]["rhs"]
        .as_u64()
        .unwrap();
    for _ in 0..4 {
        rhs = records
            .iter()
            .find(|r| r["ie"].as_u64() == Some(rhs))
            .unwrap()["lam"]["body"]
            .as_u64()
            .unwrap();
    }
    let outer = records
        .iter()
        .find(|r| r["ie"].as_u64() == Some(rhs))
        .unwrap();
    let fun = outer["app"]["fn"].as_u64().unwrap();
    let first_arg = records
        .iter()
        .find(|r| r["ie"].as_u64() == Some(fun))
        .unwrap()["app"]["arg"]
        .clone();
    records
        .iter_mut()
        .find(|r| r["ie"].as_u64() == Some(rhs))
        .unwrap()["app"]["arg"] = first_arg;
    assert_ne!(run(records), Verdict::Accept);
}

fn small_record() -> Vec<Value> {
    include_str!("fixtures/data_proof_record.ndjson")
        .lines()
        .map(|line| serde_json::from_str(line).unwrap())
        .collect()
}
#[test]
fn data_proof_schema_is_independent_of_char_name() {
    assert_eq!(run(small_record()), Verdict::Accept);
}
#[test]
fn data_universe_cannot_exceed_record_universe() {
    let mut r = small_record();
    r.iter_mut().find(|r| r["axiom"]["name"] == 1).unwrap()["axiom"]["type"] = json!(1); // Sort 2, versus record Sort 1
    assert_ne!(run(r), Verdict::Accept);
}
#[test]
fn second_field_must_be_a_proposition_for_this_schema() {
    let mut r = small_record();
    let pt = r.iter().find(|r| r["axiom"]["name"] == 2).unwrap()["axiom"]["type"]
        .as_u64()
        .unwrap();
    r.iter_mut().find(|r| r["ie"].as_u64() == Some(pt)).unwrap()["forallE"]["body"] = json!(0); // P : A -> Sort 1
    assert_ne!(run(r), Verdict::Accept);
}
#[test]
fn rule_lambda_annotations_are_checked() {
    let mut r = small_record();
    let rhs = r.last().unwrap()["inductive"]["recs"][0]["rules"][0]["rhs"]
        .as_u64()
        .unwrap();
    r.iter_mut()
        .find(|r| r["ie"].as_u64() == Some(rhs))
        .unwrap()["lam"]["type"] = json!(0);
    assert_ne!(run(r), Verdict::Accept);
}
