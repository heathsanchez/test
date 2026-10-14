# Nat.pred source authorization

A checked custom Nat.pred := fun _ => 0 exposed an incorrect ACCEPT: Nucleus installed native predecessor reduction from its name, although pinned Lean 4.34.1 does not grant Nat.pred native arithmetic meaning. The checker now derives this optimization from the actual checked definition.

Admission requires an established exact closed Nat → Nat lambda, a formed source Nat domain and a fresh source-owned typed local. Before installation, one bounded evaluator owner reduces the actual RHS at zero to zero and at succ(local) to that same local. These two source reductions cover the qualified exhaustive Nat constructors and justify substitution at runtime. No desired result chooses a recursor rule. Definitions that fail certification continue through their checked source body.

Four custom/standard fixtures give ACCEPT / REJECT / ACCEPT / REJECT. The constant-zero custom definition fails successor certification, so its false predecessor claim is rejected. The full Rust suite passes 326 tests (17 ignored). Frozen196 preserves every prior verdict: default 118 ACCEPT / 71 REJECT / 7 UNKNOWN; origin and demand 119 ACCEPT / 71 REJECT / 6 UNKNOWN; zero wrong verdicts and errors. Full Init remains ACCEPT in origin/demand. This closes a newly discovered incorrect ACCEPT, not one of the six original UNKNOWN exports.

The exact isolated binary and source hashes are in derived-evidence.json; all runtime source files match the integrated production candidate byte for byte. frozen196.json records every input hash and verdict. The report's caller checkout commit is ancestry, not the uncommitted candidate's source identity; source hashes identify the candidate until committed CI qualification.

Earlier failed removal-only qualification is retained as frozen196-removal-only.json: 118/71/7 in every mode, losing Init at Nat.sub_le. The earlier 119/71/6 removal report used four additional unpromoted proof-transport runtime files and remains frozen196-unpromoted-foundation.json. It does not qualify the production removal-only patch.

Integrated CLI independently qualifies the same counts and every prior verdict in all three modes; 326 tests pass (17 ignored). Its binary SHA256 is b60989e15579805ca297a7134be77fd4d0fc84c51716a640d3f68ba1fe3638ac. The existing false-index and eta/constructor-alias protected controls both remain UNKNOWN/non-ACCEPT. See frozen196-integrated.json and integrated logs.
