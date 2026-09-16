import Submission

namespace PackMix8FactProbe
open Submission

theorem packMix8_fact (x : Nat) :
    packMixBit x 8 = pack8 x := by
  have h := packMixBit_eight x 0
  simpa only [Nat.mul_zero, Nat.add_zero] using h

end PackMix8FactProbe
