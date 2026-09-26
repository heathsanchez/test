use std::io::Cursor;

use metatron_kernel::verdict::Verdict;
use serde_json::{Value, json};

fn fixture() -> Vec<Value> {
    include_str!("fixtures/heq-exact.ndjson")
        .lines()
        .map(|line| serde_json::from_str(line).unwrap())
        .collect()
}

fn check(rows: &[Value]) -> Verdict {
    let text = rows.iter().map(Value::to_string).collect::<Vec<_>>().join("\n") + "\n";
    metatron_kernel::run(Cursor::new(text))
}

#[test]
fn exact_heq_admission() {
    assert_eq!(check(&fixture()), Verdict::Accept);
}

#[test]
fn heq_universe_names_are_not_semantics() {
    let mut rows = fixture();
    for row in &mut rows {
        if row.get("in").and_then(Value::as_u64) == Some(2) {
            row["str"]["str"] = json!("other_universe");
        }
        if row.get("in").and_then(Value::as_u64) == Some(18) {
            row["str"]["str"] = json!("motive_universe");
        }
    }
    assert_eq!(check(&rows), Verdict::Accept);
}

#[test]
fn heq_malformed_metadata_never_gains_acceptance() {
    let paths = [
        ("/types/0/numParams", json!(1)),
        ("/types/0/numIndices", json!(1)),
        ("/types/0/ctors", json!([374])),
        ("/ctors/0/cidx", json!(1)),
        ("/ctors/0/induct", json!(373)),
        ("/ctors/0/numFields", json!(1)),
        ("/ctors/0/numParams", json!(1)),
        ("/recs/0/numIndices", json!(1)),
        ("/recs/0/k", json!(false)),
        ("/recs/0/levelParams", json!([2, 2])),
        ("/recs/0/levelParams", json!([2, 18])),
        ("/recs/0/rules/0/ctor", json!(374)),
        ("/recs/0/rules/0/nfields", json!(1)),
        ("/recs/0/rules/0/rhs", json!(1556)),
        ("/types/0/isUnsafe", json!(true)),
        ("/types/0/numNested", json!(1)),
    ];
    for (path, value) in paths {
        let mut rows = fixture();
        let block = &mut rows.last_mut().unwrap()["inductive"];
        *block.pointer_mut(path).unwrap() = value;
        let verdict = check(&rows);
        assert!(matches!(verdict, Verdict::Reject | Verdict::Unknown), "{path}: {verdict:?}");
    }
}

#[test]
fn heq_dependent_telescope_and_rule_mutations_never_gain_acceptance() {
    let mutations = [
        (1519_u64, "forallE", "type", 2_u64),
        (1524, "app", "arg", 6),
        (1530, "app", "arg", 6),
        (1531, "forallE", "body", 0),
        (1538, "app", "arg", 11),
        (1543, "app", "arg", 6),
        (1546, "app", "arg", 6),
        (1554, "lam", "body", 6),
        (1554, "lam", "type", 2),
    ];
    for (id, tag, key, value) in mutations {
        let mut rows = fixture();
        let row = rows.iter_mut().find(|r| r.get("ie").and_then(Value::as_u64) == Some(id)).unwrap();
        row[tag][key] = json!(value);
        let verdict = check(&rows);
        assert!(matches!(verdict, Verdict::Reject | Verdict::Unknown), "{id}/{tag}/{key}: {verdict:?}");
    }
}
