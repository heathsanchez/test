# Bounded V54 formal instance

The formal model uses the original MathGraph VDN definitions at
`metalogiclabs/mathgraph@cf359686c74549a132c7a651cd7aabc7c1a870fe` unchanged.
The exact original toolchain is `leanprover/lean4:v4.28.0`, recovered from its
`verified-developmental-navigation/lean/lean-toolchain` Git blob
`4c685fa085fa1c66103533e992fc82c014a12142`.

The concrete [GeneratedV54.lean](v54_formal/GeneratedV54.lean) instance is now
checked against those original sources on that compiler. The
[compiler receipt](v54_formal/lean-verification.json) reports
`CHECKED_BOUNDED_TABLE_CERTIFICATE`; the
[evidence manifest](v54_formal/evidence-manifest.json) binds the actual retained
native source snapshots and observations. All five compiled modules returned
zero. The concrete module took 22.086 seconds to check.

The exact old table contains 541 actions and 542 covered traces including the
empty trace. Every candidate hash matches the independently reconstructed
original cold enumeration in order. The observed outcomes are 497 nonzero
native failures and 44 explicit timeouts, with no recorded pass. The actual
acquired O1 and O2 operator identities also match the two source transitions.

| Actual retained state | Full source SHA256 | Direct native observation |
| --- | --- | --- |
| Double-broken start | `9da7fc1e2edb4a6bfa62e39c6dc0cf7fa97b21119abd83ed8229a28ad23f275f` | Timeout, call 705 |
| O1-only warm state | `8b2f4364c881cef2c98518c52852838ae7b7d63e14cd9be478a76e0c933987d2` | Timeout, call 706 |
| Final O1 then O2 state | `b879cb3f671cf1c28e8ff9b2b02151bcdb8974b4820a514cfdd1f5a038443cd2` | Pass, exit 0, call 1248 |

The concrete checked theorems are
`ActualV54.certifiedPhaseChange`, `ActualV54.everyOldCapabilityRetained`,
`ActualV54.oldBoundaryHasNoRecordedPass`, and
`ActualV54.finalHasRecordedPass`. The first three report the standard Lean
axioms `propext` and `Quot.sound`; the final observation theorem reports no
axiom dependencies. There are no additional proof axioms or `sorry` terms.

The generated source SHA256 is
`7996b2ec5c60484101eb1b5ebf0d6b497853021dc7571977320c6c8d373136ea`.
The compiler receipt SHA256 is
`b445ed50f176f79ff6be187a7bd1cd263fd39d9a4c287da19fa629aab2c22600`.

## Concrete state and action boundary

The state type is `String`, interpreted as the SHA256 of the complete actual
Requests `src/requests/utils.py` file. Other native-world source files and test
dependencies are fixed by the native qualification's pinned snapshot; this
interpretation does not identify arbitrary Python execution with a Lean
function.

The old action type is `Fin n`, where `n` is the number of original V54 cold
one-token-rewrite candidates. Each action has precisely its retained
source-hash transition from the double-broken source. It is undefined at other
states. These are snapshot-specific candidate actions, rather than a claim
about arbitrary applications of a rewrite schema to every Python program.

The old trace boundary is `trace.length ≤ 1`. Its complete cover is the empty
trace followed by every singleton action: exactly `n + 1` traces. The upstream
`World.CompleteCover` obligation is proved for this boundary. This boundary is
the original experiment's fixed one-new-rewrite discovery horizon; it is not
an exhaustive theorem about every old generator composition or an unbounded
Python search.

The new action type retains every old action with identical semantics at every
state, and adds two exact edges: actual double-broken source to actual O1-only
source, then O1-only source to actual accepted final source. The two edges must
independently reconstruct as actual single-token source changes. The concrete
instance packages the upstream `CapabilityPhaseChangeCertificate`, yielding
bounded old nonreachability of that final hash, new reachability, and retention
of every old-world reachability fact.

