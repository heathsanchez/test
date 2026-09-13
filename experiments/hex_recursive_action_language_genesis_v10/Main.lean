def first4 (i : Fin 4) : Bool := i.val == 0
def last4 (i : Fin 4) : Bool := i.val == 3
def target4 (i : Fin 4) : Bool := i.val == 1

theorem witnessed_collision :
    first4 1 = first4 2 ∧
    last4 1 = last4 2 ∧
    target4 1 ≠ target4 2 := by
  decide

theorem complete_old_language_cannot_fit_pair
    (f : Bool → Bool → Bool) :
    ¬ (f (first4 1) (last4 1) = target4 1 ∧
       f (first4 2) (last4 2) = target4 2) := by
  simp [first4, last4, target4]

def generatedLeftEdge {n : Nat} (i : Fin n) : Bool := i.val == 1
def targetSecond {n : Nat} (i : Fin n) : Bool := i.val == 1
def selectedProgram (first last generated : Bool) : Bool := generated

theorem selected_matches_target {n : Nat} (i : Fin n) :
    selectedProgram (i.val == 0) false (generatedLeftEdge i) = targetSecond i := by
  rfl

theorem old_scaffolding_contracts (first last generated : Bool) :
    selectedProgram first last generated = generated := by
  rfl

#check witnessed_collision
#check complete_old_language_cannot_fit_pair
#check selected_matches_target
#check old_scaffolding_contracts
