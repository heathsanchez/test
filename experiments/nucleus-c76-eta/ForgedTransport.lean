import Init

-- A directly falsified transport conclusion; cannot be proved by rfl.
example (h : True ↔ True) :
    @decide True (@decidable_of_decidable_of_iff True True
      (Decidable.isTrue True.intro) h) = false := by
  rfl
