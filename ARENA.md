# Nucleus beta entry

Nucleus is the independently implemented Rust checker in this directory. It
is separate from the sokonanoda-derived MathGraph Flash checker.

Build with Rust 1.99.1:

```sh
cargo build --locked --release --features diagnostics --manifest-path metatron-kernel/Cargo.toml
python3 metatron-kernel/arena.py < export.ndjson
```

The launcher freezes the qualified capability flags in `arena-flags.json`,
clears inherited checker flags, and passes the original input bytes to the
binary. It explicitly declines inputs larger than 10 MiB. The Arena controls
the per-test time allowance. The checker uses one worker and its existing
128 MiB worker stack. Exit codes are 0 for ACCEPT, 1 for REJECT, 2 for UNKNOWN
or a resource decline, and 3 for an error. Errors are not mapped to ACCEPT.

The renovated interface supports only a bounded fragment. The checker
reconstructs admitted single, nonrecursive inductive families and their
recursors from source types, checking the explicit feature flags, constructor
telescopes, universe constraints, recursor types, and computation rules. A
further bounded fragment checks projections and dependent field substitutions.
Contradictions of necessary feature conditions can warrant REJECT separately
from complete admission. Unsupported declarations or conversions yield UNKNOWN.
No runtime Lean or competing checker is consulted. There are no input-name,
hash, or expected-verdict lookups in the runtime path.

The previous source qualification is
https://github.com/heathsanchez/test/actions/runs/45580340184 at commit
0cd25006ebf2261cc692aecea8ae4abaa888b895, source tree
362242c265ee2b1758645c78ad141ad78bf6f8c2. The entry qualification keeps that
source tree unchanged and tests the current beta run 45676210453, revision
ac0765f269b3cb5d4ed3744301aa59f4ee67ad10, using hash-pinned published
artifacts and exact per-input SHA-256 checks. It also repeats all 212 legacy
verdicts through the frozen entry point.

The qualification is bounded testing, not a universal soundness proof.
Full Mathlib acceptance and an official Arena rank are not established.
