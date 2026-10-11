import Collatz.ParallelMeetingAffineCompiler

namespace CollatzFinal
namespace SourceProduct

set_option maxRecDepth 8192
set_option maxHeartbeats 40000000

/-!
V178 — 205 TYPED, KERNEL CHECKED BASE-SOURCE ELIMINATION RECORDS.

The rule bank below has 205 source-attached actual base meetings
(n,p,i,j), each with concrete kernel-evaluated proof of:
  0<p<n;
  T^i(n)=T^j(p) using true +1 integer arithmetic;
  2^j*3^odds(n,i) <= 2^i*3^odds(p,j).

V177 then proves, WITHOUT checking unbounded offsets one by one:
  n + (2^i*3^odds(p,j))*w
cannot be the LEAST positive nonconvergent Collatz source
for ANY w>=0.

The independent Python audit proves the 205 progressions cover
2,915,346 of 2,985,984 residue positions per common period,
for sufficiently large source integers >=16,384. It is not
a kernel theorem about the entire 3-million-residue mask; that
finite-period population count is separately exact executable evidence.

Coverage means SOURCE POSITION EXCLUSION AS THE LEAST BAD source,
NOT terminal certification of all sources in those progressions.
The remaining 70,638 positions per period are genuine residuals
under this proof grammar. No global Collatz claim. NO QED.
-/

structure V178CertifiedRule where
  source : Nat
  earlier : Nat
  sourceClock : Nat
  earlierClock : Nat
  earlierPositive : 0 < earlier
  earlierSmaller : earlier < source
  actualMeet :
    iter shortcut sourceClock source =
    iter shortcut earlierClock earlier
  slopeOrdered :
    2^earlierClock * 3^(oddCount source sourceClock) <=
      2^sourceClock * 3^(oddCount earlier earlierClock)

