# Post-failure amendment A1 — receiver reachability, 2026-10-30

**This amendment is NOT part of the frozen blind protocol** and may not be used to certify a strict blind G3 result.

The first source-native CI #40983573858 (commit 0fa11a24b3fead5ba1bc7ba81b138f8f639136c5) showed:
- Three generic AST unit tests passed.
- Source scan of `patrickmn/go-cache@46f407853014144407b6c2ec7ccc76bf67958d93` detected 8 stdlib clock calls.
- Constructor `New` was unique, but `Set`, `Get`, `Delete` each appeared on two receiver types. The grammar correctly returned `UNKNOWN_ADAPTER`; no native behavioral test ran.
- Cause: the signature-only selector ignored whether a receiver was reachable from the constructor-return type.

**Smallest generic repair:** Determine the unique constructor output type and traverse anonymous struct embedding fields (including pointer embeds) to form its receiver reachability closure. Only then match exported method signatures, requiring unambiguous matches. If no constructor or ambiguous methods remain, continue to return UNKNOWN. No target-specific receiver names or method names may appear in proposer code.

**Epistemic boundary:** this is a targeted, post-failure generalization after seeing the selected source, not a preregistered source-blind triumph. Preserve both old failed run and improved follow-up evidence. Strict G3 remains UNKNOWN even on successful replay because `ELAPSE` is a predefined clock template, and the fair manual time-aware baseline B1 should tie.

Smallest decisive regression: two distinct internal receiver types with identically typed exported methods, only one reachable through the exported constructor; verify the unreachable method set is excluded. Also retain the existing genuinely ambiguous reachable-method test.
