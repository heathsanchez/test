# V4 minimum sufficient native authority — pre-implementation contract

Frozen against `heathsanchez/test@95029db0d0b2122836bee7268299461bfbdb5a66`.
Independent test obligations: `test_native_environment_selection_v4.py`,
authored first at commit `8c7ec8815823f3cdfcb0d64fc953042e49a3e9ec`.

## Scoped hypothesis

A parse error in a Python-named source blob unrelated to executable metadata must
not, *by itself*, prohibit environment *candidacy*. The complete source remains
content-addressed, and an attempted native import, collection, or protected
execution of syntactically invalid Python must still fail.

- Never rewrite the original v3 selector or qualified environment verifier.
- All source bytes remain in canonical source identity. A deferred parse is
  evidence-bound, not a pass for an executable module.
- Setup metadata (`setup.py`) is never silently deferred.
- Native importer, test collector, required assertion, plugin and verifier
  authority are unchanged. V4 candidacy is not native admission.
- Preserve all V3 compatibility/metadata adversarial contracts.
- Verify actual pytest success for unread fixture bytes and failure on imported
  or collected syntactically invalid Python.
- Dynamic setup metadata, nonliteral requirements, unsupported metadata grammar,
  absent compatible runtime, and native integrity failures remain UNKNOWN.
- All seven V3 screening tasks have already been exposed. They may only be used
  as development diagnostics and cannot become prospective successes.
- No claim of G2–G6, comparative advantage, a solved prospective trial, or
  nonbypassable sandbox is warranted from V4 unit qualification.

## Acceptance

1. Separate V4 source published while original V3 source remains byte identical.
2. Unmodified V3 regression suite and inherited V4 regression suite both pass.
3. New actual native collection/import contracts pass with precise negative gates.
4. Preserve source SHA, exact commit, Actions job and artifact.
5. Do not commence new fresh frontier unless independent selection/admission
   qualification establishes a usable and source-preserving interface.

Scientific verdict remains `G2=UNKNOWN, G3=UNKNOWN, G4=UNKNOWN` until
separate untouched-source native study actually runs and succeeds.