The protected observation is the frozen native outcome table. Outcomes retain
`passed`, `failed`, `timedOut`, `error`, and `unknown` as distinct Lean values.
The generator refuses `error`, absent, or unknown observations. Shell exit 124
from the original `timeout 7s` command remains `timedOut` even when the outer
native-call wrapper calls a nonzero exit `native_failure`. A separate theorem
shows that every surviving old outcome inside the declared boundary has no
recorded pass, while the final source has a recorded pass.

## Evidence admission and replay

[generate.py](v54_formal/generate.py) authenticates the exact original V54
source SHA256
`13c05aea8d6c1ce2db6d3d4b85c566ee3dbd2f3fcc1c3c8c14c1c2dece7f05ba`
at commit `2dd5f41b6c7cec1004b8deaee4f976dd2a9ed21c`. It reconstructs the cold
enumeration from the retained double-broken source using the original
`DESTS`, token types, destination exclusions, token coordinates and source
replacement procedure. Every candidate hash must match an actual cold native
call in exact enumeration order. It rejects missing or additional calls,
inconsistent outcomes for the same source, a cold pass, missing endpoint
observations, and an unaccepted final source. The original Requests command
and its seven-second shell timeout must match the recorded calls.
Source provenance must match the exact original and Requests pins, every
Requests call must name that world's recorded directory, and the endpoints
must have direct native observations. When `--input RESULT.json` is supplied,
the inferred source edges must also match the actually acquired O1/O2
executable operators; that identity check is recorded in the manifest.

The evidence manifest binds original source, native calls, actual source
snapshots, optional complete acquisition artifact, emitted transition table,
and emitted Lean source by SHA256. The admitted native-call prefix and source
snapshots are frozen under `v54_formal/evidence/`, allowing later restoration
calls to append to the live qualification log without changing this proof's
evidence. Artifact references are relative to the manifest for replay from a
different checkout. The transition table retains candidate
index, token coordinates, raw native status, return code, timeout and call ID.
The enumeration procedure is regression-checked against the exact original
`one_rewrite_discovery` function on a temporary test input; that test supplies
no native V54 outcome evidence.

The frozen acquisition checkpoint includes the successful main O1/O2 native
execution and independent receipt. Later baseline, withdrawal, restoration and
cold-restart qualification outcomes are reported separately by the native
qualification journal; this finite certificate does not certify those stages.

Given an adapter output directory `NATIVE`, replay is:

```sh
python research/unified_consequence_runtime/v54_formal/generate.py \
  --native-calls NATIVE/native-calls.jsonl \
  --broken NATIVE/state-double-broken.json \
  --warm NATIVE/state-warm-after-O1.json \
  --final NATIVE/state-final.json \
  --input NATIVE/../RESULT.json
python research/unified_consequence_runtime/v54_formal/check.py \
  --lean /workspace/v54-lean/lean-4.28.0-linux/bin/lean
```

The compiler checker authenticates all three original VDN source files,
requires exact Lean v4.28.0, rechecks evidence hashes, compiles the original
World, DevelopmentCertificate and Routing modules, then the glue and concrete
generated module. It records commands, return codes, source hashes and
`#print axioms` output in `.build/verification.json` and `.build/lean.log`.
A reviewable copy is retained beside the concrete source as
`v54_formal/lean-verification.json`.
`sorry`, `admit`, new axioms, unsafe proof escapes and `sorryAx` are rejected.
The checker regenerates the table and concrete source from the frozen inputs
and requires byte equality, then requires all four concrete theorem axiom
reports with dependencies contained in `propext` and `Quot.sound`.

## What this does and does not establish

The checked theorem establishes the finite transition-table claim and its
declared horizon. The native evidence separately establishes the recorded test
outcomes at that horizon. In particular, a timeout proves only absence of an
observed pass within the configured resource boundary. It does not prove that
the candidate would never terminate or pass with another resource allowance.

The evidence-to-model correspondence still depends on the original Python
tokenizer and mutation semantics, SHA256 identification of actual source,
native source/dependency isolation and test invocation integrity, and the
correctness of the evidence-admission script. These bindings are inspectable
and replayable; they are not proved as a Python-to-Lean refinement theorem.
The model also does not establish unrestricted generator invention, general
developmental completeness, MSI's universal future-observation equivalence,
or a system-wide L7 qualification. Those claims remain **UNKNOWN**.
