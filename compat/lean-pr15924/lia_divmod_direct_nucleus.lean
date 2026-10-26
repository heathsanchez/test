/-!
Nucleus upstream compatibility probe (source only; not proof of Nucleus compatibility).
Upstream Lean PR #15924 / 9e118e97309ae41cba636cd0b5027dbfcc58f115
Upstream fixture tests/elab/lia_divmod_direct.lean, blob 3899238e7850a80776e680501fbb769a743124df.
Pin Lean and matching lean4export before exporting.
-/
import Lean

theorem nucleus_lia_divmod (x : Int) :
    x = 7 * (x / 7) + x % 7 := by
  lia

theorem nucleus_lia_mod_bound (x : Int) :
    x % 3 < 3 := by
  lia

theorem nucleus_lia_mod_nonnegative (x : Int) :
    0 ≤ x % 5 := by
  lia

theorem nucleus_lia_negative_divisor (x : Int) :
    x % (-3) < 3 := by
  lia

theorem nucleus_lia_inconsistent_remainder (x : Int)
    (h : x % 4 = 5) : False := by
  lia

/- For adversarial export testing:
  (1) Export each authentic theorem with exact source/exporter revisions.
  (2) Mutate only a theorem's exported proposition, preserving its proof.
      E.g. replace the conclusion of nucleus_lia_divmod with
      x = 7 * (x / 7) + x % 7 + 1.
  (3) Authentic exports must ACCEPT; mutated exports must NEVER ACCEPT.
  (4) Record Nucleus diagnostic on UNKNOWN, and compare against
      official leanchecker --from-export at the identical export pin.
  (5) Preserve SHA-pinned frozen196 baseline and negative fixtures.
This file alone does not exercise the checker or establish a verdict.
-/
