# Nucleus × Dogwood warrant gate V1

This experiment projects one existing Nucleus research-governance rule into the
independently developed Dogwood temporal policy engine.

## Protected rule

A candidate may reach `Promote` only after the same exact candidate SHA has:

1. built successfully;
2. qualified successfully;
3. completed a full protected replay with `wrong = regressions = errors = 0`;
4. recorded a successful evidence artifact; and
5. not been successfully revoked after that artifact.

The stage actions are themselves gated, so the dependency order is executable,
not merely documentary.

## Real lineages replayed

- Negative control: `nucleus-rule-aware-major-v1@a1b62bd3...`, GitHub Actions
  run `35960340790`, retained as a resource-negative failure.
- Positive control: `nucleus-crystal-independent-33-v1@a12353b...`, run
  `36627307769`, artifact `11061162830`, 102 ACCEPT / 58 REJECT /
  33 residual / 0 wrong on the frozen 193-case independent boundary.

The workflow verifies the live GitHub run SHAs/conclusions and artifact identity
before replaying the projected trace.

## Claim boundary

A green result warrants only this bounded interoperability claim:

> the declared Nucleus dependency-closed promotion rule can be represented and
> enforced by Dogwood on these source-pinned traces.

It does **not** prove that Dogwood authenticates GitHub events, that every ROS
warrant rule has been encoded, that the event projection is complete, or that
Dogwood and Metatron/CLC have identical semantics. Event provenance is an
explicit trusted input to this experiment.

The final revocation step is a deliberate separator: the same previously
warranted candidate must be denied promotion after a later successful Revoke.
