# Phase B — observational state acquisition (frozen before implementation)

Same exact pinned external chi base/head as FROZEN_PROTOCOL.md. Prior native run 38559762641 passed.

Acquire the minimal finite behavioural quotient WITHOUT supplying the internal "seen names" representation to the learner.

Frozen input interface:
- finite alphabet of three route wildcard names: a, b, c;
- histories of up to 4 names;
- observation: whether a parsed route pattern is accepted (no panic);
- distinguishing continuations of up to 3 names, with length-4 suffixes reserved for holdout.

The generic algorithm must build residual acceptance signatures from ONLY native oracle results, partition histories by signatures, and check that equivalent histories remain equivalent on the untouched suffix-length-4 holdout. It must produce a shortest distinguishing suffix for any distinct learned states. It must not assume or inspect a variable named "seen", "anchors", "tag handles", or a specific parser function's internals.

Apply precisely the SAME observational learning algorithm on two independently implemented sources, with only a thin public API oracle adapter:
1. chi's native patParamKeys (external original chi source, revision pinned).
2. Go standard library net/http.ServeMux (independent implementation).

Accept only when both infer 9 states and all frozen heldout checks pass; failure is a native semantic difference, not a harness success.

Negative control: an artificial order-sensitive oracle must distinguish histories (a,b) and (b,a), demonstrating that the algorithm detects when erasing ordering is UNSOUND.

The alphabet and what counts as an observation are HUMAN-CHOSEN. This is not general automatic extraction of the right semantics from arbitrary code, not proof of all string input behaviour, nor evidence of better decisions than a knowledgeable maintainer. Do not use contributor test code or contact upstream.
