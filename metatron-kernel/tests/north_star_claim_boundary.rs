//! North Star characterization: kernel proof admission is relative to its
//! declaration environment, not an assertion of unqualified real-world truth.
//!
//! These tests change no checker rules and are not a soundness proof.

use std::io::Cursor;

use metatron_kernel::verdict::Verdict;

// A minimal NDJSON export in which P : Prop is explicitly postulated,
// assumedProof : P is explicitly postulated, and provedFromAssumption : P
// is a genuine proof term referring to assumedProof.
const ASSUMPTION_BOUND_PROOF: &str = concat!(
    "{\"meta\":{\"exporter\":{\"name\":\"lean4export\",\"version\":\"3.1.0\"},\"format\":{\"version\":\"3.1.0\"},\"lean\":{\"githash\":\"5045d0056413266e57c625dcd7c365b10e377c52\",\"version\":\"4.34.1\"}}}\n",
    "{\"in\":1,\"str\":{\"pre\":0,\"str\":\"P\"}}\n",
    "{\"in\":2,\"str\":{\"pre\":0,\"str\":\"assumedProof\"}}\n",
    "{\"in\":3,\"str\":{\"pre\":0,\"str\":\"provedFromAssumption\"}}\n",
    "{\"ie\":0,\"sort\":0}\n",
    "{\"axiom\":{\"name\":1,\"type\":0,\"levelParams\":[]}}\n",
    "{\"const\":{\"name\":1,\"us\":[]},\"ie\":1}\n",
    "{\"axiom\":{\"name\":2,\"type\":1,\"levelParams\":[]}}\n",
    "{\"const\":{\"name\":2,\"us\":[]},\"ie\":2}\n",
    "{\"thm\":{\"name\":3,\"type\":1,\"value\":2,\"all\":[3],\"levelParams\":[]}}\n",
);

#[test]
fn valid_theorem_can_depend_on_an_explicit_unproved_axiom() {
    // ACCEPT means a well-typed derivation in the supplied environment.
    // It does not mean that the unproved premise P was independently proved.
    assert_eq!(
        metatron_kernel::run(Cursor::new(ASSUMPTION_BOUND_PROOF)),
        Verdict::Accept
    );
}

#[test]
fn a_claimed_proof_without_the_necessary_assumption_does_not_accept() {
    let no_assumed_proof = ASSUMPTION_BOUND_PROOF.replace(
        "{\"axiom\":{\"name\":2,\"type\":1,\"levelParams\":[]}}\n",
        "",
    );
    assert_ne!(no_assumed_proof, ASSUMPTION_BOUND_PROOF);
    assert_ne!(
        metatron_kernel::run(Cursor::new(no_assumed_proof)),
        Verdict::Accept
    );
}

#[test]
fn claiming_the_proposition_is_its_own_proof_does_not_accept() {
    let forged = ASSUMPTION_BOUND_PROOF.replace(
        "\"value\":2,\"all\":[3]",
        "\"value\":1,\"all\":[3]",
    );
    assert_ne!(forged, ASSUMPTION_BOUND_PROOF);
    assert_ne!(metatron_kernel::run(Cursor::new(forged)), Verdict::Accept);
}
