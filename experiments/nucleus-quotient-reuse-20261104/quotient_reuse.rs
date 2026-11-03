use std::process::{Command,Stdio};
use std::fs::File;
fn verdict(name:&str)->i32{
 let path=std::path::Path::new(env!("CARGO_MANIFEST_DIR")).join("tests/fixtures/quotient-reuse").join(name);
 Command::new(env!("CARGO_BIN_EXE_metatron-kernel")).stdin(Stdio::from(File::open(path).unwrap())).status().unwrap().code().unwrap()
}
#[test]fn original_source_owned_quotient_proof_accepts(){assert_eq!(verdict("authentic.ndjson"),0);}
#[test]fn independently_exposed_indirect_quotient_beta_accepts(){assert_eq!(verdict("indirect-beta.ndjson"),0);}
#[test]fn original_forged_theorem_is_rejected(){assert_eq!(verdict("mutated.ndjson"),1);}
#[test]fn original_full_export_quotient_prefix_accepts(){assert_eq!(verdict("full-prefix.ndjson"),0);}
#[test]fn same_source_proof_cannot_inhabit_false(){assert!(matches!(verdict("full-prefix-forged.ndjson"),1|2));}
