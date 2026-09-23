# G4-001 Shared-Binder Conversion Plan

**Goal:** Accept the exact dependent-identity residual by relating open types
under explicit shared witnesses, without substitution copying or accidental
equality of unrelated de Bruijn indices.

**Architecture:** Introduce semantic local identities distinct from raw source
indices. Closure environments may bind either a suspended source closure or a
fresh semantic local. Type inference allocates deterministic locals at binder
depth. Conversion carries that depth in its worklist and opens each exposed Pi
or lambda body with the same local on both sides. The existing authority,
budget, guarded delta, and UNKNOWN behavior remain unchanged.

## Experiment

1. Add the byte-exact G4-001 end-to-end failing test.
2. Add a conversion-policy ablation: raw open bodies must reject; shared
   witnesses must accept.
3. Add environment/machine tests proving equal witnesses compare and distinct
   witnesses do not alias.
4. Implement only semantic locals, binder-depth propagation, and body opening.
5. Qualify tutorial cases 001–008 and the complete protected suite.
6. Record retired instructions only if candidate and flash share the identical
   measurement identity; otherwise preserve UNKNOWN.
