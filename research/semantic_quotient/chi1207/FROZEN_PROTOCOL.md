# Source-frozen semantics experiment

Target: go-chi/chi PR 1207.
Base SHA: 167e1e3bd039d060696b99c8da4e876ae04f42c1
Head SHA: 5a84f0500b8f8f307d615969c1ba4f7cd9126978

Date: 2026-10-15 NZ.

Question: does a small observational equivalence relation over route parameter names capture the acceptance behavior, and can a source-native differential test find the smallest post-error router-tree mutation witness?

Protocol:
1. Derive an abstract set-of-declared-names state for name admission only.
2. Exhaustively compare every history of up to four names over three symbols, every continuation of up to three symbols, and every distinct semantic state.
3. Generate independent route strings, compare Go's actual patParamKeys to abstract duplicate detection on frozen original and proposed revisions.
4. Seek the shortest duplicate-key input that changes a fresh router's tree after a recovered panic; compare original and PR head. Test valid-route controls.
5. Remove only the proposed early validation call and rerun the same test.
6. Report full native logs, source pins and all negative controls.

Limitations: The PR body and patch were already inspected, so this cannot be presented as a blind new defect discovery. Do not reuse contributor test code. The result concerns only key admission and fresh-tree mutation, not the complete routing semantics. No upstream writes or outreach.
