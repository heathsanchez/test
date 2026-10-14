# FROZEN ADVERSARIAL GATE — dynamic subclass constructor compatibility

**CANDIDATE / NOT EXECUTED at freeze.** The previously generated base→patch→revert 2/2 native green [run #38627828541](https://github.com/heathsanchez/test/actions/runs/38627828541) is WARRANTED only for its declared bounded observer corpus and original targeted suites. It did not establish arbitrary user subclasses or all input iterator timing. The complete source evidence archive #11924821444 ZIP SHA256 8976d6ce9daa39e764fb467d580cf50960e2395ffec67b3069b1412b0e016362 was independently downloaded and examined; original source SHA and patch SHA retained. This protocol precedes writing/running a subclass adversarial harness or alternative repair generator.

## Hypothesis and exact falsifier

Python mutable-set classes are subclassable unless specifically forbidden. If a class's original method is inherited by a valid subclass with an additional **required constructor argument**, a repair inserting `type(self)(iterable)` might introduce a TypeError even for an input that previously worked. If true, the general preflight constructor violates protected method viability even though finite original witness/program corpus and original native suite remain green.

- Read original exact immutable upstream source in an independent ephemeral runner. Derive changed set class/method from PREVIOUS unchanged AST scanner, not a manually named class, method, file or package.
- Construct a one-off subclass of that exact original class whose `__init__` requires one additional positional token and calls the parent base initializer correctly. The extra token is a legitimate hypothetical downstream client requirement; this is an adversarial *generated* client, not a claim it occurs in the original repo.
- Instantiate subclass with two unique elements and required token, then call the inherited changed mutator with two unique elements. This control must PASS on unchanged original base and contributor head.
- Apply the previously generated exact type-directed canonicalization patch to original base **in ephemeral checkout**, preserving patch bytes/hash, and repeat same subclass client. If the patch newly raises TypeError, mark `REJECTED_SUBCLASS_UNSAFE`; do not call it production-safe or L7. Physically remove patch and rerun green original client.
- Do not use the original author-head code to construct the repair; it is an independent behavioral reference/control.
- If and only if adversarial regression is observed, test a **separately explicit, human-designed alternate candidate**: replace dynamic subtype constructor `type(self)` with the source AST's lexically defining public class constructor in the SAME predeclared normalization before mutation; no hardcoded class names. Require both old-bug repair and descendant-subclass control plus original suite and ablation. Do not retroactively promote the original candidate. The alternate may still be unsafe for other subclasses/contracts; keep broader safety UNKNOWN.
- Count action/runtime costs and all failures. Strong agent baseline, L7, external maintainer adoption and full safe-to-merge remain UNKNOWN.

This is a principled negative applicability test, NOT discovery of an original upstream bug. No unsolicited external writes, comments, new App installations or production changes; no Gmail/Render/outreach.
