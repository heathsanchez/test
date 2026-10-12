use metatron_kernel::verdict::Verdict;
use serde_json::{Value,json};
use std::io::Cursor;
const SOURCE:&str=include_str!("fixtures/good-transport-projection.ndjson");
fn run(rows:Vec<Value>)->Verdict {
    metatron_kernel::run(Cursor::new(rows.iter().map(|r|format!("{r}\n")).collect::<String>()))
}
fn rows()->Vec<Value>{SOURCE.lines().map(|l|serde_json::from_str(l).unwrap()).collect()}
#[test]
fn checked_transport_projection_supplies_the_actual_function_type() {
    assert_eq!(run(rows()),Verdict::Accept);
}
#[test]
fn checked_transport_projection_refuses_an_out_of_range_field() {
    let mut rows=rows();
    for r in &mut rows {if r.get("proj").is_some(){r["proj"]["idx"]=json!(1);}}
    assert_ne!(run(rows),Verdict::Accept);
}
#[test]
fn checked_transport_projection_does_not_replace_incompatible_equality_indices() {
    let source=include_str!("fixtures/unsupported-transport-projection-indices.ndjson");
    assert_ne!(metatron_kernel::run(Cursor::new(source)),Verdict::Accept);
}
#[test]
fn checked_transport_projection_declines_when_the_judgment_budget_is_insufficient() {
    use metatron_kernel::checker::{check_export,Limits};
    let export=metatron_kernel::parser::parse(Cursor::new(SOURCE)).unwrap().resolve().unwrap();
    let mut limits=Limits::default();limits.judgment_steps=32;
    assert_ne!(check_export(export,limits),Verdict::Accept);
}
