# Nucleus Dogwood reusable admission gate V4

V4 packages the V2/V3 evidence-to-event path as a reusable local GitHub
composite action:

`.github/actions/nucleus-dogwood-admission`.

Callers provide only:

- a Nucleus qualification `result.json`;
- the exact target residual/test;
- the exact corpus identifier;
- the exact evidence lineage identifier.

The action:

1. compiles the result into lifecycle events;
2. renders an exact source-pinned Dogwood policy from the same result;
3. validates and replays under pinned Dogwood;
4. fails unless the final admission verdict is `ALLOW`.

The qualification workflow tests the action on the sealed V3 result and then on
the same result with one synthetic wrong decision. Clean evidence must pass;
tampered evidence must fail closed.

This packages governance plumbing only. It adds no Lean-kernel semantic
authority and does not mutate the canonical Nucleus branch.
