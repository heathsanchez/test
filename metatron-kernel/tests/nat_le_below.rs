use metatron_kernel::verdict::Verdict;
use serde_json::{Value, json};
use std::io::Cursor;
fn records() -> Vec<Value> {
    include_str!("fixtures/nat_le_below_prefix.ndjson")
        .lines()
        .map(|s| serde_json::from_str(s).unwrap())
        .collect()
}
fn run(r: Vec<Value>) -> Verdict {
    metatron_kernel::run(Cursor::new(
        r.into_iter()
            .map(|r| r.to_string())
            .collect::<Vec<_>>()
            .join("\n"),
    ))
}
#[test]
fn indexed_recursive_below_prefix_is_accepted() {
    assert_eq!(run(records()), Verdict::Accept);
}
#[test]
fn below_metadata_cannot_supply_missing_authority() {
    for (section, field, value) in [
        ("types", "numIndices", json!(1)),
        ("types", "isRec", json!(false)),
        ("types", "isReflexive", json!(true)),
        ("recs", "k", json!(true)),
        ("recs", "numParams", json!(1)),
    ] {
        let mut r = records();
        let b = r.last_mut().unwrap().get_mut("inductive").unwrap();
        b[section][0][field] = value;
        assert_ne!(run(r), Verdict::Accept, "{section}.{field}");
    }
}
#[test]
fn below_step_rule_requires_recursive_call_on_exact_recursive_field() {
    let mut r = records();
    let mut rhs = r.last().unwrap()["inductive"]["recs"][0]["rules"][1]["rhs"]
        .as_u64()
        .unwrap();
    for _ in 0..9 {
        rhs = r.iter().find(|r| r["ie"].as_u64() == Some(rhs)).unwrap()["lam"]["body"]
            .as_u64()
            .unwrap();
    }
    let recursive = r.iter().find(|r| r["ie"].as_u64() == Some(rhs)).unwrap()["app"]["arg"]
        .as_u64()
        .unwrap();
    let zero = r.iter().find(|r| r.get("bvar") == Some(&json!(0))).unwrap()["ie"].clone();
    r.iter_mut()
        .find(|r| r["ie"].as_u64() == Some(recursive))
        .unwrap()["app"]["arg"] = zero;
    assert_ne!(run(r), Verdict::Accept);
}
