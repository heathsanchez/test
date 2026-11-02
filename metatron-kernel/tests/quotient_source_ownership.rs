use std::io::Cursor;
use metatron_kernel::verdict::Verdict;

// Exact official Arena d7f74a9e67459e2c251d608f524dc5efc6dc223c fixture.
// No checker implementation is imported from another project.
const SOURCE:&str=include_str!("fixtures/arena-forged-quot-ind-d7f74a9.ndjson");

#[test]
fn quotient_induction_cannot_precede_its_source_primitives() {
    assert_eq!(metatron_kernel::run(Cursor::new(SOURCE)),Verdict::Reject);
}

#[test]
fn ordinary_definitions_cannot_supply_quotient_primitive_ownership() {
    let mut rows:Vec<serde_json::Value>=SOURCE.lines().map(|line|serde_json::from_str(line).unwrap()).collect();
    let index=rows.iter().position(|r|r.get("quot").is_some()).unwrap();
    let induction=rows.remove(index);
    // Quot and Quot.mk are ordinary definitions here, not quotient primitives.
    // Moving induction after them repairs ordering, not source authority.
    rows.insert(index+2,induction);
    let data=rows.iter().map(|r|r.to_string()).collect::<Vec<_>>().join("\n")+"\n";
    assert_eq!(metatron_kernel::run(Cursor::new(data)),Verdict::Reject);
}
