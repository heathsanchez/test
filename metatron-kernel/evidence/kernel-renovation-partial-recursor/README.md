# Draft Lean #15374 partial-recursor compatibility probe

The exact historical Nucleus authority `e7c4855177eb2086c14e90b851be99062ee8c959`
returns **0 ACCEPT / 0 REJECT / 2 UNKNOWN / 0 process errors**.
The declared compatibility gate requires **2/2 ACCEPT** and therefore fails.
No kernel source or semantic authority is changed by this probe branch.

## Source and verification boundary

Lean PR #15374 is draft, unmerged, at
`63da8abdd58db2d6d4f6a648a6e24df2949d6a11` at the recorded check time.
The two equalities in `PartialRecursor.lean` are taken from
`tests/elab/12520_2.lean` at that head: the Eq.rec-vs-function and
Prod.rec-vs-function examples. Only theorem names and explicit parameter
binders are added. Both declarations compile successfully on that exact PR
release; its embedded githash and the downloaded archive digest are checked.

Unmodified lean4export source at
`66f1fb4bc256072069767fce52d39480e4524869` was built with the exact PR
toolchain. Each theorem was separately exported from the same module.
The output metadata reports NDJSON **3.1.0** and the exact PR Lean githash.
`result.json` retains input hashes, checker binary hash, process outcomes,
timings, toolchain archive digest, and the official Lean compilation outcome.

## Causal controls

For each export, its dependency-only prefix ACCEPTS. A diagnostic NDJSON
mutation replacing the equality's right-hand side by its left-hand side also
ACCEPTS using the original reflexivity proof. These four controls localize the
failure to the target equality, rather than its dependencies or export format.
The mutated exports are diagnostics, not additional upstream test examples.

The exact e7c conversion code lacks a partial-recursor/function eta path.
The observed mismatch is verified at this two-case boundary. The proposed new
upstream semantics remain **CANDIDATE** because the PR is still draft and its
author explicitly questions the completeness of the criterion and tests.
The minimal implementation target, after upstream stabilization, is
conversion-side partial-recursor eta expansion with certified eligibility.
Normal WHNF and ordinary recursor reduction are outside this experiment.

ROS already records e7c as superseded by later independent Nucleus lines.
This is an explicitly requested historical-authority compatibility test, not
a claim about the latest Nucleus implementation or a new Arena count.

## Reproduce

Build Nucleus at e7c with `cargo build --release --locked` in metatron-kernel.
Then run:

```sh
python metatron-kernel/evidence/kernel-renovation-partial-recursor/replay.py \
  metatron-kernel/target/release/metatron-kernel
```

The baseline replay exits 1 because the required compatibility gate fails.
Export regeneration uses the exact PR `lean` and `lake` binaries in PATH:

```sh
lake build PartialRecursor
lake env /path/to/pinned/lean4export PartialRecursor -- nucleusPartialEq > eq.ndjson
lake env /path/to/pinned/lean4export PartialRecursor -- nucleusPartialProd > prod.ndjson
```

Create a minimal Lake package with one library named `PartialRecursor` and the
included source. The exporter source remains unchanged; the invoked toolchain
is deliberately the pinned PR release rather than its default toolchain file.

In this container, numeric `/proc/<own-pid>/exe` lookup is denied while
`/proc/self/exe` is permitted. `self-proc-path.c` redirects only that own-process
path. It can be compiled with `cc -shared -fPIC -Wall -Wextra -Werror` and
`-ldl`, then supplied through LD_PRELOAD for Lean/Lake/exporter execution.
This changes executable-path lookup only; the Lean binaries are unmodified.
No shim was loaded into Nucleus.
