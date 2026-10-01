# Telescope admission iteration ledger

Base: e038dc5104cf7fee2737d46683c11725b124c314 (semantic113e3155).
Approved objective: iterate checked obligation representation through executable
closure, propagate to dependents, preserve all established correct decisions.

Iteration1: safe nonrecursive Type records with bounded parameter and field
telescopes. Infer each field universe in its actual prior context; prove its
universe is bounded by the result via max equality. Validate constructor,
recursor, annotations and reductions; install projections only after checking.
First targets: GetElem? x2 and Functor x1. Shape is never authority.

Ruling: use an isolated GitHub branch and local mirror; local Cargo unavailable.
Hosted CI supplies RED/GREEN and all387 replay. No official Arena submission.
Ruling: reject unsupported dependent/recursive/indexed premises by UNKNOWN;
do not relax an assertion to make the targeted prefix appear closed.

Task1 in progress: real-prefix tests written; hosted RED pending.