def v178CompactBank : List V178CertifiedRule := [
  ⟨2, 1, 1, 0, by decide, by decide, by decide, by decide⟩,
  ⟨2, 1, 0, 1, by decide, by decide, by decide, by decide⟩,
  ⟨5, 4, 2, 0, by decide, by decide, by decide, by decide⟩,
  ⟨4, 3, 0, 3, by decide, by decide, by decide, by decide⟩,
  ⟨3, 2, 4, 0, by decide, by decide, by decide, by decide⟩,
  ⟨11, 10, 5, 0, by decide, by decide, by decide, by decide⟩,
  ⟨23, 20, 5, 0, by decide, by decide, by decide, by decide⟩,
  ⟨10, 7, 0, 6, by decide, by decide, by decide, by decide⟩,
  ⟨7, 5, 7, 0, by decide, by decide, by decide, by decide⟩,
  ⟨15, 10, 7, 0, by decide, by decide, by decide, by decide⟩,
  ⟨59, 38, 7, 0, by decide, by decide, by decide, by decide⟩,
  ⟨15, 13, 6, 1, by decide, by decide, by decide, by decide⟩,
  ⟨79, 67, 6, 1, by decide, by decide, by decide, by decide⟩,
  ⟨39, 38, 8, 0, by decide, by decide, by decide, by decide⟩,
  ⟨95, 91, 8, 0, by decide, by decide, by decide, by decide⟩,
  ⟨123, 118, 8, 0, by decide, by decide, by decide, by decide⟩,
  ⟨175, 167, 8, 0, by decide, by decide, by decide, by decide⟩,
  ⟨199, 190, 8, 0, by decide, by decide, by decide, by decide⟩,
  ⟨219, 209, 8, 0, by decide, by decide, by decide, by decide⟩,
  ⟨287, 205, 10, 0, by decide, by decide, by decide, by decide⟩,
  ⟨347, 248, 10, 0, by decide, by decide, by decide, by decide⟩,
  ⟨367, 262, 10, 0, by decide, by decide, by decide, by decide⟩,
  ⟨423, 302, 10, 0, by decide, by decide, by decide, by decide⟩,
  ⟨507, 362, 10, 0, by decide, by decide, by decide, by decide⟩,
  ⟨575, 410, 10, 0, by decide, by decide, by decide, by decide⟩,
  ⟨583, 416, 10, 0, by decide, by decide, by decide, by decide⟩,
  ⟨735, 524, 10, 0, by decide, by decide, by decide, by decide⟩,
  ⟨815, 581, 10, 0, by decide, by decide, by decide, by decide⟩,
  ⟨923, 658, 10, 0, by decide, by decide, by decide, by decide⟩,
  ⟨999, 712, 10, 0, by decide, by decide, by decide, by decide⟩,
  ⟨367, 349, 9, 1, by decide, by decide, by decide, by decide⟩,
  ⟨411, 391, 9, 1, by decide, by decide, by decide, by decide⟩,
  ⟨487, 463, 9, 1, by decide, by decide, by decide, by decide⟩,
  ⟨799, 759, 9, 1, by decide, by decide, by decide, by decide⟩,
  ⟨879, 835, 9, 1, by decide, by decide, by decide, by decide⟩,
  ⟨999, 949, 9, 1, by decide, by decide, by decide, by decide⟩,
  ⟨1311, 1245, 9, 1, by decide, by decide, by decide, by decide⟩,
  ⟨1435, 1363, 9, 1, by decide, by decide, by decide, by decide⟩,
  ⟨231, 124, 12, 0, by decide, by decide, by decide, by decide⟩,
  ⟨383, 205, 12, 0, by decide, by decide, by decide, by decide⟩,
  ⟨615, 329, 12, 0, by decide, by decide, by decide, by decide⟩,
  ⟨935, 500, 12, 0, by decide, by decide, by decide, by decide⟩,
  ⟨1019, 545, 12, 0, by decide, by decide, by decide, by decide⟩,
  ⟨1087, 581, 12, 0, by decide, by decide, by decide, by decide⟩,
  ⟨1647, 880, 12, 0, by decide, by decide, by decide, by decide⟩,
  ⟨1703, 910, 12, 0, by decide, by decide, by decide, by decide⟩,
  ⟨1787, 955, 12, 0, by decide, by decide, by decide, by decide⟩,
  ⟨1855, 991, 12, 0, by decide, by decide, by decide, by decide⟩,
  ⟨2031, 1085, 12, 0, by decide, by decide, by decide, by decide⟩,
  ⟨2203, 1177, 12, 0, by decide, by decide, by decide, by decide⟩,
  ⟨2239, 1196, 12, 0, by decide, by decide, by decide, by decide⟩,
  ⟨2351, 1256, 12, 0, by decide, by decide, by decide, by decide⟩,
  ⟨2587, 1382, 12, 0, by decide, by decide, by decide, by decide⟩,
  ⟨2591, 1384, 12, 0, by decide, by decide, by decide, by decide⟩,
  ⟨2907, 1553, 12, 0, by decide, by decide, by decide, by decide⟩,
  ⟨2975, 1589, 12, 0, by decide, by decide, by decide, by decide⟩,
  ⟨3119, 1666, 12, 0, by decide, by decide, by decide, by decide⟩,
  ⟨3143, 1679, 12, 0, by decide, by decide, by decide, by decide⟩,
  ⟨3295, 1760, 12, 0, by decide, by decide, by decide, by decide⟩,
  ⟨3675, 1963, 12, 0, by decide, by decide, by decide, by decide⟩,
  ⟨3911, 2089, 12, 0, by decide, by decide, by decide, by decide⟩,
  ⟨4063, 2170, 12, 0, by decide, by decide, by decide, by decide⟩,
  ⟨231, 165, 11, 1, by decide, by decide, by decide, by decide⟩,
  ⟨543, 387, 11, 1, by decide, by decide, by decide, by decide⟩,
  ⟨1071, 763, 11, 1, by decide, by decide, by decide, by decide⟩,
  ⟨1627, 1159, 11, 1, by decide, by decide, by decide, by decide⟩,
  ⟨1647, 1173, 11, 1, by decide, by decide, by decide, by decide⟩,
  ⟨1855, 1321, 11, 1, by decide, by decide, by decide, by decide⟩,
  ⟨1863, 1327, 11, 1, by decide, by decide, by decide, by decide⟩,
  ⟨2203, 1569, 11, 1, by decide, by decide, by decide, by decide⟩,
  ⟨2431, 1731, 11, 1, by decide, by decide, by decide, by decide⟩,
  ⟨3675, 2617, 11, 1, by decide, by decide, by decide, by decide⟩,
  ⟨3751, 2671, 11, 1, by decide, by decide, by decide, by decide⟩,
  ⟨3835, 2731, 11, 1, by decide, by decide, by decide, by decide⟩,
  ⟨3903, 2779, 11, 1, by decide, by decide, by decide, by decide⟩,
  ⟨4063, 2893, 11, 1, by decide, by decide, by decide, by decide⟩,
  ⟨4251, 3027, 11, 1, by decide, by decide, by decide, by decide⟩,
  ⟨4327, 3081, 11, 1, by decide, by decide, by decide, by decide⟩,
  ⟨4479, 3189, 11, 1, by decide, by decide, by decide, by decide⟩,
  ⟨4639, 3303, 11, 1, by decide, by decide, by decide, by decide⟩,
  ⟨5167, 3679, 11, 1, by decide, by decide, by decide, by decide⟩,
  ⟨5743, 4089, 11, 1, by decide, by decide, by decide, by decide⟩,
  ⟨5799, 4129, 11, 1, by decide, by decide, by decide, by decide⟩,
  ⟨5883, 4189, 11, 1, by decide, by decide, by decide, by decide⟩,
  ⟨5959, 4243, 11, 1, by decide, by decide, by decide, by decide⟩,
  ⟨6111, 4351, 11, 1, by decide, by decide, by decide, by decide⟩,
  ⟨223, 167, 7, 5, by decide, by decide, by decide, by decide⟩,
  ⟨351, 263, 7, 5, by decide, by decide, by decide, by decide⟩,
  ⟨735, 551, 7, 5, by decide, by decide, by decide, by decide⟩,
  ⟨991, 743, 7, 5, by decide, by decide, by decide, by decide⟩,
  ⟨1119, 839, 7, 5, by decide, by decide, by decide, by decide⟩,
  ⟨1375, 1031, 7, 5, by decide, by decide, by decide, by decide⟩,
  ⟨1503, 1127, 7, 5, by decide, by decide, by decide, by decide⟩,
  ⟨1887, 1415, 7, 5, by decide, by decide, by decide, by decide⟩,
  ⟨2143, 1607, 7, 5, by decide, by decide, by decide, by decide⟩,
  ⟨2271, 1703, 7, 5, by decide, by decide, by decide, by decide⟩,
  ⟨2527, 1895, 7, 5, by decide, by decide, by decide, by decide⟩,
  ⟨2655, 1991, 7, 5, by decide, by decide, by decide, by decide⟩,
  ⟨3039, 2279, 7, 5, by decide, by decide, by decide, by decide⟩,
  ⟨3295, 2471, 7, 5, by decide, by decide, by decide, by decide⟩,
  ⟨3423, 2567, 7, 5, by decide, by decide, by decide, by decide⟩,
  ⟨3679, 2759, 7, 5, by decide, by decide, by decide, by decide⟩,
  ⟨3807, 2855, 7, 5, by decide, by decide, by decide, by decide⟩,
  ⟨4191, 3143, 7, 5, by decide, by decide, by decide, by decide⟩,
  ⟨4447, 3335, 7, 5, by decide, by decide, by decide, by decide⟩,
  ⟨4575, 3431, 7, 5, by decide, by decide, by decide, by decide⟩,
  ⟨4831, 3623, 7, 5, by decide, by decide, by decide, by decide⟩,
  ⟨4959, 3719, 7, 5, by decide, by decide, by decide, by decide⟩,
  ⟨5343, 4007, 7, 5, by decide, by decide, by decide, by decide⟩,
  ⟨5727, 4295, 7, 5, by decide, by decide, by decide, by decide⟩,
  ⟨5983, 4487, 7, 5, by decide, by decide, by decide, by decide⟩,
  ⟨6111, 4583, 7, 5, by decide, by decide, by decide, by decide⟩,
  ⟨6495, 4871, 7, 5, by decide, by decide, by decide, by decide⟩,
  ⟨6751, 5063, 7, 5, by decide, by decide, by decide, by decide⟩,
  ⟨6879, 5159, 7, 5, by decide, by decide, by decide, by decide⟩,
  ⟨7135, 5351, 7, 5, by decide, by decide, by decide, by decide⟩,
  ⟨7263, 5447, 7, 5, by decide, by decide, by decide, by decide⟩,
  ⟨7647, 5735, 7, 5, by decide, by decide, by decide, by decide⟩,
  ⟨7903, 5927, 7, 5, by decide, by decide, by decide, by decide⟩,
  ⟨8031, 6023, 7, 5, by decide, by decide, by decide, by decide⟩,
  ⟨8287, 6215, 7, 5, by decide, by decide, by decide, by decide⟩,
  ⟨8415, 6311, 7, 5, by decide, by decide, by decide, by decide⟩,
  ⟨8799, 6599, 7, 5, by decide, by decide, by decide, by decide⟩,
  ⟨9055, 6791, 7, 5, by decide, by decide, by decide, by decide⟩,
  ⟨9183, 6887, 7, 5, by decide, by decide, by decide, by decide⟩,
  ⟨9439, 7079, 7, 5, by decide, by decide, by decide, by decide⟩,
  ⟨9567, 7175, 7, 5, by decide, by decide, by decide, by decide⟩,
  ⟨9951, 7463, 7, 5, by decide, by decide, by decide, by decide⟩,
  ⟨10207, 7655, 7, 5, by decide, by decide, by decide, by decide⟩,
  ⟨10335, 7751, 7, 5, by decide, by decide, by decide, by decide⟩,
  ⟨63, 47, 8, 6, by decide, by decide, by decide, by decide⟩,
  ⟨831, 623, 8, 6, by decide, by decide, by decide, by decide⟩,
  ⟨1087, 815, 8, 6, by decide, by decide, by decide, by decide⟩,
  ⟨1599, 1199, 8, 6, by decide, by decide, by decide, by decide⟩,
  ⟨1855, 1391, 8, 6, by decide, by decide, by decide, by decide⟩,
  ⟨2367, 1775, 8, 6, by decide, by decide, by decide, by decide⟩,
  ⟨3135, 2351, 8, 6, by decide, by decide, by decide, by decide⟩,
  ⟨3391, 2543, 8, 6, by decide, by decide, by decide, by decide⟩,
  ⟨3903, 2927, 8, 6, by decide, by decide, by decide, by decide⟩,
  ⟨4159, 3119, 8, 6, by decide, by decide, by decide, by decide⟩,
  ⟨4671, 3503, 8, 6, by decide, by decide, by decide, by decide⟩,
  ⟨5439, 4079, 8, 6, by decide, by decide, by decide, by decide⟩,
  ⟨5695, 4271, 8, 6, by decide, by decide, by decide, by decide⟩,
  ⟨6207, 4655, 8, 6, by decide, by decide, by decide, by decide⟩,
  ⟨6463, 4847, 8, 6, by decide, by decide, by decide, by decide⟩,
  ⟨6975, 5231, 8, 6, by decide, by decide, by decide, by decide⟩,
  ⟨7743, 5807, 8, 6, by decide, by decide, by decide, by decide⟩,
  ⟨7999, 5999, 8, 6, by decide, by decide, by decide, by decide⟩,
  ⟨8511, 6383, 8, 6, by decide, by decide, by decide, by decide⟩,
  ⟨8767, 6575, 8, 6, by decide, by decide, by decide, by decide⟩,
  ⟨9279, 6959, 8, 6, by decide, by decide, by decide, by decide⟩,
  ⟨10047, 7535, 8, 6, by decide, by decide, by decide, by decide⟩,
  ⟨10303, 7727, 8, 6, by decide, by decide, by decide, by decide⟩,
  ⟨10815, 8111, 8, 6, by decide, by decide, by decide, by decide⟩,
  ⟨11071, 8303, 8, 6, by decide, by decide, by decide, by decide⟩,
  ⟨11583, 8687, 8, 6, by decide, by decide, by decide, by decide⟩,
  ⟨12351, 9263, 8, 6, by decide, by decide, by decide, by decide⟩,
  ⟨12607, 9455, 8, 6, by decide, by decide, by decide, by decide⟩,
  ⟨13119, 9839, 8, 6, by decide, by decide, by decide, by decide⟩,
  ⟨13887, 10415, 8, 6, by decide, by decide, by decide, by decide⟩,
  ⟨14655, 10991, 8, 6, by decide, by decide, by decide, by decide⟩,
  ⟨14911, 11183, 8, 6, by decide, by decide, by decide, by decide⟩,
  ⟨15423, 11567, 8, 6, by decide, by decide, by decide, by decide⟩,
  ⟨15679, 11759, 8, 6, by decide, by decide, by decide, by decide⟩,
  ⟨16191, 12143, 8, 6, by decide, by decide, by decide, by decide⟩,
  ⟨615, 519, 10, 5, by decide, by decide, by decide, by decide⟩,
  ⟨1563, 1319, 10, 5, by decide, by decide, by decide, by decide⟩,
  ⟨1639, 1383, 10, 5, by decide, by decide, by decide, by decide⟩,
  ⟨3687, 3111, 10, 5, by decide, by decide, by decide, by decide⟩,
  ⟨4635, 3911, 10, 5, by decide, by decide, by decide, by decide⟩,
  ⟨5659, 4775, 10, 5, by decide, by decide, by decide, by decide⟩,
  ⟨6759, 5703, 10, 5, by decide, by decide, by decide, by decide⟩,
  ⟨7707, 6503, 10, 5, by decide, by decide, by decide, by decide⟩,
  ⟨7783, 6567, 10, 5, by decide, by decide, by decide, by decide⟩,
  ⟨8731, 7367, 10, 5, by decide, by decide, by decide, by decide⟩,
  ⟨9831, 8295, 10, 5, by decide, by decide, by decide, by decide⟩,
  ⟨10779, 9095, 10, 5, by decide, by decide, by decide, by decide⟩,
  ⟨10855, 9159, 10, 5, by decide, by decide, by decide, by decide⟩,
  ⟨12903, 10887, 10, 5, by decide, by decide, by decide, by decide⟩,
  ⟨13851, 11687, 10, 5, by decide, by decide, by decide, by decide⟩,
  ⟨14875, 12551, 10, 5, by decide, by decide, by decide, by decide⟩,
  ⟨15975, 13479, 10, 5, by decide, by decide, by decide, by decide⟩,
  ⟨1191, 1131, 12, 4, by decide, by decide, by decide, by decide⟩,
  ⟨1275, 1211, 12, 4, by decide, by decide, by decide, by decide⟩,
  ⟨2607, 2475, 12, 4, by decide, by decide, by decide, by decide⟩,
  ⟨3399, 3227, 12, 4, by decide, by decide, by decide, by decide⟩,
  ⟨5371, 5099, 12, 4, by decide, by decide, by decide, by decide⟩,
  ⟨5439, 5163, 12, 4, by decide, by decide, by decide, by decide⟩,
  ⟨6703, 6363, 12, 4, by decide, by decide, by decide, by decide⟩,
  ⟨7495, 7115, 12, 4, by decide, by decide, by decide, by decide⟩,
  ⟨11355, 10779, 12, 4, by decide, by decide, by decide, by decide⟩,
  ⟨13479, 12795, 12, 4, by decide, by decide, by decide, by decide⟩,
  ⟨13563, 12875, 12, 4, by decide, by decide, by decide, by decide⟩,
  ⟨14895, 14139, 12, 4, by decide, by decide, by decide, by decide⟩,
  ⟨15451, 14667, 12, 4, by decide, by decide, by decide, by decide⟩,
  ⟨15687, 14891, 12, 4, by decide, by decide, by decide, by decide⟩,
  ⟨2331, 1967, 11, 6, by decide, by decide, by decide, by decide⟩,
  ⟨4455, 3759, 11, 6, by decide, by decide, by decide, by decide⟩,
  ⟨6427, 5423, 11, 6, by decide, by decide, by decide, by decide⟩,
  ⟨8475, 7151, 11, 6, by decide, by decide, by decide, by decide⟩,
  ⟨8551, 7215, 11, 6, by decide, by decide, by decide, by decide⟩,
  ⟨10599, 8943, 11, 6, by decide, by decide, by decide, by decide⟩,
  ⟨12571, 10607, 11, 6, by decide, by decide, by decide, by decide⟩,
  ⟨14619, 12335, 11, 6, by decide, by decide, by decide, by decide⟩,
  ⟨14695, 12399, 11, 6, by decide, by decide, by decide, by decide⟩
]

