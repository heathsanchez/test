import Collatz.AffineFTransportBank

namespace CollatzFinal
namespace SourceProduct

/-- Six actual shortcut steps on the first branch. -/
theorem F_swap_source_trace (q : Nat) :
    iter shortcut 6 (56 + 64 * q) = 26 + 27 * q := by
  have hb : iter shortcut 6 56 = 26 := by decide
  have hc : oddCount 56 6 = 3 := by decide
  simpa [hb, hc] using (parity_cylinder_shift 56 6 q)

/-- Six actual steps on F(n)=3n+2. The branches exchange roles:
    the first endpoint is F(8+9q), the second is 8+9q. -/
theorem F_swap_partner_trace (q : Nat) :
    iter shortcut 6 (3 * (56 + 64 * q) + 2) = 8 + 9 * q := by
  have hb : iter shortcut 6 170 = 8 := by decide
  have hc : oddCount 170 6 = 1 := by decide
  have h := parity_cylinder_shift 170 6 (3 * q)
  rw [hb, hc] at h
  have ha : 170 + 2 ^ 6 * (3 * q) = 3 * (56 + 64 * q) + 2 := by omega
  have he : 8 + 3 ^ 1 * (3 * q) = 8 + 9 * q := by omega
  exact (congrArg (iter shortcut 6) ha).symm.trans (h.trans he)

/-- A certificate is indexed by the unchanged source and actual clock.
    The swap constructor may be nested any finite number of times.
    Soundness does NOT imply that every source has a certificate. -/
inductive FCollisionCert : Nat → Nat → Prop where
  | close (n : Nat) (heven : n % 2 = 0)
      (hnextodd : shortcut n % 2 = 1) : FCollisionCert n 2
  | odd (n t : Nat) (hn : n % 2 = 1)
      (h : FCollisionCert (shortcut n) t) : FCollisionCert n (t + 1)
  | swap (q t : Nat) (h : FCollisionCert (8 + 9 * q) t) :
      FCollisionCert (56 + 64 * q) (6 + t)

/-- Universal structural soundness, not universal grammar coverage. -/
theorem F_collision_certificate_sound {n t : Nat}
    (h : FCollisionCert n t) :
    iter shortcut t n = iter shortcut t (3 * n + 2) := by
  induction h with
  | close n heven hnextodd =>
      exact (three_plus_two_even_odd_collision n heven hnextodd).symm
  | odd n t hn h ih =>
      change iter shortcut t (shortcut n) =
        iter shortcut t (shortcut (3 * n + 2))
      rw [three_plus_two_commutes_odd n hn]
      exact ih
  | swap q t h ih =>
      have he : 26 + 27 * q = 3 * (8 + 9 * q) + 2 := by omega
      calc
        iter shortcut (6 + t) (56 + 64 * q) =
            iter shortcut t (26 + 27 * q) := by
          rw [iter_add, F_swap_source_trace]
        _ = iter shortcut t (3 * (8 + 9 * q) + 2) :=
          congrArg (iter shortcut t) he
        _ = iter shortcut t (8 + 9 * q) := ih.symm
        _ = iter shortcut (6 + t) (3 * (56 + 64 * q) + 2) := by
          rw [iter_add, F_swap_partner_trace]

/-- An accepted grammar certificate composes with ANY actual F-preimage,
    but only a strictly smaller positive ORIGINAL source earns progress. -/
theorem F_certificate_lower_merge (n p t k : Nat)
    (hcert : FCollisionCert n t)
    (hpre : iter shortcut k p = 3 * n + 2)
    (hpos : 0 < p) (hlt : p < n) :
    0 < p ∧ LowerMerge shortcut n p := by
  refine ⟨hpos, hlt, t, k + t, ?_⟩
  calc
    iter shortcut t n = iter shortcut t (3 * n + 2) :=
      F_collision_certificate_sound hcert
    _ = iter shortcut t (iter shortcut k p) :=
      congrArg (iter shortcut t) hpre.symm
    _ = iter shortcut (k + t) p := (iter_add shortcut k t p).symm

