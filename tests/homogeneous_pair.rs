use std::io::Cursor;
use metatron_kernel::verdict::Verdict;
const SOURCE:&str=include_str!("fixtures/good-homogeneous-pair.ndjson");
#[test]
fn same_universe_pair_derives_its_complete_telescope() {
    assert_eq!(metatron_kernel::run(Cursor::new(SOURCE)),Verdict::Accept);
}

fn mutate(mut update: impl FnMut(&mut serde_json::Value)) -> Verdict {
    let raw=SOURCE.lines().map(|line| {
        let mut row:serde_json::Value=serde_json::from_str(line).unwrap();
        update(&mut row);serde_json::to_string(&row).unwrap()+"\n"
    }).collect::<String>();
    metatron_kernel::run(Cursor::new(raw))
}

#[test]
fn homogeneous_pair_rejects_forged_universes_fields_and_rules() {
    // Alter the carrier result universe without altering either parameter.
    assert_ne!(mutate(|r| {if r["ie"]==37 {r["forallE"]["body"]=serde_json::json!(3);}}),Verdict::Accept);
    // The second field must have the second parameter's type.
    assert_ne!(mutate(|r| {if r["ie"]==40 {r["bvar"]=serde_json::json!(2);}}),Verdict::Accept);
    // A forged RHS field annotation cannot grant iota authority.
    assert_ne!(mutate(|r| {if r["ie"]==86 {r["bvar"]=serde_json::json!(4);}}),Verdict::Accept);
    // Reversing minor arguments changes the constructor equation.
    assert_ne!(mutate(|r| {if r["ie"]==90 {r["app"]["arg"]=serde_json::json!(89);} if r["ie"]==91 {r["app"]["arg"]=serde_json::json!(88);}}),Verdict::Accept);
    assert_ne!(mutate(|r| {if r["ie"]==87 {r["bvar"]=serde_json::json!(3);}}),Verdict::Accept);
}

#[test]
fn homogeneous_pair_admission_is_structural() {
    assert_eq!(metatron_kernel::run(Cursor::new(SOURCE.replace("SameUniversePair","RenamedPair"))),Verdict::Accept);
}
