# Frozen extension: source-pattern witness → actual native application predicate (2026-10-15)

## New residual and stopping condition
The previously qualified identical generic Go AST/regexp generator produced one unique source-native changed pattern per source family, without author positive seeds. Its regex witness alone does NOT establish that any application behavior changed. This extension asks whether *the original executable application's own Go code*, not an isolated compiled regex, exposes the difference.

No changing the two original source PRs or their original generated witnesses. Their names, diff and historical author claims are now publicly known, so this extension is an **engineering/source-to-runtime transfer check, not a new blind scientific discovery**.

## Target-independent bridge construction (pre-code frozen)
Use only the generator's original pinned source pattern identifier and minimal frozen witness. Without per-repo function/test names, scan Go AST for a function or function-valued source declaration whose body references the changed regex variable and that accepts exactly one `string` and returns `bool` (or a one-field validation predicate that can be derived without hand authoring). Compile/run an entirely NEW test against each actual original module, once at historical base and again at contributor head; do not import original author regression tests as answers. A mismatch in the actual application predicate on the identical frozen witness qualifies bounded source-to-observed-runtime fidelity. A missing callable, dependency/toolchain error or same outcome must return UNKNOWN or REJECTED, not fall back to calling the regex evaluator.

Mandatory independently checked conditions: exact original Git revision, genuinely executed named test (zero test invocations must fail), old/head outcome differences on same input, newly created test not present in either repo's original source, no source implementation modifications; changed/wrong SHA refuses; no action authority. Count compile/setup/build failures and human time separately. Equal-information competent Go AST/control reviewer can implement the same bridge; no advantage claim.

Targeted ORIGINAL upstream PR scope remains go-ozzo/ozzo-validation #208 and asaskevich/govalidator #528 under the SHA pairs already committed in FROZEN_PROTOCOL.md. Do not retune upstream sample inputs from patch/tests. Preserve 2026-10-15 original fixed-source regex witness experiment and its run #38599440770 as a separate earlier authority.

Classification:
- PASS_BOUNDED: exact original application predicate evaluates changed meaning with generated witness.
- UNKNOWN_NO_CALLABLE/UNKNOWN_BUILD: source predicate bridge could not be independently executed.
- REJECTED: same public/app predicate outcome on the frozen distinguishing input.
- L7 independent method-generation remains UNKNOWN even if both app predicates differ.
