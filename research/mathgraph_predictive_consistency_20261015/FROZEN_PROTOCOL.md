# Frozen protocol — source-derived predictive consistency observer, 15 Oct 2026

**State: CANDIDATE, NOT EXECUTED.** Authored before opening original Python implementations, contributor code patches, or regression test files in the two targets. Titles and PR bodies WERE READ during selection: both explicitly describe their defects. This is **retrospective, topic-informed mechanism qualification**, not novel bug discovery or a blinded customer trial.

## Source identities and held-out transfer
- DEVELOPMENT: `grantjenks/python-sortedcontainers` PR #254; original predecessor `3ac358631f58c1347f1d6d2d92784117db0f38ed`; contributor head `43e683b8040440200997daf441d3975f709c3b44`. Public topic: SortedDict update leaves inconsistent state when iterable raises.
- TRANSFER: `rspeer/ordered-set` PR #107; original predecessor `9dfc91c27c0c56df2536036bec4a5b3f717ef2ba`; contributor head `697a395537ff1e41b8fea65dc54f85664d5eac82`. Public topic: symmetric_difference_update duplicates internal items.
- Third-party PRs remain read-only; the second source is developed without per-target adaptation after the first's run. Subject selection is title-informed, so holdout is **implementation/operation generalization**, not a concealed semantic goal.

## General source-derived constructor
1. Read original source classes/method ASTs at exact commit identities. Select the changed original callable method mechanically from old/new diff HUNK LINE SPANS, not a manually named method, class, source path, witness literal, or test.
2. Determine *standard normative contracts* only from actual public Python ABC inheritance/structural interface and source docstrings: Mapping/MutableMapping: number of unique keys reported by iteration must equal len(instance); Set/MutableSet: number of distinct emitted elements must equal len(instance). Normative contract is independent of the contributor's patched behavior, and does not require the system to guess a product goal.
3. Automatically derive a finite typed observer/program grammar from available source public operations:
   - construct collection from zero or small input;
   - execute discovered changed method with a generated standard argument shape, including lists, tuples, duplicate iterables, malformed pairs, and one-shot iterators whose iteration raises;
   - after any success **OR expected exception**, independently read len(instance), list(iter(instance)), and len(set(iter(instance))) when supported.
   - candidate typed prediction relations: equality of independent readouts (len vs enumeration size; for Set, len vs distinct members); refuse unsupported/effectful projections.
4. Select the *smallest* generated observation relation that distinguishes old source from independently sourced contributor head while agreeing with controls and standard Python protocols. Do not present a mere behavioral delta as a normative violation; false/undefined contracts => UNKNOWN.
5. Apply the SAME interpreter/constructor source without edits or hard-coded target names to transfer repo. Physical missing test/observer abstention, incorrect source SHA, unavailable original source, and malformed/unsupported contracts must not issue a PASS. A deliberately incorrect len equality prediction on a normal Python object must be rejected. Restore/replay and cold run if practical.

## Promotion and controls
- One positive on development source alone => CANDIDATE. Both independent native sources positive plus source SHA, contract evidence, typed program, genuine negative controls => WARRANTED_BOUNDED_PROGRAMMED_OBSERVER_COMPOSITION, NOT unrestricted method grammar invention.
- A counterexample (e.g. no admissible native sequence, wrong contract, failed transfer) remains REJECTED/UNKNOWN, not repaired by injecting target-specific test code.
- No outside code writes, comments, PRs, merges, customer installations or deployments. No Gmail, Render or outreach.
- Baselines: report a no-composition/call-only comparator and a fully information-equivalent source-aware consistency check. No strict reviewer superiority claim without a true strong equal-information live coding-agent comparator and lifecycle costs. Read-only historical contributor fixes are not MathGraph-authored patches.
- Scientific L7 remains UNKNOWN: the native compiler itself and its typed candidate operators are written by a human, even if it constructs a previously absent executable composition at runtime. No source self-rewriting or recursive improvement claim.
