# V7b source-native scope refinement — observed timeout after positive comparisons

Frozen 17 October 2026 **after observing V7 native apparatus failure, before changing V7 comparator code**. Prior V7 protocol was frozen before V7 results and remains unchanged. This does **not** retrospectively turn the original V7 full-gate run green.

## Evidence that forced this refinement

- V7 first 64-bit default source build: RED #38991553072; glibc reported corrupted heap.
- Diagnostic RED #38991702492: AddressSanitizer traced 8-byte out-of-bounds write to historical lip.c `kar_sq` through `zsqmod`, `zexpmod`, `zsqrtmod` on modern 64-bit long. Original source default `SIZEOFLONG=4`; no scientific claim about original deployed platforms or security.
- Documented PLAIN arithmetic RED #38991787904 still reached `kar_sq`; reconfiguration did not fix the ABI issue.
- True 32-bit ABI build RED #38991858580: original FreeLIP calculated a result and printed `zwriteln` with a backslash + newline as specified by legacy formatting; harness incorrectly required single-line output.
- True 32-bit + corrected newline parser RED #38991929104: `native_compare.py` passed all FIVE original-C published-curve root equalities, candidate-876 original-C root, then stalled >30 s on FIRST intentionally invalid native P-224 quadratic-nonresidue input `(a=11, p=P-224)` with ASan. This was a native resource timeout, not an independently qualified value/rejection witness. No full-gate PASS can be claimed.

## Predeclared minimal V7b follow-up

Keep source versions, arithmetic grammar, published curve targets and candidate-876 completely unchanged. Do not adjust expected roots or post-hoc select candidates. For the *native-source positive correspondence* require exact original 1997 C output equals frozen Python output for all 5 published curves and the 876 root, under 32-bit ABI + ASan. Check deterministic independent negative nonresidues on FOUR p=3(mod 4) curves in original native code, which short-circuits via source-declared `zexpmod` and exact square recheck. Preserve P-224 nonresidue as `UNKNOWN_NATIVE_TIMEOUT_ASAN_30S` from the prior independent run; no repeat 30-second timeout, no false native negative PASS. All five Python nonresidue negatives remain exact.

**Promotable narrow status only:** original FreeLIP 1997 code's POSITIVE curve-root selection reproduces 4/5 published roots and picks the qualifying prime-order 876 root, with source mirror pins and independent Python correspondence; native invalid-input semantics for P-224 remains UNKNOWN. 1997 source availability ≠ actual NSA implementation. No historical selection rule discovered, no basepoint G origin, no cryptographic weakness, no model comparative advantage.

If four p=3mod4 native nonresidue cases fail or any original C output differs, preserve RED/UNKNOWN, don't promote. Archive this amendment and the original source code/run as distinct lineage.