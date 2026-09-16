import WideDenseByteProof
import Submission

namespace WideDensePack8Probe

open WideDenseByte
open Submission

set_option maxRecDepth 1048576
set_option maxHeartbeats 1000000

theorem pack8Nat_eq_packMixBit8_probe (x : Nat) :
    pack8Nat x = packMixBit x 8 := by
  rw [pack8Nat_eq]
  symm
  have h := packMixBit_eight x 0
  have hz : packMixBit (advance8 x) 0 = 0 := rfl
  rw [hz] at h
  simpa only [Nat.zero_add, Nat.mul_zero, Nat.add_zero] using h

theorem dense8_eq_packMixBit8_probe (x : Nat) :
    WideGather.dense8 x = packMixBit x 8 := by
  exact (dense8_eq_pack8Nat x).trans (pack8Nat_eq_packMixBit8_probe x)

end WideDensePack8Probe
