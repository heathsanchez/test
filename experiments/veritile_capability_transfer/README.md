# VeriTile capability-transfer probe v1

## Question

Can one verified optimization law be compiled into a smaller reusable capability
and then discharge a semantically richer, held-out kernel consequence without
adding authority to VeriTile?

## Frozen external source

- Repository: `Lizn-zn/VeriTile`
- Revision: `95a01f598e2cd1cac4052e5e5ff9145c658e18db`
- Seed: `VeriTile/Triton/Math/Softmax.lean::TiledSoftmax.naive_eq_stable`
- Held out from capability construction:
  `bench/tritonbench_g/softmax_reducev/SoftmaxReducev.lean`

The seed says ordinary softmax is invariant under a common exponential shift.
The compiled candidate law strengthens only that algebraic observation:

> any normalized exponentially weighted finite quotient is invariant under a
> common shift.

The held-out `softmax_reducev` closed form is a richer consumer because its
numerator is a weighted vector reduction, not a single softmax lane.

## Qualification boundary

The hosted workflow:

1. checks out the exact VeriTile SHA;
2. builds the VeriTile lite library under its pinned Lean toolchain;
3. independently elaborates the seed softmax showcase;
4. runs an ablation in which the exact transfer theorem is appended to the
   held-out file **without** the compiled capability and requires elaboration to
   fail;
5. injects only `MathGraphShiftCapability.lean`, appends the same transfer
   theorem, and requires the held-out file to elaborate;
6. writes a JSON evidence artifact with source hashes and proof-size accounting.

No upstream file is changed. The vendored checkout is ephemeral inside CI.

## Epistemic state

Before the hosted gate: **CANDIDATE**.

A green gate warrants only the bounded semantic-transfer claim. GPU speed,
IEEE-754/PTX/codegen correctness, and an actual training-throughput consequence
remain **UNKNOWN**. Those are deliberately not inferred from Lean-level
transfer.