/-- Any item admitted by the kernel-checked finite bank generates
    a genuine infinite family of strict earlier-source meetings. -/
theorem v178_rule_all_offsets_have_real_lower_merge
    (r : V178CertifiedRule) (w : Nat) :
    LowerMerge shortcut
      (r.source + 2^r.sourceClock *
        (3^(oddCount r.earlier r.earlierClock)*w))
      (r.earlier + 2^r.earlierClock *
        (3^(oddCount r.source r.sourceClock)*w)) :=
  v177_unshifted_ordered_affine_lower_merge
    r.source r.earlier r.sourceClock r.earlierClock w
    r.actualMeet r.earlierSmaller r.slopeOrdered

/-- The entire infinite progression of a selected certified
    rule is disallowed as the LEAST bad original source.
    Does not claim that its members converge independently. -/
theorem v178_rule_excludes_least_bad
    (r : V178CertifiedRule) (w : Nat) :
    ¬ MinimalBad PositiveBad
      (r.source + 2^r.sourceClock *
        (3^(oddCount r.earlier r.earlierClock)*w)) := by
  intro hmin
  have hm := v178_rule_all_offsets_have_real_lower_merge r w
  obtain ⟨hlt,i,j,hEq⟩ := hm
  have hp : 0 < r.earlier +
      2^r.earlierClock *
        (3^(oddCount r.source r.sourceClock)*w) := by
    have hh := r.earlierPositive
    omega
  exact (minimal_positive_bad_no_earlier_source_meeting
    hmin
    (r.earlier + 2^r.earlierClock *
        (3^(oddCount r.source r.sourceClock)*w))
    i j hp hlt) hEq

