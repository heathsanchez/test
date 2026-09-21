import Submission

namespace GenericPack

def packW (w p q : Nat) : Nat :=
  p + (q <<< w)

def maskW (w m : Nat) : Nat :=
  packW w m m

def stage (m s p : Nat) : Nat :=
  (p ^^^ (p >>> s)) &&& m

theorem testBit_packW (w p q i : Nat) (hp : p < 2 ^ w) :
    (packW w p q).testBit i =
      if i < w then p.testBit i else q.testBit (i - w) := by
  unfold packW
  simpa [Nat.add_comm, Nat.shiftLeft_eq, Nat.mul_comm] using
    (Nat.testBit_two_pow_mul_add q hp i)

theorem testBit_maskW (w m i : Nat) (hm : m < 2 ^ w) :
    (maskW w m).testBit i =
      if i < w then m.testBit i else m.testBit (i - w) := by
  unfold maskW
  exact testBit_packW w m m i hm

theorem stage_le (m s p : Nat) :
    stage m s p ≤ m := by
  unfold stage
  exact Nat.and_le_right

theorem stage_lt_pow (w m s p : Nat) (hm : m < 2 ^ w) :
    stage m s p < 2 ^ w :=
  Nat.lt_of_le_of_lt (stage_le m s p) hm

theorem bit_false_above_pow {x k i : Nat}
    (hx : x < 2 ^ k) (hi : k ≤ i) :
    x.testBit i = false := by
  have hpow : 2 ^ k ≤ 2 ^ i :=
    Nat.pow_le_pow_right (by omega) hi
  have hxi : x < 2 ^ i := Nat.lt_of_lt_of_le hx hpow
  simp [Nat.testBit, Nat.shiftRight_eq_div_pow, Nat.div_eq_of_lt hxi]

theorem lift_stage
    (w m s p q : Nat)
    (hp : p < 2 ^ w)
    (hm : m < 2 ^ (w - s))
    (hs0 : 0 < s)
    (hsw : s ≤ w) :
    stage (maskW w m) s (packW w p q) =
      packW w (stage m s p) (stage m s q) := by
  have hmw : m < 2 ^ w := by
    have hpow : 2 ^ (w - s) ≤ 2 ^ w :=
      Nat.pow_le_pow_right (by omega) (Nat.sub_le w s)
    exact Nat.lt_of_lt_of_le hm hpow
  apply Nat.eq_of_testBit_eq
  intro i
  rw [testBit_packW w (stage m s p) (stage m s q) i
      (stage_lt_pow w m s p hmw)]
  unfold stage
  rw [Nat.testBit_and, testBit_maskW w m i hmw]
  simp only [Nat.testBit_and, Nat.testBit_xor, Nat.testBit_shiftRight]
  by_cases hi : i < w
  · rw [if_pos hi, if_pos hi]
    by_cases hb : m.testBit i = true
    · have hik : i < w - s := by
        by_cases hsmall : i < w - s
        · exact hsmall
        · have hki : w - s ≤ i := by omega
          have hf := bit_false_above_pow hm hki
          rw [hf] at hb
          simp at hb
      have his : s + i < w := by omega
      rw [testBit_packW w p q i hp, testBit_packW w p q (s + i) hp]
      simp [hi, his, hb]
    · have hbf : m.testBit i = false := by
        cases h : m.testBit i <;> simp_all
      simp [hbf]
  · have hwi : w ≤ i := by omega
    let j := i - w
    have hij : i = w + j := by dsimp [j]; omega
    have hsi : ¬ s + i < w := by omega
    have hsub : (s + i) - w = s + j := by rw [hij]; omega
    rw [if_neg hi, if_neg hi]
    rw [testBit_packW w p q i hp, testBit_packW w p q (s + i) hp]
    simp [hi, hwi, hsi, j, hsub]

def shrMask (m s p : Nat) : Nat :=
  (p >>> s) &&& m

theorem shrMask_le (m s p : Nat) :
    shrMask m s p ≤ m := by
  unfold shrMask
  exact Nat.and_le_right

theorem shrMask_lt_pow (w m s p : Nat) (hm : m < 2 ^ w) :
    shrMask m s p < 2 ^ w :=
  Nat.lt_of_le_of_lt (shrMask_le m s p) hm

theorem lift_shrMask
    (w m s p q : Nat)
    (hp : p < 2 ^ w)
    (hm : m < 2 ^ (w - s))
    (hs0 : 0 < s)
    (hsw : s ≤ w) :
    shrMask (maskW w m) s (packW w p q) =
      packW w (shrMask m s p) (shrMask m s q) := by
  have hmw : m < 2 ^ w := by
    have hpow : 2 ^ (w - s) ≤ 2 ^ w :=
      Nat.pow_le_pow_right (by omega) (Nat.sub_le w s)
    exact Nat.lt_of_lt_of_le hm hpow
  apply Nat.eq_of_testBit_eq
  intro i
  rw [testBit_packW w (shrMask m s p) (shrMask m s q) i
      (shrMask_lt_pow w m s p hmw)]
  unfold shrMask
  rw [Nat.testBit_and, testBit_maskW w m i hmw]
  simp only [Nat.testBit_shiftRight]
  by_cases hi : i < w
  · rw [if_pos hi, if_pos hi]
    by_cases hb : m.testBit i = true
    · have hik : i < w - s := by
        by_cases hsmall : i < w - s
        · exact hsmall
        · have hki : w - s ≤ i := by omega
          have hf := bit_false_above_pow hm hki
          rw [hf] at hb
          simp at hb
      have his : s + i < w := by omega
      rw [testBit_packW w p q (s + i) hp]
      simp [his, hb]
    · have hbf : m.testBit i = false := by
        cases h : m.testBit i <;> simp_all
      simp [hbf]
  · let j := i - w
    have hij : i = w + j := by dsimp [j]; omega
    have hsi : ¬ s + i < w := by omega
    have hsub : (s + i) - w = s + j := by rw [hij]; omega
    rw [if_neg hi, if_neg hi]
    rw [testBit_packW w p q (s + i) hp]
    simp [hsi, j, hsub]

