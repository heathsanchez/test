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

## Subsequent rejected mandatory ambient beta derivation

`checked-beta-derived-rejected` distinguishes completed strict payload typing from ambient evaluation-origin validity, including an unused ill-typed beta argument. Two new controls were RED before implementation. Library 173 pass / 0 fail / 10 ignored. Optional argument-retention copying is capped at256 total work units shared by strict probes; no work allowance increases. This restores app-lam and shift-cascade from the earlier beta regression, but ambient reconstruction introduces other failures. Full196 **115 ACCEPT / 71 REJECT / 10 UNKNOWN / 0 incorrect / 0 errors**; init-prelude, church-numerals, peano2 and peano3 regress from ACCEPT to UNKNOWN. All original six remain UNKNOWN. REJECT; not a production candidate. Further reconstruction fallbacks are not justified by this outcome.

## Independently downloaded CI evidence for165 snapshot

Actions https://github.com/heathsanchez/test/actions/runs/38960915917 at057b724f9ae0d1ed21c45e550d671f7a7418b070 verifies165 library passes, input pins and119/71/6/0 incorrect/0 errors. All196 individual input hashes and verdicts exactly match local replay. Strict promotion gate FAILS as required: complete Fueled remains UNKNOWN. Artifact12072926661 ZIP SHA256 dc5fcfd23a81b620016b7f436e983760db9a8b48e08f56f8fe8a5b6fc2daf01e; verified downloaded contents in typed-substitution/ci-38960915917. Previous run38960483514 failed library compilation due to omitted embedded fixtures and never qualified the corpus; fixed in057b724.

## Composed completed application and typed substitution

169 library tests pass / 0 fail / 10 ignored. The composition retains exact completed App premises, original scope guards and whole-TYPE typed substitution. Fresh review found no concrete wrong-ACCEPT hole and requested an explicit original outer/inner Pi revocation control for the memo consumer; that control now passes. Optional recording copies are capped at256 total work units, shared by strict probes. Full196 **119 ACCEPT / 71 REJECT / 6 UNKNOWN / 0 incorrect / 0 errors**, all individual verdicts preserved, all six original full exports still UNKNOWN at original declarations. This is unpromoted, not closure.

A passive typed-substitution audit on complete Fueled found zero declined whole-Pi substitutions: the existing whole-TYPE path does not decline a nested Pi in this replay. Therefore weakening that path is not justified by this witness; no context weakening was implemented.
