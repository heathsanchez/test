use metatron_kernel::verdict::Verdict;
use serde_json::{Value,json};
use std::io::Cursor;
fn witness()->Vec<Value>{include_str!("fixtures/good-proof-only-singleton.ndjson").lines().map(|l|serde_json::from_str(l).unwrap()).collect()}
fn run(rows:Vec<Value>)->Verdict{metatron_kernel::run(Cursor::new(rows.into_iter().map(|r|r.to_string()+"\n").collect::<String>()))}
#[test]
fn proof_only_singleton_checks_dependent_fields_under_all_five_parameters(){assert_eq!(run(witness()),Verdict::Accept);}
#[test]
fn proof_only_singleton_refuses_false_index_metadata(){let mut r=witness();r.last_mut().unwrap()["inductive"]["types"][0]["numIndices"]=json!(1);assert_ne!(run(r),Verdict::Accept);}
#[test]
fn proof_only_singleton_refuses_malformed_rule_and_universe(){
 for (key,value) in [("rhs",json!(0)),("levelParams",json!([]))] {
  let mut r=witness();let rec=&mut r.last_mut().unwrap()["inductive"]["recs"][0];
  if key=="rhs"{rec["rules"][0][key]=value;}else{rec[key]=value;}
  assert_ne!(run(r),Verdict::Accept);
 }
}
#[test]
fn proof_only_singleton_does_not_treat_a_data_parameter_as_a_proof(){
 let mut r=witness();
 // P is data Sort(1), so the constructor's h:P is not a proof.
 r.push(json!({"il":2,"succ":0}));r.push(json!({"ie":69,"sort":2}));
 for row in &mut r {if row["ie"].as_u64().is_some() {for k in ["forallE","lam"] {if row[k]["type"]==json!(0){row[k]["type"]=json!(69);}}}}
 assert_ne!(run(r),Verdict::Accept);
}

#[test]
fn proof_only_singleton_accepts_only_source_certified_parameter_and_field_erasure(){
 let rows:Vec<Value>=include_str!("fixtures/good-proof-only-singleton-wrapped.ndjson").lines().map(|l|serde_json::from_str(l).unwrap()).collect();
 assert_eq!(run(rows.clone()),Verdict::Accept);
 let mut bad=rows;let skip=bad.iter().find(|r|r["def"]["name"]==json!(7)).unwrap()["def"]["value"].as_u64().unwrap();
 let inner=bad.iter().find(|r|r["ie"]==json!(skip)).unwrap()["lam"]["body"].as_u64().unwrap();
 let other=bad.iter().find(|r|r["bvar"]==json!(0)).unwrap()["ie"].clone();
 bad.iter_mut().find(|r|r["ie"]==json!(inner)).unwrap()["lam"]["body"]=other;
 assert_ne!(run(bad),Verdict::Accept);
}