def orStage (m s p : Nat) : Nat :=
  (p ||| (p >>> s)) &&& m

theorem orStage_le (m s p : Nat) :
    orStage m s p ≤ m := by
  unfold orStage
  exact Nat.and_le_right

theorem orStage_lt_pow (w m s p : Nat) (hm : m < 2 ^ w) :
    orStage m s p < 2 ^ w :=
  Nat.lt_of_le_of_lt (orStage_le m s p) hm

theorem lift_or_stage
    (w m s p q : Nat)
    (hp : p < 2 ^ w)
    (hm : m < 2 ^ (w - s))
    (hs0 : 0 < s)
    (hsw : s ≤ w) :
    orStage (maskW w m) s (packW w p q) =
      packW w (orStage m s p) (orStage m s q) := by
  have hmw : m < 2 ^ w := by
    have hpow : 2 ^ (w - s) ≤ 2 ^ w :=
      Nat.pow_le_pow_right (by omega) (Nat.sub_le w s)
    exact Nat.lt_of_lt_of_le hm hpow
  apply Nat.eq_of_testBit_eq
  intro i
  rw [testBit_packW w (orStage m s p) (orStage m s q) i
      (orStage_lt_pow w m s p hmw)]
  unfold orStage
  rw [Nat.testBit_and, testBit_maskW w m i hmw]
  simp only [Nat.testBit_and, Nat.testBit_or, Nat.testBit_shiftRight]
  by_cases hi : i < w
  · rw [if_pos hi, if_pos hi]
    by_cases hb : m.testBit i = true
    · have hik : i < w - s := by
        by_cases hsmall : i < w - s
        · exact hsmall
        · have hki : w - s ≤ i := by omega
          have hf := bit_false_above_pow hm hki
          rw [hf] at hb
          simp at hb
      have his : s + i < w := by omega
      rw [testBit_packW w p q i hp, testBit_packW w p q (s + i) hp]
      simp [hi, his, hb]
    · have hbf : m.testBit i = false := by
        cases h : m.testBit i <;> simp_all
      simp [hbf]
  · have hwi : w ≤ i := by omega
    let j := i - w
    have hij : i = w + j := by dsimp [j]; omega
    have hsi : ¬ s + i < w := by omega
    have hsub : (s + i) - w = s + j := by rw [hij]; omega
    rw [if_neg hi, if_neg hi]
    rw [testBit_packW w p q i hp, testBit_packW w p q (s + i) hp]
    simp [hi, hsi, j, hsub]

theorem packW_lt_double
    (w p q : Nat)
    (hp : p < 2 ^ w)
    (hq : q < 2 ^ w) :
    packW w p q < 2 ^ (w + w) := by
  unfold packW
  rw [Nat.shiftLeft_eq]
  let P := 2 ^ w
  have hP : 0 < P := by
    dsimp [P]
    exact Nat.two_pow_pos w
  have hp' : p ≤ P - 1 := by
    dsimp [P] at hp ⊢
    omega
  have hq' : q ≤ P - 1 := by
    dsimp [P] at hq ⊢
    omega
  have hmul : q * P ≤ (P - 1) * P :=
    Nat.mul_le_mul_right P hq'
  have hPP : P ≤ P * P := by
    have h1 : 1 ≤ P := by omega
    have hm := Nat.mul_le_mul_left P h1
    simpa using hm
  calc
    p + q * P ≤ (P - 1) + (P - 1) * P :=
      Nat.add_le_add hp' hmul
    _ = P * P - 1 := by
      rw [Nat.sub_mul]
      simp
      omega
    _ < P * P := by omega
    _ = 2 ^ (w + w) := by
      dsimp [P]
      rw [Nat.pow_add]

theorem packW_mul (w p q k : Nat) :
    packW w p q * k = packW w (p * k) (q * k) := by
  unfold packW
  rw [Nat.add_mul, Nat.shiftLeft_eq, Nat.shiftLeft_eq]
  congr 1
  calc
    (q * 2 ^ w) * k = q * (2 ^ w * k) := Nat.mul_assoc _ _ _
    _ = q * (k * 2 ^ w) := by rw [Nat.mul_comm (2 ^ w) k]
    _ = (q * k) * 2 ^ w := (Nat.mul_assoc _ _ _).symm

theorem and_maskW
    (w m p q : Nat)
    (hp : p < 2 ^ w)
    (hm : m < 2 ^ w) :
    (packW w p q &&& maskW w m) =
      packW w (p &&& m) (q &&& m) := by
  apply Nat.eq_of_testBit_eq
  intro i
  rw [Nat.testBit_and, testBit_maskW w m i hm]
  have hpm : (p &&& m) < 2 ^ w := by
    exact Nat.lt_of_le_of_lt Nat.and_le_right hm
  rw [testBit_packW w (p &&& m) (q &&& m) i hpm]
  rw [testBit_packW w p q i hp]
  simp only [Nat.testBit_and]
  by_cases hi : i < w <;> simp [hi]

end GenericPack
