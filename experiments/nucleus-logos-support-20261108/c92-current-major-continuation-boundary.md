# C92: current-source recursor continuation boundary (13 November 2026)

**Status:** WARRANTED_BOUNDED for the source-hash-pinned current C91 CLI and
diagnostic observations below. **REJECTED** as closure candidates: three existing
evaluator toggles and one tested combination for the two selected Magma
originals. The six original valid UNKNOWNs and full Mathlib remain **UNKNOWN**.
No source code, inference rule, recursor certificate, budget or input was changed.

## Exact authority and non-comparable baselines

- Checker: clean C91 parent commit `a7eb9020a9099b7acb0703b49adbbd86ab3efdd3`,
  GitHub-published equivalent tree `d939d30d631dc05f8d74ad1440ae68d1b27a9916`;
  source `checker.rs` SHA-256
  `8b009ff49a02c65a245dae86141b728bcd9fb3dc6db487d7ddb05ff4733f1306`,
  `convert.rs` `c3d47f4be05dbdcc1ba99eb668fe4cd32873f4e7d8b1b95480f6c1e943bd7f88`,
  `machine.rs` `6a61a2a42833364aa1222b4b07c414a9c8ae6d278da9958c7875ee61eb23ee05`.
- Current upstream Arena: `6c2d82164f1a2b1ac94aee62290fe78a3c3853fb`;
  native exporter 3.1.0 / Lean 4.34.1, original re-export byte SHA-256:
  `magma-list-pair-n7` `abce636f6a7dd529c0dc6bbad8e7c8e2eaecfdda0d04c191d7f868e3a4468d35`,
  `magma-list-pair-n21` `b8279fa9189a203c6c11b04702c27c0f99a650b37f2b0165dd260b1d14e9ef84`.
- The C91 `Limits::default()` **has 65,536 judgment steps**. Its selected
  comparison flags here were `NUCLEUS_EXPERIMENTAL_RELEVANCE=1` and
  `NUCLEUS_EXPERIMENTAL_EXPECTED_LAMBDA=1`. The older C89/C90b campaign used
  **262,144** and 24 selected flags. These are **different qualification
  boundaries**: no equivalence of outcomes, costs or root causes is inferred.
- Diagnostic-only local `cargo build --release --locked --features diagnostics`
  succeeded. Built diagnostic binary SHA-256
  `a6966393f26bfd528a9068e9c9b2bc08245d5a4cf03eb7e951005cec55c8284f`.
  Rust diagnostic counters on n7: 276 declaration checks, 89 inductive
  signatures, 247 type judgments, 45,551 conversions. Counters are not Arena
  retired instructions or a comparison with the historical C89 artifact.

## Negative actual-source A/B

Invoke the same release CLI with the two selected flags above, exact source on
stdin and **only** the extra flag(s) indicated. Exit 2 means UNKNOWN:

| C91 evaluator setting | Pair n7 | Pair n21 |
| --- | --- | --- |
| None (baseline) | 2 | 2 |
| `NUCLEUS_EXPERIMENTAL_DEMAND_MAJOR=1` | 2 | 2 |
| `NUCLEUS_EXPERIMENTAL_REPLAY_PROJECTION_MAJOR=1` | 2 | 2 |
| `NUCLEUS_EXPERIMENTAL_REPLAY_NEUTRAL_PROJECTION=1` | 2 | 2 |
| Both projection flags | 2 | 2 |

These ten native replays rule out the *tested existing toggle settings* as a
current-C91 closure by themselves. They do not test every possible composition,
the older 24-flag baseline, or any soundness claim for a hypothetical ACCEPT.
The full 403 protected corpus was **not** rerun for these unchanged-UNKNOWN arms.

## Causal lead: actual, but only diagnostic, constructor endpoint

With `METATRON_KERNEL_DIAGNOSTICS=1` and
`NUCLEUS_TRACE_APPLICATION_FUNCTION_TYPE=1`, n7's outer source application
`ExprId(8835) = (ExprId(8805) ExprId(8834))` reached
`application-function-type` because the inferred function type is UNKNOWN,
with inner residual `unresolved-qualified-recursor-heads` and 65,069
remaining local steps. The function is source `App(8753,8804)`; the argument is
a source lambda. This is a downstream *observation*, not proof of first causal
failure; earlier inner applications also returned UNKNOWN in the trace.

With `NUCLEUS_TRACE_DECIDABLE_MAJOR_CHAIN=1`, two source-captured major-chain
samples were printed for each original. First samples:

| Case | First chain length | Major source | Terminal sampled constructor |
| --- | ---: | --- | --- |
| n7 | 11 | `ExprId(11) = BVar(2)` through distinct captured frames | `NameId(146) = Decidable.isTrue` (steps 8–10) |
| n21 | 25 | `ExprId(11) = BVar(2)` through distinct captured frames | `NameId(146) = Decidable.isTrue` (steps 22–24) |

The registered recursor is `NameId(147) = Decidable.rec` with five arguments;
its independently registered constructor rules are `NameId(145) = isFalse`
and `NameId(146) = isTrue`, one field each. The diagnostic emits different
captured frame IDs and actual universe substitutions, not proof that the
corresponding recursor *outputs* are equal. Most importantly, the observer
calls `machine.expose` with a separate `min(budget,256)` allowance per trace
step. **This is observational exploration outside the original charged owner,
not a certified proof or resource-saving implementation.** We must not turn
the sampled `isTrue` endpoint or an expected Bool result into a chosen recursor
minor without applying every real source RHS in the original context.

## Next smallest consequential experiment

On the same hash-pinned originals, preserve a *single caller-owned charge* and
record each actual five-argument `Decidable.rec` continuation's exact
`(source ExprId, captured EnvFrame, universes, full arguments, phase)` and
enter/resume/completion result, together with the **actual** owner delta.
Check whether a source-checked completed RHS ever becomes available but is
recomputed before its enclosing major resumes. If it does, test one
source-exact, owner-charged continuation retention change with a red/green
test on the original n7 source; otherwise reject that optimization and pursue
an independent structural recursor evaluator. Never cache an UNKNOWN or
unfinished projection as a proved constructor. Require both originals under
the **same 262,144 / 24-flag** C89 boundary for comparison and the unchanged
forged-proof plus 403-case regression before promoting a semantic change.

Cross-project convergence (CANDIDATE): the first *meaning-loss* risk here is
collapsing different captured environments or suspended phases into one proof
value. The correct factorization question is whether two computation states
are equivalent for **every downstream source rule**, not whether they share a
syntax node or eventually display the same constructor in a diagnostic.
