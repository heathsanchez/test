# Andrews-Curtis Development V1

Pinned external authority: `SAIRcompetition/Andrews-Curtis@99a65377c5c4f412cd9af7b8d31c41464a855736`.

This experiment tests whether reusable continuation structure learned from published,
unscored certificates can improve later search while preserving exact replay authority.

Protocol:

1. Reproduce the official sample verifier.
2. Split the 424 published AC training certificates deterministically by row parity.
3. Mine a small macro vocabulary from development rows only, then freeze it.
4. Keep the other half out of macro construction and use a fixed subset as a prospective
   atomic-vs-macro diagnostic.
5. Build a bounded exact reverse neighbourhood of the ordered target `(x,y)`.
6. Search scored AC presentations in exposed initial-length order, without using hidden
   source labels or difficulty labels and without changing the macro vocabulary.
7. Admit only paths that pass the pinned official verifier.
8. Independently verify Stable-AC certificates obtained by appending the official
   `[16,15]` finish to each verified AC path.
9. Emit <=500-line submission shards, official replay receipts, and a hashed JSON report.

This V1 is a bounded qualification, not a claim of unrestricted developmental search.