/-- Reuse the qualified all-offset source-45 reverse word. -/
theorem source_45_merge_of_F_certificate (q t : Nat)
    (hcert : FCollisionCert (45 + 729 * q) t) :
    0 < 31 + 512 * q ∧
      LowerMerge shortcut (45 + 729 * q) (31 + 512 * q) := by
  exact F_certificate_lower_merge _ _ t 9 hcert
    (source_45_reverse_all_offsets q) (by omega) (by omega)

/-- Two swaps really compose; the old odd-run/even/odd constructor alone
    stops at 3128. This is an admitted certificate, not a coverage claim. -/
theorem F_two_swap_example : FCollisionCert 2085 15 := by
  apply FCollisionCert.odd 2085 14 (by decide)
  change FCollisionCert (56 + 64 * 48) (6 + 8)
  apply FCollisionCert.swap 48 8
  change FCollisionCert (56 + 64 * 6) (6 + 2)
  exact FCollisionCert.swap 6 2
    (FCollisionCert.close 62 (by decide) (by decide))

/-- A source whose first fifteen iterates do not give direct descent or
    a capped ternary hit, but whose new swap certificate has clock 15. -/
theorem F_swap_example_certificate : FCollisionCert 22652991 15 := by
  apply FCollisionCert.odd _ 14 (by decide)
  apply FCollisionCert.odd _ 13 (by decide)
  apply FCollisionCert.odd _ 12 (by decide)
  apply FCollisionCert.odd _ 11 (by decide)
  apply FCollisionCert.odd _ 10 (by decide)
  apply FCollisionCert.odd _ 9 (by decide)
  change FCollisionCert (56 + 64 * 4031745) (6 + 3)
  apply FCollisionCert.swap 4031745 3
  apply FCollisionCert.odd _ 2 (by decide)
  exact FCollisionCert.close _ (by decide) (by decide)

/-- The original-source coalescence conclusion, not just F-quotient identity. -/
theorem F_swap_example_lower_merge :
    0 < 15909919 ∧ LowerMerge shortcut 22652991 15909919 := by
  exact source_45_merge_of_F_certificate 31074 15 F_swap_example_certificate

/-- Terminal phases remain different under identical clocks. -/
theorem terminal_opposite_phases (k : Nat) :
    iter shortcut k 1 ≠ iter shortcut k 2 ∧
      iter shortcut k 2 ≠ iter shortcut k 1 := by
  induction k with
  | zero => decide
  | succ k ih =>
      simpa only [iter, shortcut_one, shortcut_two] using And.symm ih

/-- Important negative control: NOT every terminating source synchronizes
    with F(n) at equal clocks. Both 3 and 11 terminate, in opposite phases.
    Consequently no universal FCollisionCert coverage is claimed. -/
theorem source_three_has_no_synchronous_F_collision (k : Nat) :
    iter shortcut k 3 ≠ iter shortcut k 11 := by
  intro h
  have h3 : iter shortcut 10 3 = 2 := by decide
  have h11 : iter shortcut 10 11 = 1 := by decide
  have hshift := congrArg (iter shortcut 10) h
  have hcomm (n : Nat) :
      iter shortcut 10 (iter shortcut k n) =
        iter shortcut k (iter shortcut 10 n) := by
    calc
      iter shortcut 10 (iter shortcut k n) =
          iter shortcut (k + 10) n := (iter_add shortcut k 10 n).symm
      _ = iter shortcut (10 + k) n := by rw [Nat.add_comm k 10]
      _ = iter shortcut k (iter shortcut 10 n) := iter_add shortcut 10 k n
  rw [hcomm 3, hcomm 11, h3, h11] at hshift
  exact (terminal_opposite_phases k).2 hshift

#print axioms F_swap_source_trace
#print axioms F_swap_partner_trace
#print axioms F_collision_certificate_sound
#print axioms F_certificate_lower_merge
#print axioms source_45_merge_of_F_certificate
#print axioms F_two_swap_example
#print axioms F_swap_example_certificate
#print axioms F_swap_example_lower_merge
#print axioms source_three_has_no_synchronous_F_collision

end SourceProduct
end CollatzFinal
