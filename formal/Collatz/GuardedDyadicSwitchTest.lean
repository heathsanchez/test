import Collatz.GuardedDyadicSwitch
namespace CollatzFinal.SourceProduct
example : DyadicOrder (40 + 96) 3 :=
  dyadic_sum_unequal (v := 3) (w := 5)
    ⟨5, by decide, by decide⟩ ⟨3, by decide, by decide⟩ (by decide)
example : ∃ z : Int, 40 + 24 = (2 : Int)^4 * z :=
  dyadic_equal_sum_even (v := 3)
    ⟨5, by decide, by decide⟩ ⟨3, by decide, by decide⟩
example : ¬ DyadicOrder 0 7 := by
  intro h
  exact dyadic_order_nonzero h rfl
example : DyadicOrder (-40) 3 := ⟨-5, by decide, by decide⟩
#check fixed_centre_exhaustion
#check shared_centre_return_exhaustion
#check return_switch_unequal
#check equal_order_cancellation_unbounded
end CollatzFinal.SourceProduct