/-- No matter which of the 205 strictly source-attached
    rules is selected, the universal least-bad exclusion is sound. -/
theorem v178_compact_bank_sound
    (r : V178CertifiedRule)
    (hr : r ∈ v178CompactBank)
    (w : Nat) :
    ¬ MinimalBad PositiveBad
      (r.source + 2^r.sourceClock *
        (3^(oddCount r.earlier r.earlierClock)*w)) :=
  v178_rule_excludes_least_bad r w

/-- One especially strong root rule: ALL positive n congruent
    2 mod3 have a strictly smaller odd immediate predecessor.
    It is directly a certified V177 affine meeting:
      T(1+2w) = 2+3w, for EVERY w. -/
theorem v178_no_least_bad_source_two_mod_three
    (n : Nat) (hmod : n%3=2) :
    ¬ MinimalBad PositiveBad n := by
  have hdiv := Nat.mod_add_div n 3
  let w := n/3
  have hn : n = 2+3*w := by
    dsimp [w]
    omega
  have hMeet : iter shortcut 0 2 = iter shortcut 1 1 := by decide
  have hCount1 : oddCount 1 1=1 := by decide
  have hCount2 : oddCount 2 0=0 := by decide
  have hSlope : 2^1*3^(oddCount 2 0) <=
    2^0*3^(oddCount 1 1) := by
    simp [hCount1,hCount2]
  have hrule :=
    v177_unshifted_ordered_affine_lower_merge
      2 1 0 1 w hMeet (by decide) hSlope
  have hm : LowerMerge shortcut (2+3*w) (1+2*w) := by
    simpa [hCount1,hCount2] using hrule
  intro hmin
  rw [hn] at hmin
  obtain ⟨hlt,i,j,hEq⟩ := hm
  have hpos : 0<1+2*w := by omega
  exact (minimal_positive_bad_no_earlier_source_meeting
    hmin (1+2*w) i j hpos hlt) hEq

#print axioms v178_rule_all_offsets_have_real_lower_merge
#print axioms v178_rule_excludes_least_bad
#print axioms v178_compact_bank_sound
#print axioms v178_no_least_bad_source_two_mod_three

end SourceProduct
end CollatzFinal
