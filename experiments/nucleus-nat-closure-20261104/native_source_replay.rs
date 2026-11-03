use std::process::{Command,Stdio};
use std::fs::File;
fn verdict(name:&str)->i32{
 let path=std::path::Path::new(env!("CARGO_MANIFEST_DIR")).join("tests/fixtures/native-source-replay").join(name);
 Command::new(env!("CARGO_BIN_EXE_metatron-kernel")).stdin(Stdio::from(File::open(path).unwrap())).status().unwrap().code().unwrap()
}
#[test]fn original_nat_arithmetic_prefix_accepts(){assert_eq!(verdict("nat-original.ndjson"),0);}
#[test]fn original_proof_cannot_gain_false_goal_or_wrong_operator_universes(){
 for name in ["false-goal.ndjson","pred-universe.ndjson","sub-universe.ndjson"]{assert!(matches!(verdict(name),1|2),"{name}");}
}
