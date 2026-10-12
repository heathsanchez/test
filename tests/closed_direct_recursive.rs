use std::io::Cursor;
use metatron_kernel::checker::{check_export, Limits};
use metatron_kernel::parser::parse;
use metatron_kernel::verdict::Verdict;
const SOURCE: &str = include_str!("fixtures/good-closed-direct-recursive.ndjson");
fn verdict(source: &str) -> Verdict {
    check_export(parse(Cursor::new(source)).unwrap().resolve().unwrap(), Limits::default())
}
#[test]
fn derives_direct_recursive_positions_and_equations() {
    assert_eq!(verdict(SOURCE), Verdict::Accept);
    assert_eq!(verdict(&SOURCE.replace("\"str\": \"Branch\"", "\"str\": \"Renamed\"")), Verdict::Accept);
}
#[test]
fn malformed_recursive_equations_are_not_certified() {
    let mut rows: Vec<serde_json::Value> = SOURCE.lines().map(|s| serde_json::from_str(s).unwrap()).collect();
    let rule = rows.last().unwrap()["inductive"]["recs"][0]["rules"][1]["rhs"].as_u64().unwrap();
    let rhs = rows.iter_mut().find(|r| r["ie"].as_u64() == Some(rule)).unwrap();
    rhs["lam"]["body"] = serde_json::json!(5); // replace the rule body with a free minor-shaped variable
    assert_ne!(verdict(&rows.iter().map(|r|format!("{r}\n")).collect::<String>()), Verdict::Accept);
}

#[test]
fn checks_recursive_metadata_and_every_exported_binder() {
    let rows: Vec<serde_json::Value> = SOURCE.lines().map(|s| serde_json::from_str(s).unwrap()).collect();
    let last = rows.len()-1;
    let mut variants = Vec::new();
    for key in ["isUnsafe", "isReflexive"] {
        let mut v=rows.clone();v[last]["inductive"]["types"][0][key]=serde_json::json!(true);variants.push(v);
    }
    let mut v=rows.clone();v[last]["inductive"]["recs"][0]["rules"][1]["nfields"]=serde_json::json!(1);variants.push(v);
    let mut v=rows.clone();v[last]["inductive"]["ctors"][1]["cidx"]=serde_json::json!(2);variants.push(v);
    let mut v=rows.clone();v[last]["inductive"]["recs"][0]["k"]=serde_json::json!(true);variants.push(v);
    // Mutate each original bound variable individually, exercising motive,
    // fields, induction hypotheses, result and recursive call arguments.
    for (i,row) in rows.iter().enumerate() {
        if let Some(index)=row["bvar"].as_u64() {
            if i < rows.iter().position(|r|r.get("inductive").is_some()).unwrap() { continue; }
            let mut v=rows.clone();v[i]["bvar"]=serde_json::json!(index+1);variants.push(v);
        }
    }
    for v in variants {
        assert_ne!(verdict(&v.iter().map(|r|format!("{r}\n")).collect::<String>()), Verdict::Accept);
    }
}
