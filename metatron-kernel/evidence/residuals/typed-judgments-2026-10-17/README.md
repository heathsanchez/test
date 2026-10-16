# Typed judgments — unpromoted research, 17 October 2026

No complete residual closed. Production is unchanged.

* `typed-substitution`: 165 passing library tests, 10 ignored; all Cargo targets pass. Immutable full196: 119 ACCEPT / 71 REJECT / 6 UNKNOWN / 0 incorrect / 0 errors. Individual verdicts exactly preserved. All six complete positive residuals remain UNKNOWN. Binary SHA256 39f2a599ca21ec5e46c06fad6e0441cbe9bffe89d95403b4ec2c59759d460db6.
* `checked-beta-bindings`: 171 passing library tests, 10 ignored; all Cargo targets pass. Immutable full196: 116 ACCEPT / 71 REJECT / 9 UNKNOWN / 0 incorrect / 0 errors. Rejected: init-prelude, app-lam and shift-cascade regress from ACCEPT to UNKNOWN. All six targeted exports remain UNKNOWN, with earlier obligations. Binary SHA256 11d38950fb65a76d584b553d4102c4f39748db33d472991cfdc4dfe8d94b0ce2.

## Acquired capability, not export completion

The first source snapshot transports a checked application's dependent whole TYPE with a single explicit environment mapping. Inner Pi binders receive actual fresh introductions in the target context, preserving original owners as dependencies and universe substitutions. Derived judgments are invalidated transitively when any observed original source witness changes, including revoke-and-restore within one mutation guard. The actual physical caller and complete context must match. Unsupported cases retain the legacy partial path; no extra fuel or conversion proof is invented.

The second snapshot attempts to preserve completed argument judgments across actual evaluator beta/let binding nodes. Origin metadata is intrinsic in each environment node, including fresh probes and cache overflow. It is rejected: mandatory reconstruction at every referenced evaluated binding loses accepted cases. Fresh review also found that checking only referenced BVars misses an entirely unused ill-typed outer beta argument. These local controls and raw evaluator metadata do not prove a sound completed source substitution rule. Do not promote this snapshot or interpret 171 local passes as sufficient.

## Next decisive work

Trace the first new regression and distinguish typing the already-substituted term from certifying the original source substitution. Source typing evidence must be attached to the exact checked derivation that authorizes transport; neither global rejection of every evaluator binding nor forgetting erased obligations is an adequate rule. Require an actual complete positive export ACCEPT before promotion, with all original per-case verdicts and adversarial controls preserved.

No full Mathlib replay or performance qualification occurred for either snapshot. No new GitHub CI run is claimed here. Previous CI runs do not qualify these sources.
