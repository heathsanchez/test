use std::io::Cursor;
use metatron_kernel::{parser,syntax::Expr,verdict::Verdict};
const DEP:&str=include_str!("fixtures/let-metadata/canonical-let.ndjson");
const INDEP:&str=include_str!("fixtures/let-metadata/canonical-independent-let.ndjson");
#[test]fn parser_retains_explicit_flags_and_legacy_default(){
 for (source,expected) in [(DEP,false),(INDEP,true)] {
  let parsed=parser::parse(Cursor::new(source)).unwrap().resolve().unwrap();
  let bits=parsed.exprs.values().filter_map(|e|if let Expr::Let{nondep,..}=e{Some(*nondep)}else{None}).collect::<Vec<_>>();
  assert!(!bits.is_empty());assert!(bits.iter().all(|b|*b==expected));
 }
 let legacy="{\"ie\":0,\"sort\":0}\n{\"ie\":1,\"letE\":{\"type\":0,\"value\":0,\"body\":0}}\n";
 let parsed=parser::parse(Cursor::new(legacy)).unwrap().resolve().unwrap();
 assert!(parsed.exprs.values().any(|e|matches!(e,Expr::Let{nondep:false,..})));
 println!("Expr size {}",std::mem::size_of::<Expr>());
}
#[test]fn both_canonical_let_record_forms_accept(){for source in [DEP,INDEP]{assert_eq!(metatron_kernel::run(Cursor::new(source)),Verdict::Accept);}}
#[test]fn dependency_mismatches_cannot_grant_recursor_authority(){for source in [include_str!("fixtures/let-metadata/forged-let-nondep.ndjson"),include_str!("fixtures/let-metadata/forged-independent-let-nondep.ndjson")]{assert_ne!(metatron_kernel::run(Cursor::new(source)),Verdict::Accept);}}
#[test]fn explicit_non_boolean_dependency_metadata_is_rejected(){
 for bad in [serde_json::json!("true"),serde_json::json!(1),serde_json::Value::Null]{
  let mut rows=DEP.lines().map(|l|serde_json::from_str::<serde_json::Value>(l).unwrap()).collect::<Vec<_>>();
  rows.iter_mut().find(|r|r.get("letE").is_some()).unwrap()["letE"]["nondep"]=bad;
  let source=rows.iter().map(|r|format!("{r}\n")).collect::<String>();
  assert!(parser::parse(Cursor::new(source)).is_err());
 }
}
