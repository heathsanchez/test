# Corrected recursor-major authority

Candidate: `58b77d34d441b90dc6a103abd98a8d879c23c445`.
Arena: `b1d6e91d6de351f9bcf21e6b039f4d51d6b9bb42`, exact 196-case corpus.
Result: **115 ACCEPT / 71 REJECT / 10 UNKNOWN / 0 wrong / 0 errors**.

This supersedes the earlier eight-UNKNOWN checkpoint for current authority.
The previous shortcut inferred an eliminator's input constructor from its
own possible output constructors. That is not valid iota-reduction evidence.
The regression `recursor_output_constructor_does_not_identify_its_symbolic_major`
fails on the previous code and passes after removal. Its before-fix failure
and the complete passing release suite are retained here.

Recursor dispatch now requires the actual major to expose a certified
constructor. Speculative full major exposure is capped at sixteen steps;
an unresolved major leaves the recursor stuck and ultimately produces UNKNOWN.
The cap controls work and grants no reduction authority.

Removing the shortcut without bounding speculative exposure produced two
ten-second timeouts. With the bound, all 196 cases finish without process errors.
`perf/folded-constant-first` and `perf/folded-constant-last` change from ACCEPT
to UNKNOWN. No other corpus verdict changes relative to the eight-UNKNOWN run.
The args-before-unfold and RBTree improvements are retained.

Remaining: init-prelude; perf/folded-constant-first; perf/folded-constant-last;
perf/fueled-chain; perf/grind-ring-5; perf/magma-list-deep-n21;
perf/magma-list-deep-n36; perf/magma-list-pair-n21; perf/magma-list-pair-n7;
perf/shared-subterm.

This records tested behavior and a corrected reduction rule, not a general
soundness proof or an official Arena ranking.
